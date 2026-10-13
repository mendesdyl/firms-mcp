"""Encrypted tokens for the MAP_KEY connect flow (ADR-0004 §3; FR-AUTH-008).

Tokens are JWE compact serializations with ``alg: dir`` and ``enc: A256GCM``, encrypted
with a server key. The payload carries the issuer, audience, client, scopes, times, a
token ID, a pseudonymous subject, and the user's MAP_KEY, so verifying a token needs only
the key: the MCP request path stays stateless.

``FIRMS_MCP_TOKEN_KEYS`` holds one or more 32-byte keys, comma-separated, each written as
``<kid>:<base64url key>`` (or just ``<base64url key>``, whose ``kid`` is then derived from
the key). The first key encrypts; every key decrypts, so keys can be rotated by putting a
new key first and removing the old one after the longest token lifetime.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import logging
import secrets
from dataclasses import dataclass
from typing import Any

from joserfc import jwe
from joserfc.errors import JoseError
from joserfc.jwk import OctKey

logger = logging.getLogger(__name__)

ALGORITHMS = ("dir", "A256GCM")
KEY_BYTES = 32


class TokenKeyError(ValueError):
    """FIRMS_MCP_TOKEN_KEYS is malformed; the message says how."""


class InvalidToken(ValueError):
    """A token could not be decrypted or is not one this server issued."""


def _b64url_decode(text: str) -> bytes:
    """Strict base64url decoding: characters outside the alphabet are an error."""
    padded = text + "=" * (-len(text) % 4)
    return base64.b64decode(padded.encode("ascii"), altchars=b"-_", validate=True)


def generate_key_spec(kid: str | None = None) -> str:
    """A new ``kid:key`` entry for FIRMS_MCP_TOKEN_KEYS."""
    key = base64.urlsafe_b64encode(secrets.token_bytes(KEY_BYTES)).decode("ascii").rstrip("=")
    return f"{kid or secrets.token_hex(4)}:{key}"


@dataclass(frozen=True)
class TokenKey:
    kid: str
    secret: bytes

    def oct_key(self) -> OctKey:
        return OctKey.import_key(self.secret)


def parse_token_keys(spec: str) -> list[TokenKey]:
    keys: list[TokenKey] = []
    for raw in (part.strip() for part in spec.split(",")):
        if not raw:
            continue
        kid, sep, encoded = raw.partition(":")
        if not sep:
            kid, encoded = "", raw
        try:
            secret = _b64url_decode(encoded)
        except (binascii.Error, ValueError, UnicodeEncodeError) as exc:
            raise TokenKeyError("FIRMS_MCP_TOKEN_KEYS: a key is not valid base64url") from exc
        if len(secret) != KEY_BYTES:
            raise TokenKeyError(
                f"FIRMS_MCP_TOKEN_KEYS: each key must be {KEY_BYTES} bytes (got {len(secret)})"
            )
        kid = kid or hashlib.sha256(secret).hexdigest()[:8]
        if any(k.kid == kid for k in keys):
            raise TokenKeyError(f"FIRMS_MCP_TOKEN_KEYS: duplicate key id {kid!r}")
        keys.append(TokenKey(kid=kid, secret=secret))
    if not keys:
        raise TokenKeyError("FIRMS_MCP_TOKEN_KEYS contains no keys")
    return keys


class TokenCodec:
    """Seal and open claim sets as JWE with the configured keys."""

    def __init__(self, keys: list[TokenKey]) -> None:
        if not keys:
            raise TokenKeyError("at least one token key is required")
        self.keys = keys
        self._by_kid = {key.kid: key for key in keys}
        # Derived secrets for other uses, so the encryption key is never reused directly.
        self._subject_secret = hmac.new(keys[0].secret, b"firms-mcp:subject", "sha256").digest()
        self.binding_secret = hmac.new(keys[0].secret, b"firms-mcp:connect", "sha256").digest()

    @classmethod
    def from_spec(cls, spec: str | None) -> TokenCodec:
        """Codec for FIRMS_MCP_TOKEN_KEYS; an ephemeral key when none is configured."""
        if spec:
            return cls(parse_token_keys(spec))
        logger.warning(
            "FIRMS_MCP_TOKEN_KEYS is not set: using a temporary key. Connected users must "
            "reconnect after a restart, and replicas cannot share tokens."
        )
        return cls([TokenKey(kid="ephemeral", secret=secrets.token_bytes(KEY_BYTES))])

    def seal(self, claims: dict[str, Any], *, typ: str) -> str:
        key = self.keys[0]
        header = {"alg": "dir", "enc": "A256GCM", "kid": key.kid, "typ": typ}
        payload = json.dumps(claims, separators=(",", ":")).encode("utf-8")
        return jwe.encrypt_compact(header, payload, key.oct_key(), algorithms=ALGORITHMS)

    def open(self, token: str, *, typ: str) -> dict[str, Any]:
        try:
            header = json.loads(_b64url_decode(token.split(".", 1)[0]))
        except (ValueError, UnicodeDecodeError, binascii.Error) as exc:
            raise InvalidToken("not a token issued by this server") from exc
        if not isinstance(header, dict) or header.get("typ") != typ:
            raise InvalidToken("wrong token type")
        if header.get("alg") != "dir" or header.get("enc") != "A256GCM":
            raise InvalidToken("unsupported token algorithm")
        key = self._by_kid.get(str(header.get("kid")))
        if key is None:
            raise InvalidToken("unknown token key")
        try:
            decrypted = jwe.decrypt_compact(token, key.oct_key(), algorithms=ALGORITHMS)
            claims = json.loads(decrypted.plaintext)
        except (JoseError, ValueError, TypeError) as exc:
            raise InvalidToken("token could not be decrypted") from exc
        if not isinstance(claims, dict):
            raise InvalidToken("token payload is not an object")
        return claims

    def subject(self, map_key: str) -> str:
        """A stable pseudonym for a MAP_KEY that does not reveal it (keyed hash)."""
        return hmac.new(self._subject_secret, map_key.encode("utf-8"), "sha256").hexdigest()[:32]
