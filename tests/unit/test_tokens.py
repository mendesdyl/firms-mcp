"""Token encryption keys and the JWE codec (FR-AUTH-008; ADR-0004 §3)."""

from __future__ import annotations

import logging

import pytest

from firms_mcp.auth.tokens import (
    InvalidToken,
    TokenCodec,
    TokenKeyError,
    generate_key_spec,
    parse_token_keys,
)

CLAIMS = {"iss": "https://testserver/", "aud": "https://testserver/mcp", "mk": "x" * 32}


@pytest.mark.req("FR-AUTH-008")
def test_keys_rotate_first_encrypts_all_decrypt() -> None:
    old, new = generate_key_spec("old"), generate_key_spec("new")
    before = TokenCodec.from_spec(old)
    sealed_with_old = before.seal(CLAIMS, typ="at+jwe")
    during = TokenCodec.from_spec(f"{new},{old}")
    assert during.open(sealed_with_old, typ="at+jwe") == CLAIMS  # old tokens still valid
    sealed_with_new = during.seal(CLAIMS, typ="at+jwe")
    assert '"kid":"new"' in _header(sealed_with_new)
    after = TokenCodec.from_spec(new)
    with pytest.raises(InvalidToken):
        after.open(sealed_with_old, typ="at+jwe")  # old key removed


@pytest.mark.req("FR-AUTH-008")
def test_tokens_are_bound_to_their_type_and_tamper_evident() -> None:
    codec = TokenCodec.from_spec(generate_key_spec())
    token = codec.seal(CLAIMS, typ="at+jwe")
    assert "x" * 32 not in token  # the MAP_KEY is encrypted, not merely encoded
    with pytest.raises(InvalidToken):
        codec.open(token, typ="rt+jwe")
    head, key, iv, ciphertext, tag = token.split(".")
    flipped = ciphertext[:-2] + ("A" if ciphertext[-2] != "A" else "B") + ciphertext[-1]
    with pytest.raises(InvalidToken):
        codec.open(".".join((head, key, iv, flipped, tag)), typ="at+jwe")
    with pytest.raises(InvalidToken):
        codec.open("not.a.token", typ="at+jwe")


@pytest.mark.parametrize(
    ("spec", "message"),
    [
        ("k1:" + "A" * 22, "32 bytes"),  # 16 bytes
        ("k1:!!!!", "base64url"),
        (" , ", "no keys"),
    ],
)
def test_malformed_key_specs_are_rejected(spec: str, message: str) -> None:
    with pytest.raises(TokenKeyError, match=message):
        parse_token_keys(spec)


def test_duplicate_key_ids_and_derived_ids() -> None:
    spec = generate_key_spec("same")
    with pytest.raises(TokenKeyError, match="duplicate"):
        parse_token_keys(f"{spec},{spec}")
    bare = spec.split(":", 1)[1]
    (key,) = parse_token_keys(bare)
    assert len(key.kid) == 8  # derived from the key itself


def test_missing_keys_fall_back_to_an_ephemeral_key_with_a_warning(caplog) -> None:
    with caplog.at_level(logging.WARNING):
        codec = TokenCodec.from_spec(None)
    assert codec.keys[0].kid == "ephemeral"
    assert "FIRMS_MCP_TOKEN_KEYS is not set" in caplog.text


def test_subjects_are_stable_pseudonyms() -> None:
    codec = TokenCodec.from_spec(generate_key_spec())
    assert codec.subject("a" * 32) == codec.subject("a" * 32) != codec.subject("b" * 32)
    assert "a" * 32 not in codec.subject("a" * 32)


def _header(token: str) -> str:
    import base64

    return base64.urlsafe_b64decode(token.split(".")[0] + "==").decode()


def test_keygen_command_prints_a_usable_key(capsys) -> None:
    from firms_mcp.server import main

    main(["keygen"])
    spec = capsys.readouterr().out.strip()
    (key,) = parse_token_keys(spec)
    assert len(key.secret) == 32
