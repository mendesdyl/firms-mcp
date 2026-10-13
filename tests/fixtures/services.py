"""Server test helpers: settings, services with a mocked FIRMS host, and MCP clients.

FIRMS is reached at ``https://firms.test`` and mocked with respx in each test; the clock is
fixed at 2026-10-10 12:00 UTC so date windows and map links are deterministic.
"""

from __future__ import annotations

import contextlib
import datetime as dt
from collections.abc import AsyncIterator
from functools import lru_cache

import httpx2
from fastmcp import Client, FastMCP
from fastmcp.client.transports import StreamableHttpTransport

from firms_mcp.config import Settings
from firms_mcp.credentials import CredentialMode, MapKeyResolver
from firms_mcp.firms.client import FirmsClient
from firms_mcp.knowledge import KnowledgeBase, load_knowledge_base
from firms_mcp.server import MCP_PATH, create_http_app, create_server
from firms_mcp.services import Services

FIRMS_BASE = "https://firms.test"
NOW = dt.datetime(2026, 10, 10, 12, 0, tzinfo=dt.UTC)
TODAY = NOW.date()

# Connect-time modes of the FastMCP client and the protocol revision each negotiates.
ERAS = {"legacy": "2025-11-25", "auto": "2026-07-28"}


@lru_cache(maxsize=1)
def repo_knowledge() -> KnowledgeBase:
    return load_knowledge_base()


def make_settings(**overrides: object) -> Settings:
    values = {"FIRMS_API_BASE_URL": FIRMS_BASE, "FIRMS_MCP_RETRY_BACKOFF": 0, **overrides}
    return Settings(_env_file=None, **values)


async def _no_sleep(_: float) -> None:
    return None


def make_services(
    *,
    map_key: str | None = None,
    mode: CredentialMode = CredentialMode.LOCAL,
    knowledge: KnowledgeBase | None = None,
    now: dt.datetime = NOW,
    **settings: object,
) -> Services:
    if map_key is not None:
        settings["FIRMS_MAP_KEY"] = map_key
    resolved = make_settings(**settings)
    return Services(
        settings=resolved,
        knowledge=knowledge or repo_knowledge(),
        firms=FirmsClient(resolved, sleep=_no_sleep),
        credentials=MapKeyResolver(resolved, mode),
        clock=lambda: now,
    )


def make_server(services: Services | None = None, **kwargs: object) -> FastMCP:
    return create_server(services=services or make_services(**kwargs))


@contextlib.asynccontextmanager
async def http_client(mcp: FastMCP, mode: str) -> AsyncIterator[tuple[Client, list[dict]]]:
    """An MCP client talking Streamable HTTP to the app in-process (no sockets).

    Yields the client and a list that collects each HTTP request's method, path, and
    ``mcp-*`` headers.
    """
    app = create_http_app(mcp)
    seen: list[dict] = []

    async def recording_app(scope, receive, send):
        if scope["type"] == "http":
            headers = {k.decode().lower(): v.decode() for k, v in scope["headers"]}
            seen.append(
                {
                    "method": scope["method"],
                    "path": scope["path"],
                    "headers": {k: v for k, v in headers.items() if k.startswith("mcp-")},
                }
            )
        await app(scope, receive, send)

    def factory(**kwargs):
        kwargs.pop("verify", None)
        return httpx2.AsyncClient(
            transport=httpx2.ASGITransport(app=recording_app),
            base_url="http://testserver",
            **kwargs,
        )

    async with app.router.lifespan_context(app):
        transport = StreamableHttpTransport(
            f"http://testserver{MCP_PATH}", httpx_client_factory=factory
        )
        async with Client(transport, mode=mode) as client:
            yield client, seen


@contextlib.asynccontextmanager
async def raw_http(mcp: FastMCP) -> AsyncIterator[httpx2.AsyncClient]:
    """A plain HTTP client for the app in-process, for operational routes and raw MCP."""
    app = create_http_app(mcp)
    async with (
        app.router.lifespan_context(app),
        httpx2.AsyncClient(
            transport=httpx2.ASGITransport(app=app), base_url="http://testserver"
        ) as client,
    ):
        yield client
