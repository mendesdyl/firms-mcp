"""Transports and operational endpoints (FR-MCP-004, FR-MCP-006, FR-MCP-007).

Streamable HTTP runs in-process through the ASGI app (no sockets); stdio starts the real
``python -m firms_mcp`` process.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx2
import pytest
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

from firms_mcp import __version__
from tests.fixtures.services import ERAS, http_client, make_server, raw_http, repo_knowledge


def _first_message(response) -> dict:
    """The first JSON-RPC message of a Streamable HTTP response (JSON or an SSE stream)."""
    if response.headers["content-type"].startswith("text/event-stream"):
        for line in response.text.splitlines():
            if line.startswith("data:"):
                return json.loads(line.removeprefix("data:").strip())
        raise AssertionError("no data in the event stream")
    return response.json()


@pytest.mark.req("FR-MCP-006", "FR-MCP-007")
@pytest.mark.parametrize("mode", list(ERAS))
async def test_streamable_http_in_both_eras(mode: str) -> None:
    async with http_client(make_server(), mode) as (client, seen):
        assert client.protocol_version == ERAS[mode]
        tools = await client.list_tools()
        assert len(tools) == 9
        result = await client.call_tool(
            "get_knowledge_entry", {"entry_ids": ["faq.getting-started.what-is-utc"]}
        )
        assert result.structured_content["entries"][0]["title"] == "What is UTC?"
    assert all(request["path"] == "/mcp" for request in seen)
    calls = [r for r in seen if r["headers"].get("mcp-method") == "tools/call"]
    if ERAS[mode] == "2026-07-28":
        # Stateless requests that name the method and tool in standard headers (used by the
        # per-tool step-up of ADR-0004), and no session.
        assert calls and calls[0]["headers"]["mcp-name"] == "get_knowledge_entry"
        assert not any("mcp-session-id" in r["headers"] for r in seen)
    else:
        assert any("mcp-session-id" in r["headers"] for r in seen)


@pytest.mark.req("FR-MCP-007")
async def test_older_handshake_revision_is_accepted() -> None:
    """A client on the 2025-06-18 revision completes the initialize handshake."""
    async with raw_http(make_server()) as http:
        response = await http.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "old-client", "version": "1.0"},
                },
            },
            headers={"Accept": "application/json, text/event-stream"},
        )
    assert response.status_code == 200
    payload = _first_message(response)
    assert payload["result"]["protocolVersion"] == "2025-06-18"
    assert payload["result"]["serverInfo"]["name"] == "firms-mcp"
    assert payload["result"]["instructions"].startswith("This server connects you to NASA")


@pytest.mark.req("FR-MCP-004")
async def test_health_endpoint() -> None:
    async with raw_http(make_server()) as http:
        response = await http.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "server": "firms-mcp",
        "version": __version__,
        "tools": 9,
        "knowledge_entries": len(repo_knowledge()),
    }


@pytest.mark.req("FR-MCP-004")
async def test_ard_discovery_document_matches_the_server() -> None:
    server = make_server()
    async with raw_http(server) as http:
        response = await http.get("/.well-known/ard.json")
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"
    entry = response.json()["entries"][0]
    async with Client(server) as client:
        tools = sorted(t.name for t in await client.list_tools())
    assert entry["capabilities"] == tools
    assert entry["type"] == "application/mcp-server+json"
    assert "Not an official NASA service" in entry["description"]
    assert len(entry["representativeQueries"]) >= 5


@pytest.mark.req("FR-MCP-006")
async def test_stdio_transport_runs_the_installed_entry_point(tmp_path: Path) -> None:
    transport = StdioTransport(
        command=sys.executable,
        args=["-m", "firms_mcp"],
        env={"FIRMS_MAP_KEY": "", "FIRMS_MCP_LOG_LEVEL": "WARNING"},
        cwd=str(tmp_path),  # no .env here
        keep_alive=False,
    )
    async with Client(transport) as client:
        tools = await client.list_tools()
        assert len(tools) == 9
        result = await client.call_tool("search_knowledge", {"query": "what is UTC", "limit": 1})
        assert result.structured_content["results"][0]["id"] == "faq.getting-started.what-is-utc"
        missing_key = await client.call_tool(
            "get_fire_detections", {"area": "world"}, raise_on_error=False
        )
        assert missing_key.structured_content["error_code"] == "auth_required"


@pytest.mark.req("FR-MCP-006", "FR-AUTH-004")
async def test_http_command_serves_metadata_for_its_own_address(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import uvicorn

    import firms_mcp.server as server_module

    captured: dict = {}
    monkeypatch.chdir(tmp_path)  # no .env
    monkeypatch.setattr(server_module, "configure_logging", lambda level: None)
    monkeypatch.setattr(uvicorn, "run", lambda app, **kwargs: captured.update(app=app, **kwargs))
    server_module.main(["http", "--port", "9123"])
    assert (captured["host"], captured["port"]) == ("127.0.0.1", 9123)
    async with httpx2.AsyncClient(
        transport=httpx2.ASGITransport(app=captured["app"]), base_url="http://127.0.0.1:9123"
    ) as http:
        metadata = (await http.get("/.well-known/oauth-protected-resource/mcp")).json()
    assert metadata["resource"] == "http://127.0.0.1:9123/mcp"
