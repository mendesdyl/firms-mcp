"""The MAP_KEY connect flow end to end, in-process (ADR-0004; FR-AUTH-002 … FR-AUTH-010,
SEC-001, SEC-003, SEC-004).

The app runs with OAuth enabled at ``https://testserver``. FIRMS (MAP_KEY status and the
area API) is mocked with respx; MCP and OAuth traffic goes through httpx2's ASGI transport.
"""

from __future__ import annotations

import base64
import contextlib
import hashlib
import json
import re
import secrets
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from urllib.parse import parse_qs, urlencode, urlsplit

import httpx2
import pytest
import respx
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from fastmcp.server.auth.cimd import CIMDDocument

from firms_mcp.auth.tokens import TokenCodec, generate_key_spec
from firms_mcp.credentials import CredentialMode
from firms_mcp.server import create_auth_provider, create_http_app, create_server
from tests.fixtures import firms_csv
from tests.fixtures.firms_csv import MAP_KEY, OTHER_KEY
from tests.fixtures.services import FIRMS_BASE, make_services

BASE = "https://testserver"
RESOURCE = f"{BASE}/mcp"
ISSUER = f"{BASE}/"
REDIRECT = "http://127.0.0.1:33418/callback"
LA_URL = f"{FIRMS_BASE}/api/area/csv/{MAP_KEY}/MODIS_NRT/-119.2,33.8,-117.6,34.6/1/2025-01-08"
STATUS_URL = f"{FIRMS_BASE}/mapserver/mapkey_status/"
DETECTIONS_ARGS = {
    "area": {"west": -119.2, "south": 33.8, "east": -117.6, "north": 34.6},
    "date": "2025-01-08",
    "sources": ["MODIS_NRT"],
}


@dataclass
class OAuthApp:
    http: httpx2.AsyncClient
    provider: object
    app: object
    client_id: str = ""
    verifier: str = field(default_factory=lambda: secrets.token_urlsafe(48))

    @property
    def challenge(self) -> str:
        digest = hashlib.sha256(self.verifier.encode()).digest()
        return base64.urlsafe_b64encode(digest).decode().rstrip("=")


@contextlib.asynccontextmanager
async def oauth_app(**settings: object) -> AsyncIterator[OAuthApp]:
    services = make_services(
        mode=CredentialMode.REMOTE,
        FIRMS_MCP_PUBLIC_URL=BASE,
        FIRMS_MCP_TOKEN_KEYS=generate_key_spec("test"),
        **settings,
    )
    provider = create_auth_provider(services)
    app = create_http_app(create_server(services=services), auth=provider)
    async with (
        app.router.lifespan_context(app),
        httpx2.AsyncClient(transport=httpx2.ASGITransport(app=app), base_url=BASE) as http,
    ):
        yield OAuthApp(http=http, provider=provider, app=app)


async def register(oauth: OAuthApp, redirect_uris: list[str] | None = None) -> httpx2.Response:
    response = await oauth.http.post(
        "/register",
        json={
            "redirect_uris": redirect_uris or [REDIRECT],
            "token_endpoint_auth_method": "none",
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "client_name": "Test Client",
        },
    )
    if response.status_code == 201:
        oauth.client_id = response.json()["client_id"]
    return response


async def start_authorization(oauth: OAuthApp, **overrides: str) -> httpx2.Response:
    params = {
        "response_type": "code",
        "client_id": oauth.client_id,
        "redirect_uri": REDIRECT,
        "code_challenge": oauth.challenge,
        "code_challenge_method": "S256",
        "state": "state-123",
        "scope": "firms:data",
        "resource": RESOURCE,
        **overrides,
    }
    return await oauth.http.get(f"/authorize?{urlencode(params)}")


def csrf_from(page: str) -> str:
    match = re.search(r'name="csrf" value="([^"]+)"', page)
    assert match, "no CSRF field on the page"
    return match.group(1)


async def connect(oauth: OAuthApp, map_key: str = MAP_KEY) -> tuple[str, httpx2.Response]:
    """Run /authorize and the connect page; return the pending ID and the POST response."""
    started = await start_authorization(oauth)
    assert started.status_code == 302, started.text
    connect_url = started.headers["location"]
    txn = parse_qs(urlsplit(connect_url).query)["txn"][0]
    page = await oauth.http.get(connect_url)
    assert page.status_code == 200, page.text
    submitted = await oauth.http.post(
        "/connect",
        data={"txn": txn, "csrf": csrf_from(page.text), "map_key": map_key, "action": "connect"},
    )
    return txn, submitted


async def get_tokens(oauth: OAuthApp, router: respx.MockRouter) -> dict:
    router.get(STATUS_URL, params={"MAP_KEY": MAP_KEY}).respond(
        200, json={"transaction_limit": 5000, "current_transactions": 0}
    )
    await register(oauth)
    _, submitted = await connect(oauth)
    assert submitted.status_code == 303, submitted.text
    query = parse_qs(urlsplit(submitted.headers["location"]).query)
    token = await oauth.http.post(
        "/token",
        data={
            "grant_type": "authorization_code",
            "code": query["code"][0],
            "redirect_uri": REDIRECT,
            "client_id": oauth.client_id,
            "code_verifier": oauth.verifier,
            "resource": RESOURCE,
        },
    )
    assert token.status_code == 200, token.text
    return token.json()


def tools_call(name: str, arguments: dict, *, modern: bool) -> tuple[dict, dict]:
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    }
    headers = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}
    if modern:
        body["params"]["_meta"] = {
            "io.modelcontextprotocol/protocolVersion": "2026-07-28",
            "io.modelcontextprotocol/clientCapabilities": {},
        }
        headers |= {
            "MCP-Protocol-Version": "2026-07-28",
            "Mcp-Method": "tools/call",
            "Mcp-Name": name,
        }
    return body, headers


# -- discovery and challenges --------------------------------------------------------------


@pytest.mark.req("FR-AUTH-004", "FR-AUTH-005", "FR-AUTH-007")
async def test_metadata_is_published() -> None:
    async with oauth_app() as oauth:
        prm = (await oauth.http.get("/.well-known/oauth-protected-resource/mcp")).json()
        asm = (await oauth.http.get("/.well-known/oauth-authorization-server")).json()
    assert prm["resource"] == RESOURCE
    assert prm["authorization_servers"] == [ISSUER]
    assert prm["scopes_supported"] == ["firms:data"]
    assert asm["issuer"] == ISSUER
    assert asm["authorization_endpoint"] == f"{BASE}/authorize"
    assert asm["token_endpoint"] == f"{BASE}/token"
    assert asm["registration_endpoint"] == f"{BASE}/register"
    assert asm["code_challenge_methods_supported"] == ["S256"]
    assert asm["client_id_metadata_document_supported"] is True  # CIMD
    assert asm["authorization_response_iss_parameter_supported"] is True  # RFC 9207
    assert "none" in asm["token_endpoint_auth_methods_supported"]


@pytest.mark.req("FR-AUTH-003", "FR-AUTH-002")
@pytest.mark.parametrize("modern", [False, True], ids=["handshake-era", "2026-07-28"])
async def test_protected_tools_are_challenged_and_others_are_not(modern: bool) -> None:
    async with oauth_app() as oauth:
        body, headers = tools_call("get_fire_detections", DETECTIONS_ARGS, modern=modern)
        challenged = await oauth.http.post("/mcp", json=body, headers=headers)
        bad_token = await oauth.http.post(
            "/mcp", json=body, headers={**headers, "Authorization": "Bearer not-a-token"}
        )
        body, headers = tools_call("search_knowledge", {"query": "UTC"}, modern=modern)
        anonymous = await oauth.http.post("/mcp", json=body, headers=headers)
    assert challenged.status_code == 401
    challenge = challenged.headers["www-authenticate"]
    assert challenge.startswith("Bearer ")
    assert f'resource_metadata="{BASE}/.well-known/oauth-protected-resource/mcp"' in challenge
    assert 'scope="firms:data"' in challenge
    assert "error=" not in challenge  # no credentials yet: RFC 6750 §3.1
    assert bad_token.status_code == 401
    assert 'error="invalid_token"' in bad_token.headers["www-authenticate"]
    assert anonymous.status_code != 401  # anonymous tools reach the MCP layer
    if modern:  # stateless: the anonymous call completes
        assert anonymous.status_code == 200 and '\\"status\\": \\"success\\"' in anonymous.text


@pytest.mark.req("FR-AUTH-003")
async def test_modern_requests_cannot_name_one_tool_and_call_another() -> None:
    """The step-up trusts Mcp-Name on 2026-07-28 requests because the SDK rejects any
    request whose headers disagree with its body; this checks that assumption."""
    async with oauth_app() as oauth:
        body, headers = tools_call("get_fire_detections", DETECTIONS_ARGS, modern=True)
        spoofed = await oauth.http.post(
            "/mcp", json=body, headers={**headers, "Mcp-Name": "search_knowledge"}
        )
    assert spoofed.status_code == 400
    assert "header does not match the request body" in spoofed.json()["error"]["message"]


# -- registration ---------------------------------------------------------------------------


@pytest.mark.req("FR-AUTH-005", "SEC-003")
async def test_dynamic_registration_rejects_unsafe_redirect_uris() -> None:
    async with oauth_app() as oauth:
        ok = await register(oauth)
        assert ok.status_code == 201
        for bad in (
            "javascript:alert(1)",
            "http://evil.example.com/callback",
            "https://x.test/cb#frag",
        ):
            response = await register(oauth, [bad])
            assert response.status_code == 400, bad
            assert response.json()["error"] in {"invalid_redirect_uri", "invalid_client_metadata"}


@pytest.mark.req("FR-AUTH-005")
async def test_client_id_metadata_document_clients() -> None:
    client_id = "https://client.example.com/oauth/client.json"
    document = CIMDDocument(
        client_id=client_id,
        client_name="Example Client",
        redirect_uris=["https://client.example.com/callback"],
        token_endpoint_auth_method="none",
        grant_types=["authorization_code", "refresh_token"],
    )
    async with oauth_app() as oauth:

        async def fetch(url: str) -> CIMDDocument:
            assert url == client_id
            return document

        oauth.provider.cimd._fetcher.fetch = fetch  # no network: the document is served here
        oauth.client_id = client_id
        good = await start_authorization(oauth, redirect_uri="https://client.example.com/callback")
        bad = await start_authorization(oauth, redirect_uri="https://attacker.example.net/callback")
        page = await oauth.http.get(good.headers["location"])
    assert good.status_code == 302 and "/connect?txn=" in good.headers["location"]
    assert bad.status_code == 400  # not in the document: no redirect to the attacker
    assert "Example Client (client.example.com)" in page.text
    assert "verified" in page.text


# -- authorization and connect page ---------------------------------------------------------


@pytest.mark.req("FR-AUTH-006", "FR-AUTH-007", "SEC-003")
async def test_connect_page_and_code_redirect_with_iss() -> None:
    with respx.mock(assert_all_called=True) as router:
        status = router.get(STATUS_URL, params={"MAP_KEY": MAP_KEY}).respond(
            200, json={"transaction_limit": 5000, "current_transactions": 0}
        )
        async with oauth_app() as oauth:
            await register(oauth)
            started = await start_authorization(oauth)
            page = await oauth.http.get(started.headers["location"])
            _, submitted = await connect(oauth)
    assert started.status_code == 302
    assert "firms_mcp_connect" in started.headers["set-cookie"]
    assert "httponly" in started.headers["set-cookie"].lower()
    # The page: who asks, where the user returns, where the key goes, not NASA's.
    assert page.status_code == 200
    assert "Test Client" in page.text and "127.0.0.1:33418" in page.text
    assert "The AI model never sees it" in page.text
    assert "not operated or endorsed by NASA" in page.text
    assert 'type="password"' in page.text
    assert "<script" not in page.text
    csp = page.headers["content-security-policy"]
    assert "default-src 'none'" in csp and "frame-ancestors 'none'" in csp
    assert "form-action 'self' http://127.0.0.1:33418" in csp
    assert page.headers["x-frame-options"] == "DENY"
    # The redirect carries the code, the client's state, and the issuer (RFC 9207).
    assert submitted.status_code == 303
    location = urlsplit(submitted.headers["location"])
    assert f"{location.scheme}://{location.netloc}{location.path}" == REDIRECT
    query = parse_qs(location.query)
    assert query["state"] == ["state-123"] and query["iss"] == [ISSUER] and query["code"]
    assert status.call_count == 1  # the key is checked with FIRMS once, on submit
    assert MAP_KEY not in submitted.headers["location"]


@pytest.mark.req("FR-AUTH-006")
async def test_connect_page_explains_rejected_keys() -> None:
    with respx.mock() as router:
        router.get(STATUS_URL, params={"MAP_KEY": OTHER_KEY}).respond(
            403, text="MAP_KEY is invalid or your have exceeded your transaction/time limit."
        )
        async with oauth_app() as oauth:
            await register(oauth)
            _, malformed = await connect(oauth, map_key="too-short")
            _, rejected = await connect(oauth, map_key=OTHER_KEY)
    assert malformed.status_code == 400 and "32 letters and digits" in malformed.text
    assert rejected.status_code == 400 and "FIRMS did not accept this MAP_KEY" in rejected.text
    assert OTHER_KEY not in rejected.text


@pytest.mark.req("SEC-003")
async def test_connect_requires_the_browser_binding_and_csrf_token() -> None:
    async with oauth_app() as oauth:
        await register(oauth)
        started = await start_authorization(oauth)
        txn = parse_qs(urlsplit(started.headers["location"]).query)["txn"][0]
        page = await oauth.http.get(started.headers["location"])
        csrf = csrf_from(page.text)
        wrong_csrf = await oauth.http.post(
            "/connect", data={"txn": txn, "csrf": "forged", "map_key": MAP_KEY}
        )
        oauth.http.cookies.clear()  # another browser, or a link sent by someone else
        no_cookie_page = await oauth.http.get(started.headers["location"])
        no_cookie = await oauth.http.post(
            "/connect", data={"txn": txn, "csrf": csrf, "map_key": MAP_KEY}
        )
    assert wrong_csrf.status_code == 403
    assert no_cookie_page.status_code == 403
    assert no_cookie.status_code == 403


@pytest.mark.req("SEC-003")
async def test_unregistered_redirect_uri_is_never_followed() -> None:
    async with oauth_app() as oauth:
        await register(oauth)
        response = await start_authorization(oauth, redirect_uri="http://127.0.0.1:9999/other")
    assert response.status_code == 400
    assert "location" not in response.headers


@pytest.mark.req("FR-AUTH-007", "SEC-004")
async def test_errors_returned_to_the_client_carry_iss_and_resource_is_checked() -> None:
    async with oauth_app() as oauth:
        await register(oauth)
        bad_scope = await start_authorization(oauth, scope="admin")
        other_resource = await start_authorization(oauth, resource="https://elsewhere.example/mcp")
    for response, error in ((bad_scope, "invalid_scope"), (other_resource, "invalid_target")):
        assert response.status_code == 302
        query = parse_qs(urlsplit(response.headers["location"]).query)
        assert query["error"] == [error]
        assert query["iss"] == [ISSUER]
        assert query["state"] == ["state-123"]


async def test_the_user_can_decline() -> None:
    async with oauth_app() as oauth:
        await register(oauth)
        started = await start_authorization(oauth)
        txn = parse_qs(urlsplit(started.headers["location"]).query)["txn"][0]
        page = await oauth.http.get(started.headers["location"])
        declined = await oauth.http.post(
            "/connect", data={"txn": txn, "csrf": csrf_from(page.text), "action": "deny"}
        )
    query = parse_qs(urlsplit(declined.headers["location"]).query)
    assert declined.status_code == 303 and query["error"] == ["access_denied"]
    assert query["iss"] == [ISSUER]


# -- tokens -------------------------------------------------------------------------------


@pytest.mark.req("FR-AUTH-007", "FR-AUTH-008")
async def test_codes_are_single_use_and_tokens_are_encrypted() -> None:
    with respx.mock() as router:
        router.get(STATUS_URL, params={"MAP_KEY": MAP_KEY}).respond(
            200, json={"transaction_limit": 5000, "current_transactions": 0}
        )
        async with oauth_app() as oauth:
            await register(oauth)
            _, submitted = await connect(oauth)
            code = parse_qs(urlsplit(submitted.headers["location"]).query)["code"][0]
            form = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT,
                "client_id": oauth.client_id,
                "code_verifier": oauth.verifier,
            }
            wrong_verifier = await oauth.http.post(
                "/token", data={**form, "code_verifier": "x" * 64}
            )
            first = await oauth.http.post("/token", data=form)
            again = await oauth.http.post("/token", data=form)
    assert wrong_verifier.status_code in (400, 401)
    assert wrong_verifier.json()["error"] == "invalid_grant"
    assert first.status_code == 200
    tokens = first.json()
    assert tokens["token_type"] == "Bearer" and tokens["expires_in"] == 3600
    assert tokens["scope"] == "firms:data"
    for token in (tokens["access_token"], tokens["refresh_token"]):
        assert token.count(".") == 4  # JWE compact serialization
        header = json.loads(base64.urlsafe_b64decode(token.split(".")[0] + "=="))
        assert header["alg"] == "dir" and header["enc"] == "A256GCM"
        assert MAP_KEY not in token
    assert again.status_code == 401 and again.json()["error"] == "invalid_grant"


@pytest.mark.req("FR-AUTH-009")
async def test_refresh_tokens_rotate_and_replay_revokes_the_family() -> None:
    with respx.mock() as router:
        async with oauth_app() as oauth:
            tokens = await get_tokens(oauth, router)

            async def refresh(token: str) -> httpx2.Response:
                return await oauth.http.post(
                    "/token",
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": token,
                        "client_id": oauth.client_id,
                    },
                )

            rotated = await refresh(tokens["refresh_token"])
            assert rotated.status_code == 200
            new_refresh = rotated.json()["refresh_token"]
            assert new_refresh != tokens["refresh_token"]
            replay = await refresh(tokens["refresh_token"])
            after_replay = await refresh(new_refresh)
    assert replay.status_code == 401 and replay.json()["error"] == "invalid_grant"
    # Replay of a used token revokes every token of its family, including the newest.
    assert after_replay.status_code == 401


@pytest.mark.req("FR-AUTH-008", "SEC-004")
async def test_tokens_for_other_audiences_issuers_or_keys_are_rejected() -> None:
    with respx.mock() as router:
        async with oauth_app() as oauth:
            tokens = await get_tokens(oauth, router)
            provider = oauth.provider
            claims = provider.codec.open(tokens["access_token"], typ="at+jwe")
            other_aud = provider.codec.seal(
                {**claims, "aud": "https://elsewhere/mcp"}, typ="at+jwe"
            )
            other_iss = provider.codec.seal({**claims, "iss": "https://elsewhere/"}, typ="at+jwe")
            expired = provider.codec.seal({**claims, "exp": claims["iat"] - 1}, typ="at+jwe")
            foreign = TokenCodec.from_spec(generate_key_spec("other")).seal(claims, typ="at+jwe")
            refresh_as_access = tokens["refresh_token"]
            assert await provider.load_access_token(tokens["access_token"]) is not None
            for token in (other_aud, other_iss, expired, foreign, refresh_as_access):
                assert await provider.load_access_token(token) is None
            body, headers = tools_call("get_fire_detections", DETECTIONS_ARGS, modern=False)
            response = await oauth.http.post(
                "/mcp", json=body, headers={**headers, "Authorization": f"Bearer {other_aud}"}
            )
    assert response.status_code == 401


# -- the connected key in use ---------------------------------------------------------------


@pytest.mark.req("FR-AUTH-003", "FR-AUTH-010", "SEC-001")
@pytest.mark.parametrize("mode", ["legacy", "auto"])
async def test_connected_key_reaches_firms_through_the_mcp_client(mode: str) -> None:
    with respx.mock() as router:
        area = router.get(LA_URL).respond(200, text=firms_csv.MODIS_NRT)
        # An operator key is configured and allowed, but a connected user's own key wins.
        async with oauth_app(map_key=OTHER_KEY, FIRMS_MCP_ALLOW_OPERATOR_KEY=True) as oauth:
            tokens = await get_tokens(oauth, router)

            def factory(**kwargs):
                kwargs.pop("verify", None)
                return httpx2.AsyncClient(
                    transport=httpx2.ASGITransport(app=oauth.app), base_url=BASE, **kwargs
                )

            transport = StreamableHttpTransport(
                f"{BASE}/mcp", auth=tokens["access_token"], httpx_client_factory=factory
            )
            async with Client(transport, mode=mode) as client:
                result = await client.call_tool("get_fire_detections", DETECTIONS_ARGS)
    assert result.structured_content["status"] == "success"
    assert area.call_count == 1  # the URL contains the connected key, not the operator's
    assert MAP_KEY not in json.dumps(result.structured_content)


@pytest.mark.req("FR-AUTH-007")
async def test_codes_and_pending_authorizations_expire() -> None:
    with respx.mock() as router:
        router.get(STATUS_URL, params={"MAP_KEY": MAP_KEY}).respond(
            200, json={"transaction_limit": 5000, "current_transactions": 0}
        )
        async with oauth_app() as oauth:
            await register(oauth)
            real_clock = oauth.provider.clock
            # A code minted "an hour ago" is past its five-minute lifetime.
            oauth.provider.clock = lambda: real_clock() - 3600
            _, submitted = await connect(oauth)
            oauth.provider.clock = real_clock
            code = parse_qs(urlsplit(submitted.headers["location"]).query)["code"][0]
            expired_code = await oauth.http.post(
                "/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": REDIRECT,
                    "client_id": oauth.client_id,
                    "code_verifier": oauth.verifier,
                },
            )
            # A pending authorization left open past its ten minutes cannot be completed.
            started = await start_authorization(oauth)
            oauth.provider.clock = lambda: real_clock() + 3600
            stale_page = await oauth.http.get(started.headers["location"])
    assert expired_code.status_code == 401 and expired_code.json()["error"] == "invalid_grant"
    assert stale_page.status_code == 400 and "expired" in stale_page.text


@pytest.mark.req("SEC-003")
async def test_connect_attempts_are_limited() -> None:
    async with oauth_app() as oauth:
        await register(oauth)
        started = await start_authorization(oauth)
        txn = parse_qs(urlsplit(started.headers["location"]).query)["txn"][0]
        page = await oauth.http.get(started.headers["location"])
        form = {"txn": txn, "csrf": csrf_from(page.text), "map_key": "bad"}
        statuses = [(await oauth.http.post("/connect", data=form)).status_code for _ in range(6)]
    assert statuses == [400, 400, 400, 400, 400, 429]


@pytest.mark.req("FR-AUTH-009")
async def test_revoking_a_refresh_token_revokes_its_family() -> None:
    with respx.mock() as router:
        async with oauth_app() as oauth:
            tokens = await get_tokens(oauth, router)
            revoked = await oauth.http.post(
                "/revoke",
                data={"token": tokens["refresh_token"], "client_id": oauth.client_id},
            )
            refresh = await oauth.http.post(
                "/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": tokens["refresh_token"],
                    "client_id": oauth.client_id,
                },
            )
    assert revoked.status_code == 200
    assert refresh.status_code == 401 and refresh.json()["error"] == "invalid_grant"


@pytest.mark.req("FR-AUTH-003")
async def test_tokens_without_the_data_scope_get_403() -> None:
    with respx.mock() as router:
        async with oauth_app() as oauth:
            tokens = await get_tokens(oauth, router)
            claims = oauth.provider.codec.open(tokens["access_token"], typ="at+jwe")
            no_scope = oauth.provider.codec.seal({**claims, "scope": ""}, typ="at+jwe")
            body, headers = tools_call("get_fire_detections", DETECTIONS_ARGS, modern=False)
            response = await oauth.http.post(
                "/mcp", json=body, headers={**headers, "Authorization": f"Bearer {no_scope}"}
            )
    assert response.status_code == 403
    assert 'error="insufficient_scope"' in response.headers["www-authenticate"]
