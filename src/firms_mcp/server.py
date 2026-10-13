"""Assemble and run the FIRMS MCP server (ADR-0002, ADR-0003).

``create_server`` registers the manifest-defined tools, the resources, the prompts, and the
operational routes (``/health``, ``/.well-known/ard.json``) on a FastMCP 4 server, which
serves MCP 2026-07-28 clients and handshake-era clients from the same deployment.

Run it with::

    firms-mcp            # stdio (local use; FIRMS_MAP_KEY from the environment or .env)
    firms-mcp http       # Streamable HTTP at http://127.0.0.1:8000/mcp
"""

from __future__ import annotations

import argparse
import json
from functools import lru_cache
from importlib import resources

from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from firms_mcp import __version__
from firms_mcp.config import Settings
from firms_mcp.credentials import CredentialMode
from firms_mcp.instructions import SERVER_INSTRUCTIONS
from firms_mcp.logging_setup import configure_logging
from firms_mcp.prompts import register_prompts
from firms_mcp.resources import register_resources
from firms_mcp.services import Services, build_services
from firms_mcp.tools.loader import LoadedTool, register_tools

SERVER_NAME = "firms-mcp"
MCP_PATH = "/mcp"
LIST_CACHE_TTL_SECONDS = 3600
"""Tool, prompt, and resource lists and resource contents are static per server version."""


@lru_cache(maxsize=1)
def ard_document() -> dict:
    text = resources.files("firms_mcp").joinpath("discovery", "ard.json").read_text("utf-8")
    return json.loads(text)


def register_routes(mcp: FastMCP, services: Services, tools: list[LoadedTool]) -> None:
    """Operational HTTP routes (served by the Streamable HTTP app only)."""

    @mcp.custom_route("/health", methods=["GET"], include_in_schema=False)
    async def health(_: Request) -> JSONResponse:
        return JSONResponse(
            {
                "status": "ok",
                "server": SERVER_NAME,
                "version": __version__,
                "tools": len(tools),
                "knowledge_entries": len(services.knowledge),
            }
        )

    @mcp.custom_route("/.well-known/ard.json", methods=["GET"], include_in_schema=False)
    async def ard(_: Request) -> JSONResponse:
        response = JSONResponse(ard_document())
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response


def create_server(
    settings: Settings | None = None,
    *,
    services: Services | None = None,
    mode: CredentialMode = CredentialMode.LOCAL,
) -> FastMCP:
    services = services or build_services(settings, mode=mode)
    mcp = FastMCP(
        SERVER_NAME,
        instructions=SERVER_INSTRUCTIONS,
        version=__version__,
        on_duplicate="error",
        mask_error_details=True,
        cache_ttl=LIST_CACHE_TTL_SECONDS,
        cache_scope="public",
    )
    tools = register_tools(mcp, services)
    register_resources(mcp, services)
    register_prompts(mcp)
    register_routes(mcp, services, tools)
    return mcp


def create_http_app(mcp: FastMCP, *, middleware: list[Middleware] | None = None) -> Starlette:
    """The Streamable HTTP application, with the MCP endpoint at ``/mcp``."""
    return mcp.http_app(path=MCP_PATH, middleware=middleware)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="firms-mcp", description="MCP server for NASA FIRMS (independent project)"
    )
    parser.add_argument(
        "transport",
        nargs="?",
        choices=("stdio", "http"),
        default="stdio",
        help="stdio for local clients (default) or http for Streamable HTTP",
    )
    parser.add_argument("--host", help="HTTP bind address (default FIRMS_MCP_HOST or 127.0.0.1)")
    parser.add_argument("--port", type=int, help="HTTP port (default FIRMS_MCP_PORT or 8000)")
    args = parser.parse_args(argv)

    settings = Settings()
    configure_logging(settings.log_level)
    if args.transport == "stdio":
        create_server(settings, mode=CredentialMode.LOCAL).run(transport="stdio", show_banner=False)
        return

    import uvicorn

    app = create_http_app(create_server(settings, mode=CredentialMode.REMOTE))
    uvicorn.run(
        app,
        host=args.host or settings.host,
        port=args.port or settings.port,
        log_config=None,
    )


if __name__ == "__main__":  # pragma: no cover
    main()
