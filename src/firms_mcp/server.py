"""Assemble and run the FIRMS MCP server (ADR-0002, ADR-0003).

``create_server`` registers the manifest-defined tools, the resources, the prompts, and the
operational routes (``/health``, ``/.well-known/ard.json``) on a FastMCP 4 server, which
serves MCP 2026-07-28 clients and handshake-era clients from the same deployment.

Run it with::

    firms-mcp            # stdio (local use; FIRMS_MAP_KEY from the environment or .env)
    firms-mcp http       # Streamable HTTP at http://127.0.0.1:8000/mcp, with the MAP_KEY
                         # connect flow (FIRMS_MCP_AUTH=oauth, the default)
    firms-mcp keygen     # print a new FIRMS_MCP_TOKEN_KEYS entry
"""

from __future__ import annotations

import argparse
import json
import logging
from functools import lru_cache
from importlib import resources

from fastmcp import FastMCP
from key_value.aio.protocols import AsyncKeyValue
from mcp.server.auth.routes import build_resource_metadata_url
from pydantic import AnyHttpUrl
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from firms_mcp import __version__
from firms_mcp.auth.provider import SCOPE, FirmsOAuthProvider
from firms_mcp.auth.stepup import StepUpAuth
from firms_mcp.auth.tokens import TokenCodec, generate_key_spec
from firms_mcp.config import Settings
from firms_mcp.credentials import CredentialMode
from firms_mcp.instructions import SERVER_INSTRUCTIONS
from firms_mcp.logging_setup import configure_logging
from firms_mcp.prompts import register_prompts
from firms_mcp.resources import register_resources
from firms_mcp.services import Services, build_services
from firms_mcp.tools.loader import LoadedTool, discover_tools, register_tools

logger = logging.getLogger(__name__)

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


def create_auth_provider(
    services: Services, *, store: AsyncKeyValue | None = None
) -> FirmsOAuthProvider:
    """The MAP_KEY connect flow's authorization server for this deployment (ADR-0004)."""
    settings = services.settings
    keys = settings.token_keys.get_secret_value() if settings.token_keys else None
    return FirmsOAuthProvider(
        base_url=settings.effective_public_url,
        codec=TokenCodec.from_spec(keys),
        firms=services.firms,
        mcp_path=MCP_PATH,
        store=store,
        access_token_ttl=settings.access_token_ttl_seconds,
        refresh_token_ttl=settings.refresh_token_ttl_seconds,
        enable_dcr=settings.enable_dcr,
        enable_cimd=settings.enable_cimd,
    )


def protected_tool_names() -> set[str]:
    """Tools whose manifests require the user's MAP_KEY (ADR-0004 §4)."""
    return {
        tool.manifest.name
        for tool in discover_tools()
        if tool.manifest.enabled and tool.manifest.require_auth
    }


def create_http_app(
    mcp: FastMCP,
    *,
    auth: FirmsOAuthProvider | None = None,
    middleware: list[Middleware] | None = None,
) -> Starlette:
    """The Streamable HTTP application, with the MCP endpoint at ``/mcp``.

    With ``auth``, bearer tokens are parsed on every request (never rejected there), calls
    to protected tools without a sufficient token get a 401/403 challenge (step-up), and
    the authorization server's routes are added (metadata, registration, authorize,
    connect, token, revoke, protected resource metadata).
    """
    stack = list(middleware or [])
    if auth is not None:
        stack = [
            *auth.get_middleware(),
            Middleware(
                StepUpAuth,  # type: ignore[arg-type]
                protected_tools=protected_tool_names(),
                mcp_path=MCP_PATH,
                resource_metadata_url=build_resource_metadata_url(AnyHttpUrl(auth.resource)),
                required_scopes=[SCOPE],
            ),
            *stack,
        ]
    app = mcp.http_app(path=MCP_PATH, middleware=stack)
    if auth is not None:
        app.routes.extend(auth.get_routes(MCP_PATH))
    return app


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="firms-mcp", description="MCP server for NASA FIRMS (independent project)"
    )
    parser.add_argument(
        "transport",
        nargs="?",
        choices=("stdio", "http", "keygen"),
        default="stdio",
        help=(
            "stdio for local clients (default), http for Streamable HTTP, or keygen to print a "
            "new FIRMS_MCP_TOKEN_KEYS entry"
        ),
    )
    parser.add_argument("--host", help="HTTP bind address (default FIRMS_MCP_HOST or 127.0.0.1)")
    parser.add_argument("--port", type=int, help="HTTP port (default FIRMS_MCP_PORT or 8000)")
    args = parser.parse_args(argv)
    if args.transport == "keygen":
        print(generate_key_spec())
        return

    settings = Settings()
    overrides = {"host": args.host, "port": args.port}
    settings = settings.model_copy(update={k: v for k, v in overrides.items() if v is not None})
    configure_logging(settings.log_level)
    if args.transport == "stdio":
        create_server(settings, mode=CredentialMode.LOCAL).run(transport="stdio", show_banner=False)
        return

    import uvicorn

    if settings.public_url is None and settings.host not in ("127.0.0.1", "localhost", "::1"):
        logger.warning(
            "FIRMS_MCP_PUBLIC_URL is not set; OAuth metadata will advertise %s, which clients "
            "outside this machine cannot reach",
            settings.effective_public_url,
        )
    services = build_services(settings, mode=CredentialMode.REMOTE)
    auth = create_auth_provider(services) if settings.auth_mode == "oauth" else None
    app = create_http_app(create_server(services=services), auth=auth)
    uvicorn.run(app, host=settings.host, port=settings.port, log_config=None)


if __name__ == "__main__":  # pragma: no cover
    main()
