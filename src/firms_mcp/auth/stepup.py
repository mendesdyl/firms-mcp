"""Per-tool step-up authentication at the HTTP layer (ADR-0004 §4; FR-AUTH-003).

Follows the NASA Earthdata MCP's ``util/stepup.py``: anonymous requests reach every tool
whose manifest does not set ``require_auth``; a call to one that does, without a valid
token carrying the ``firms:data`` scope, is answered with HTTP 401 (or 403 for a missing
scope) and a ``WWW-Authenticate`` challenge naming the protected resource metadata, which
starts the client's OAuth flow. This runs before the MCP transport, the only place an
HTTP status can still be chosen.

Which tool is called:

* **2026-07-28 requests** (a modern ``MCP-Protocol-Version`` header) name the method and
  tool in the standard ``Mcp-Method`` and ``Mcp-Name`` headers. The MCP SDK routes on the
  same header and rejects any request whose headers disagree with its body, so the
  headers are used without reading the body.
* **Handshake-era requests** carry the tool name only in the JSON-RPC body (a single
  message or a batch), which is buffered, read, and replayed to the application.

The tools enforce the key again themselves (defense in depth).

ASGI stack, outermost first::

    AuthenticationMiddleware(BearerAuthBackend)  token → scope["user"] (never rejects)
    AuthContextMiddleware                        token visible to tool code
    StepUpAuth (this module)                     challenge for protected tools
    Streamable HTTP MCP endpoint
"""

from __future__ import annotations

import json
from collections.abc import Iterable

from fastmcp.server.auth.middleware import RequireAuthMiddleware
from mcp.shared.inbound import MCP_METHOD_HEADER, MCP_NAME_HEADER, decode_header_value
from mcp_types.version import HANDSHAKE_PROTOCOL_VERSIONS
from pydantic import AnyHttpUrl
from starlette.types import ASGIApp, Message, Receive, Scope, Send

PROTOCOL_VERSION_HEADER = "mcp-protocol-version"


class StepUpAuth:
    def __init__(
        self,
        app: ASGIApp,
        *,
        protected_tools: Iterable[str],
        mcp_path: str,
        resource_metadata_url: AnyHttpUrl,
        required_scopes: list[str],
    ) -> None:
        self.app = app
        self.protected_tools = frozenset(protected_tools)
        self.mcp_path = mcp_path.rstrip("/")
        self.gate = RequireAuthMiddleware(
            app, required_scopes=required_scopes, resource_metadata_url=resource_metadata_url
        )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (
            scope["type"] != "http"
            or scope["method"] != "POST"
            or scope["path"].rstrip("/") != self.mcp_path
        ):
            await self.app(scope, receive, send)
            return
        headers = {k.decode("latin-1").lower(): v.decode("latin-1") for k, v in scope["headers"]}
        version = headers.get(PROTOCOL_VERSION_HEADER)
        if version is not None and version not in HANDSHAKE_PROTOCOL_VERSIONS:
            called = (
                {decode_header_value(headers.get(MCP_NAME_HEADER))}
                if headers.get(MCP_METHOD_HEADER) == "tools/call"
                else set()
            )
        else:
            body, receive = await _buffer_body(receive)
            called = called_tools(body)
        if called & self.protected_tools:
            await self.gate(scope, receive, send)  # passes through when the token suffices
        else:
            await self.app(scope, receive, send)


async def _buffer_body(receive: Receive) -> tuple[bytes, Receive]:
    """Read the whole request body, and return a receive() that replays it."""
    chunks: list[bytes] = []
    more = True
    while more:
        message = await receive()
        if message["type"] != "http.request":
            break
        chunks.append(message.get("body", b""))
        more = message.get("more_body", False)
    body = b"".join(chunks)
    replayed = False

    async def replay() -> Message:
        nonlocal replayed
        if replayed:
            return await receive()
        replayed = True
        return {"type": "http.request", "body": body, "more_body": False}

    return body, replay


def called_tools(body: bytes) -> set[str | None]:
    """Names of the tools a JSON-RPC message or batch calls."""
    try:
        parsed = json.loads(body)
    except (ValueError, UnicodeDecodeError):
        return set()
    messages = parsed if isinstance(parsed, list) else [parsed]
    names: set[str | None] = set()
    for message in messages:
        if isinstance(message, dict) and message.get("method") == "tools/call":
            params = message.get("params")
            names.add(params.get("name") if isinstance(params, dict) else None)
    return names
