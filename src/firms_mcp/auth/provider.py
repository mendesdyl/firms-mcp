"""OAuth 2.1 authorization server whose consent step collects the user's FIRMS MAP_KEY.

ADR-0004 §2 and §3. The server is its own authorization server, co-hosted with the MCP
endpoint. The "login" is one page on which the user enters their own FIRMS MAP_KEY; the
key is checked with FIRMS and then travels only inside encrypted tokens.

Flow: ``/authorize`` (SDK handler: client, redirect URI, scope, PKCE) → a pending
authorization and a redirect to ``/connect`` with a browser-binding cookie → the user
submits the key → FIRMS's MAP_KEY status service accepts it → a single-use code and a
redirect to the client with ``code``, ``state``, and ``iss`` (RFC 9207) → ``/token``
(SDK handler: PKCE S256, redirect URI, code expiry) → an encrypted access token (one hour)
and a rotating refresh token.

Clients register with a Client ID Metadata Document (FastMCP's ``CIMDClientManager``) or,
for compatibility, Dynamic Client Registration. Short-lived records (registrations,
pending authorizations, codes, refresh-rotation state) live in a pluggable key-value
store, in memory by default.
"""

from __future__ import annotations

import asyncio
import hmac
import logging
import secrets
import time
from collections.abc import Callable
from typing import Any
from urllib.parse import parse_qs, urlsplit

from fastmcp.server.auth.auth import AccessToken, OAuthProvider, TokenHandler
from fastmcp.server.auth.cimd import CIMDClientManager
from key_value.aio.protocols import AsyncKeyValue
from key_value.aio.stores.memory import MemoryStore
from mcp.server.auth.handlers.authorize import AuthorizationHandler
from mcp.server.auth.handlers.metadata import MetadataHandler
from mcp.server.auth.json_response import PydanticJSONResponse
from mcp.server.auth.middleware.client_auth import AuthenticationError, ClientAuthenticator
from mcp.server.auth.provider import (
    AuthorizationCode,
    AuthorizationParams,
    AuthorizeError,
    RefreshToken,
    RegistrationError,
    TokenError,
    construct_redirect_uri,
)
from mcp.server.auth.routes import build_metadata, cors_middleware
from mcp.server.auth.settings import ClientRegistrationOptions, RevocationOptions
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken
from pydantic import AnyUrl
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.routing import Route

from firms_mcp.auth.connect_page import render_connect_form, render_problem
from firms_mcp.auth.tokens import InvalidToken, TokenCodec
from firms_mcp.credentials import MAP_KEY_CLAIM, MAP_KEY_PATTERN
from firms_mcp.firms.client import FirmsClient
from firms_mcp.firms.errors import FirmsError, InvalidMapKey, MapKeyRejected
from firms_mcp.redaction import register_secret

logger = logging.getLogger(__name__)

SCOPE = "firms:data"
CONNECT_PATH = "/connect"
BINDING_COOKIE = "firms_mcp_connect"

PENDING_TTL_SECONDS = 600
CODE_TTL_SECONDS = 300
MAX_CONNECT_ATTEMPTS = 5
CLIENT_TTL_SECONDS = 90 * 24 * 3600

ACCESS_TYP = "at+jwe"
REFRESH_TYP = "rt+jwe"
CODE_TYP = "code+jwe"

CLIENTS = "firms-mcp-clients"
PENDING = "firms-mcp-pending"
CODES = "firms-mcp-codes"
USED_REFRESH = "firms-mcp-used-refresh"
REVOKED_FAMILIES = "firms-mcp-revoked-families"

_LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "[::1]", "::1"}
_FORBIDDEN_SCHEMES = {"javascript", "data", "file", "vbscript", "about", "blob"}


def _redirect_uri_is_acceptable(uri: str) -> bool:
    """https anywhere, http only on loopback (RFC 8252), or a native app's private scheme."""
    parts = urlsplit(uri)
    scheme = parts.scheme.lower()
    if parts.fragment or scheme in _FORBIDDEN_SCHEMES or not scheme:
        return False
    if scheme == "https":
        return bool(parts.hostname)
    if scheme == "http":
        return (parts.hostname or "").lower() in _LOOPBACK_HOSTS
    return True


class FirmsOAuthProvider(OAuthProvider):
    def __init__(
        self,
        *,
        base_url: str,
        codec: TokenCodec,
        firms: FirmsClient,
        mcp_path: str = "/mcp",
        store: AsyncKeyValue | None = None,
        access_token_ttl: int = 3600,
        refresh_token_ttl: int = 30 * 24 * 3600,
        enable_dcr: bool = True,
        enable_cimd: bool = True,
        clock: Callable[[], float] = time.time,
    ) -> None:
        super().__init__(
            base_url=base_url,
            client_registration_options=ClientRegistrationOptions(
                enabled=enable_dcr, valid_scopes=[SCOPE], default_scopes=[SCOPE]
            ),
            revocation_options=RevocationOptions(enabled=True),
            required_scopes=[SCOPE],
        )
        self.codec = codec
        self.firms = firms
        self.store: AsyncKeyValue = store or MemoryStore()
        self.access_token_ttl = access_token_ttl
        self.refresh_token_ttl = refresh_token_ttl
        self.enable_cimd = enable_cimd
        self.cimd = CIMDClientManager(enable_cimd=enable_cimd, default_scope=SCOPE)
        self.clock = clock
        self._rotation_lock = asyncio.Lock()
        self.set_mcp_path(mcp_path)

    # -- identities -----------------------------------------------------------------------
    @property
    def issuer(self) -> str:
        return str(self.issuer_url)

    @property
    def resource(self) -> str:
        return str(self._resource_url)

    @property
    def base(self) -> str:
        return str(self.base_url).rstrip("/")

    def _is_this_resource(self, value: str | None) -> bool:
        return value is None or value.rstrip("/") == self.resource.rstrip("/")

    def binding(self, pending_id: str) -> str:
        """The browser-binding value for a pending authorization (set as a cookie)."""
        return hmac.new(self.codec.binding_secret, pending_id.encode(), "sha256").hexdigest()

    # -- clients (CIMD preferred, DCR for compatibility) -------------------------------------
    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        if self.cimd.is_cimd_client_id(client_id):
            return await self.cimd.get_client(client_id)
        data = await self.store.get(client_id, collection=CLIENTS)
        return OAuthClientInformationFull.model_validate(data) if data else None

    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        if client_info.client_id is None:
            raise RegistrationError("invalid_client_metadata", "client_id is required")
        if client_info.scope and set(client_info.scope.split()) - {SCOPE}:
            raise RegistrationError(
                "invalid_client_metadata", f"the only scope this server grants is {SCOPE}"
            )
        for uri in client_info.redirect_uris or []:
            if not _redirect_uri_is_acceptable(str(uri)):
                raise RegistrationError(
                    "invalid_redirect_uri",
                    "redirect URIs must use https, http on a loopback address, or an app's own scheme",
                )
        await self.store.put(
            client_info.client_id,
            client_info.model_dump(mode="json"),
            collection=CLIENTS,
            ttl=CLIENT_TTL_SECONDS,
        )

    # -- authorization ----------------------------------------------------------------------
    async def authorize(
        self, client: OAuthClientInformationFull, params: AuthorizationParams
    ) -> str:
        if not self._is_this_resource(params.resource):
            raise AuthorizeError(
                error="invalid_target",
                error_description=f"this authorization server issues tokens only for {self.resource}",
            )
        assert client.client_id is not None
        verified = self.cimd.is_cimd_client_id(client.client_id)
        name = getattr(client, "client_name", None) or client.client_id
        if verified:
            name = f"{name} ({urlsplit(client.client_id).hostname})"
        pending_id = secrets.token_urlsafe(24)
        await self.store.put(
            pending_id,
            {
                "client_id": client.client_id,
                "client_name": name,
                "client_verified": verified,
                "redirect_uri": str(params.redirect_uri),
                "redirect_uri_provided_explicitly": params.redirect_uri_provided_explicitly,
                "scopes": params.scopes or [SCOPE],
                "code_challenge": params.code_challenge,
                "state": params.state,
                "resource": params.resource,
                "csrf": secrets.token_urlsafe(24),
                "attempts": 0,
                "expires_at": self.clock() + PENDING_TTL_SECONDS,
            },
            collection=PENDING,
            ttl=PENDING_TTL_SECONDS,
        )
        return f"{self.base}{CONNECT_PATH}?txn={pending_id}"

    async def _pending(self, pending_id: str | None) -> dict[str, Any] | None:
        if not pending_id:
            return None
        record = await self.store.get(pending_id, collection=PENDING)
        if record is None or record["expires_at"] <= self.clock():
            return None
        return record

    def _client_redirect(self, record: dict[str, Any], **params: str | None) -> RedirectResponse:
        url = construct_redirect_uri(
            record["redirect_uri"], **params, state=record.get("state"), iss=self.issuer
        )
        response = RedirectResponse(url, status_code=303, headers={"Cache-Control": "no-store"})
        response.delete_cookie(BINDING_COOKIE, path=CONNECT_PATH)
        return response

    def _bound(self, request: Request, pending_id: str) -> bool:
        cookie = request.cookies.get(BINDING_COOKIE, "")
        return hmac.compare_digest(cookie, self.binding(pending_id))

    def _form(
        self, pending_id: str, record: dict[str, Any], error: str | None = None, status: int = 200
    ):
        return render_connect_form(
            txn=pending_id,
            csrf=record["csrf"],
            client_name=record["client_name"],
            client_verified=record["client_verified"],
            redirect_host=urlsplit(record["redirect_uri"]).netloc or record["redirect_uri"],
            redirect_uri=record["redirect_uri"],
            error=error,
            status_code=status,
        )

    async def connect_page(self, request: Request) -> Response:
        pending_id = request.query_params.get("txn")
        record = await self._pending(pending_id)
        if record is None or pending_id is None:
            return render_problem(
                "This connection request is unknown or has expired. Start again from your app."
            )
        if not self._bound(request, pending_id):
            return render_problem(
                "This page must be opened from your app's sign-in step in this browser. "
                "Start again from your app.",
                status_code=403,
            )
        return self._form(pending_id, record)

    async def connect_submit(self, request: Request) -> Response:
        form = await request.form()
        pending_id = str(form.get("txn") or "")
        record = await self._pending(pending_id)
        if record is None:
            return render_problem(
                "This connection request is unknown or has expired. Start again from your app."
            )
        if not self._bound(request, pending_id) or not hmac.compare_digest(
            str(form.get("csrf") or ""), record["csrf"]
        ):
            return render_problem(
                "This form was not submitted from the page this server showed you. Start "
                "again from your app.",
                status_code=403,
            )
        if form.get("action") == "deny":
            await self.store.delete(pending_id, collection=PENDING)
            return self._client_redirect(
                record,
                error="access_denied",
                error_description="The user did not connect a MAP_KEY.",
            )

        record["attempts"] += 1
        if record["attempts"] > MAX_CONNECT_ATTEMPTS:
            await self.store.delete(pending_id, collection=PENDING)
            return render_problem("Too many attempts. Start again from your app.", status_code=429)
        remaining = max(1, int(record["expires_at"] - self.clock()))
        await self.store.put(pending_id, record, collection=PENDING, ttl=remaining)

        map_key = str(form.get("map_key") or "").strip()
        if not MAP_KEY_PATTERN.fullmatch(map_key):
            return self._form(
                pending_id,
                record,
                "A FIRMS MAP_KEY is 32 letters and digits. Check the key and try again.",
                400,
            )
        register_secret(map_key)
        try:
            await self.firms.map_key_status(map_key)
        except (InvalidMapKey, MapKeyRejected):
            return self._form(
                pending_id,
                record,
                "FIRMS did not accept this MAP_KEY. It may be mistyped, or it may have reached "
                "its limit of 5,000 transactions per 10 minutes; wait a few minutes if so.",
                400,
            )
        except FirmsError:
            logger.warning("could not check a MAP_KEY with FIRMS", exc_info=True)
            return self._form(
                pending_id,
                record,
                "FIRMS could not be reached to check the key. Try again shortly.",
                503,
            )

        code = secrets.token_urlsafe(32)
        await self.store.put(
            code,
            {
                "client_id": record["client_id"],
                "redirect_uri": record["redirect_uri"],
                "redirect_uri_provided_explicitly": record["redirect_uri_provided_explicitly"],
                "scopes": record["scopes"],
                "code_challenge": record["code_challenge"],
                "resource": record["resource"],
                "expires_at": self.clock() + CODE_TTL_SECONDS,
                "sealed_key": self.codec.seal({"mk": map_key}, typ=CODE_TYP),
            },
            collection=CODES,
            ttl=CODE_TTL_SECONDS,
        )
        await self.store.delete(pending_id, collection=PENDING)
        logger.info("MAP_KEY connected for client %s", record["client_id"])
        return self._client_redirect(record, code=code)

    # -- codes and tokens ------------------------------------------------------------------
    async def load_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: str
    ) -> AuthorizationCode | None:
        record = await self.store.get(authorization_code, collection=CODES)
        if record is None or record["client_id"] != client.client_id:
            return None
        return AuthorizationCode(
            code=authorization_code,
            scopes=record["scopes"],
            expires_at=record["expires_at"],
            client_id=record["client_id"],
            code_challenge=record["code_challenge"],
            redirect_uri=AnyUrl(record["redirect_uri"]),
            redirect_uri_provided_explicitly=record["redirect_uri_provided_explicitly"],
            resource=record["resource"],
        )

    async def exchange_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: AuthorizationCode
    ) -> OAuthToken:
        async with self._rotation_lock:
            record = await self.store.get(authorization_code.code, collection=CODES)
            if record is None:
                raise TokenError("invalid_grant", "authorization code already used or expired")
            await self.store.delete(authorization_code.code, collection=CODES)  # single use
        map_key = self.codec.open(record["sealed_key"], typ=CODE_TYP)["mk"]
        assert client.client_id is not None
        return self._issue(client.client_id, record["scopes"], map_key)

    def _issue(
        self, client_id: str, scopes: list[str], map_key: str, family: str | None = None
    ) -> OAuthToken:
        now = int(self.clock())
        common = {
            "iss": self.issuer,
            "aud": self.resource,
            "client_id": client_id,
            "scope": " ".join(scopes),
            "iat": now,
            "sub": self.codec.subject(map_key),
            "mk": map_key,
        }
        access = self.codec.seal(
            {**common, "exp": now + self.access_token_ttl, "jti": secrets.token_urlsafe(12)},
            typ=ACCESS_TYP,
        )
        refresh = self.codec.seal(
            {
                **common,
                "exp": now + self.refresh_token_ttl,
                "jti": secrets.token_urlsafe(12),
                "fid": family or secrets.token_urlsafe(12),
            },
            typ=REFRESH_TYP,
        )
        return OAuthToken(
            access_token=access,
            token_type="Bearer",
            expires_in=self.access_token_ttl,
            refresh_token=refresh,
            scope=" ".join(scopes),
        )

    def _open(self, token: str, typ: str) -> dict[str, Any] | None:
        """Claims of a token this server issued for this resource and not yet expired."""
        try:
            claims = self.codec.open(token, typ=typ)
        except InvalidToken:
            return None
        if claims.get("iss") != self.issuer or claims.get("aud") != self.resource:
            return None
        if not isinstance(claims.get("exp"), int) or claims["exp"] <= self.clock():
            return None
        return claims

    async def load_access_token(self, token: str) -> AccessToken | None:  # type: ignore[override]
        claims = self._open(token, ACCESS_TYP)
        if claims is None:
            return None
        return AccessToken(
            token=token,
            client_id=claims["client_id"],
            scopes=claims["scope"].split(),
            expires_at=claims["exp"],
            resource=claims["aud"],
            subject=claims["sub"],
            claims={
                "iss": claims["iss"],
                "aud": claims["aud"],
                "sub": claims["sub"],
                "jti": claims["jti"],
                MAP_KEY_CLAIM: claims["mk"],
            },
        )

    async def _revoke_family(self, family: str) -> None:
        await self.store.put(
            family, {"revoked": True}, collection=REVOKED_FAMILIES, ttl=self.refresh_token_ttl
        )

    async def load_refresh_token(
        self, client: OAuthClientInformationFull, refresh_token: str
    ) -> RefreshToken | None:
        claims = self._open(refresh_token, REFRESH_TYP)
        if claims is None or claims["client_id"] != client.client_id:
            return None
        if await self.store.get(claims["fid"], collection=REVOKED_FAMILIES):
            return None
        if await self.store.get(claims["jti"], collection=USED_REFRESH):
            logger.warning("refresh token replay detected; revoking its token family")
            await self._revoke_family(claims["fid"])
            return None
        return RefreshToken(
            token=refresh_token,
            client_id=claims["client_id"],
            scopes=claims["scope"].split(),
            expires_at=claims["exp"],
            resource=claims["aud"],
            subject=claims["sub"],
        )

    async def exchange_refresh_token(
        self,
        client: OAuthClientInformationFull,
        refresh_token: RefreshToken,
        scopes: list[str],
    ) -> OAuthToken:
        claims = self._open(refresh_token.token, REFRESH_TYP)
        if claims is None:
            raise TokenError("invalid_grant", "refresh token is not valid")
        async with self._rotation_lock:
            if await self.store.get(claims["jti"], collection=USED_REFRESH):
                await self._revoke_family(claims["fid"])
                raise TokenError("invalid_grant", "refresh token already used")
            ttl = max(1, claims["exp"] - int(self.clock()))
            await self.store.put(
                claims["jti"], {"fid": claims["fid"]}, collection=USED_REFRESH, ttl=ttl
            )
        assert client.client_id is not None
        return self._issue(client.client_id, scopes, claims["mk"], family=claims["fid"])

    async def revoke_token(self, token: AccessToken | RefreshToken) -> None:  # type: ignore[override]
        # Access tokens are stateless and short-lived (ADR-0004); revoking a refresh token
        # revokes its whole rotation family.
        if isinstance(token, RefreshToken):
            claims = self._open(token.token, REFRESH_TYP)
            if claims is not None:
                await self._revoke_family(claims["fid"])

    # -- routes -----------------------------------------------------------------------------
    def _metadata_route(self) -> Route:
        metadata = build_metadata(
            self.base_url,  # type: ignore[arg-type]
            self.service_documentation_url,
            self.client_registration_options or ClientRegistrationOptions(),
            self.revocation_options or RevocationOptions(),
        )
        metadata.issuer = self.issuer_url  # type: ignore[assignment]
        metadata.client_id_metadata_document_supported = self.enable_cimd
        metadata.authorization_response_iss_parameter_supported = True
        methods = ["none", "client_secret_post", "client_secret_basic"]
        metadata.token_endpoint_auth_methods_supported = methods
        metadata.revocation_endpoint_auth_methods_supported = methods
        handler = MetadataHandler(metadata)
        return Route(
            "/.well-known/oauth-authorization-server",
            endpoint=cors_middleware(handler.handle, ["GET", "OPTIONS"]),
            methods=["GET", "OPTIONS"],
        )

    def _authorize_route(self) -> Route:
        handler = AuthorizationHandler(self)
        connect_prefix = f"{self.base}{CONNECT_PATH}?"
        secure = self.base.startswith("https://")

        async def authorize(request: Request) -> Response:
            response = await handler.handle(request)
            location = response.headers.get("location")
            if location is None:
                return response
            if location.startswith(connect_prefix):
                pending_id = parse_qs(urlsplit(location).query).get("txn", [""])[0]
                response.set_cookie(
                    BINDING_COOKIE,
                    self.binding(pending_id),
                    max_age=PENDING_TTL_SECONDS,
                    path=CONNECT_PATH,
                    secure=secure,
                    httponly=True,
                    samesite="lax",
                )
                return response
            # An error returned to the client's redirect URI: add iss (RFC 9207).
            return RedirectResponse(
                construct_redirect_uri(location, iss=self.issuer),
                status_code=302,
                headers={"Cache-Control": "no-store"},
            )

        return Route("/authorize", endpoint=authorize, methods=["GET", "POST"])

    def _token_route(self) -> Route:
        handler = TokenHandler(provider=self, client_authenticator=ClientAuthenticator(self))

        async def token(request: Request) -> Response:
            form = await request.form()  # cached on the request for the handler
            resource = form.get("resource")
            if isinstance(resource, str) and not self._is_this_resource(resource):
                return PydanticJSONResponse(
                    content={
                        "error": "invalid_target",
                        "error_description": f"tokens are issued only for {self.resource}",
                    },
                    status_code=400,
                    headers={"Cache-Control": "no-store"},
                )
            return await handler.handle(request)

        return Route(
            "/token",
            endpoint=cors_middleware(token, ["POST", "OPTIONS"]),
            methods=["POST", "OPTIONS"],
        )

    def _revoke_route(self) -> Route:
        """RFC 7009 revocation that also serves public (PKCE) clients.

        The SDK's handler requires a ``client_secret`` form field, which public clients do
        not have (integration issue II-14)."""
        authenticator = ClientAuthenticator(self)

        async def revoke(request: Request) -> Response:
            try:
                client = await authenticator.authenticate_request(request)
            except AuthenticationError as exc:
                return PydanticJSONResponse(
                    content={"error": "invalid_client", "error_description": exc.message},
                    status_code=401,
                )
            form = await request.form()
            token = form.get("token")
            if not isinstance(token, str) or not token:
                return PydanticJSONResponse(
                    content={"error": "invalid_request", "error_description": "token is required"},
                    status_code=400,
                )
            found = await self.load_refresh_token(client, token) or await self.load_access_token(
                token
            )
            if found is not None and found.client_id == client.client_id:
                await self.revoke_token(found)
            # Unknown or foreign tokens also get 200 (RFC 7009 §2.2).
            return Response(
                status_code=200, headers={"Cache-Control": "no-store", "Pragma": "no-cache"}
            )

        return Route(
            "/revoke",
            endpoint=cors_middleware(revoke, ["POST", "OPTIONS"]),
            methods=["POST", "OPTIONS"],
        )

    def get_routes(self, mcp_path: str | None = None) -> list[Route]:
        replacements = {
            "/.well-known/oauth-authorization-server": self._metadata_route(),
            "/authorize": self._authorize_route(),
            "/token": self._token_route(),
            "/revoke": self._revoke_route(),
        }
        routes: list[Route] = []
        for route in super().get_routes(mcp_path):
            path = getattr(route, "path", None)
            routes.append(replacements.pop(path) if path in replacements else route)
        routes.append(Route(CONNECT_PATH, endpoint=self.connect_page, methods=["GET"]))
        routes.append(Route(CONNECT_PATH, endpoint=self.connect_submit, methods=["POST"]))
        return routes
