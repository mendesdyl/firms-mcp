"""Per-tool step-up at the HTTP layer (FR-AUTH-003; ADR-0004 §4; integration issue II-06)."""

from __future__ import annotations

import json

import pytest
from pydantic import AnyHttpUrl

from firms_mcp.auth.stepup import StepUpAuth, called_tools

METADATA = AnyHttpUrl("https://testserver/.well-known/oauth-protected-resource/mcp")


class Downstream:
    def __init__(self) -> None:
        self.bodies: list[bytes] = []

    async def __call__(self, scope, receive, send) -> None:
        message = await receive()
        self.bodies.append(message.get("body", b""))
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})


async def run(middleware: StepUpAuth, headers: dict[str, str], body: bytes) -> int:
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/mcp",
        "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
    }
    sent: list[dict] = []
    delivered = False

    async def receive():
        nonlocal delivered
        if delivered:
            return {"type": "http.disconnect"}
        delivered = True
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message):
        sent.append(message)

    await middleware(scope, receive, send)
    return sent[0]["status"]


def stepup(downstream: Downstream) -> StepUpAuth:
    return StepUpAuth(
        downstream,
        protected_tools={"get_fire_detections"},
        mcp_path="/mcp",
        resource_metadata_url=METADATA,
        required_scopes=["firms:data"],
    )


def call(name: str) -> dict:
    return {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name}}


@pytest.mark.req("FR-AUTH-003")
async def test_modern_requests_are_decided_from_the_headers_alone() -> None:
    downstream = Downstream()
    modern = {"MCP-Protocol-Version": "2026-07-28", "Mcp-Method": "tools/call"}
    # The body is not even JSON: the decision comes from Mcp-Name.
    assert await run(stepup(downstream), {**modern, "Mcp-Name": "get_fire_detections"}, b"?") == 401
    assert await run(stepup(downstream), {**modern, "Mcp-Name": "search_knowledge"}, b"?") == 200
    assert downstream.bodies == [b"?"]  # passed through unread


@pytest.mark.req("FR-AUTH-003")
async def test_handshake_era_requests_are_decided_from_the_body_and_replayed() -> None:
    downstream = Downstream()
    legacy = {"MCP-Protocol-Version": "2025-11-25"}
    protected = json.dumps([call("search_knowledge"), call("get_fire_detections")]).encode()
    anonymous = json.dumps(call("search_knowledge")).encode()
    assert await run(stepup(downstream), legacy, protected) == 401  # batch containing one
    assert await run(stepup(downstream), {}, anonymous) == 200  # no version header at all
    assert downstream.bodies == [anonymous]  # the buffered body is replayed intact


def test_called_tools_parses_messages_and_batches() -> None:
    assert called_tools(json.dumps(call("a")).encode()) == {"a"}
    assert called_tools(json.dumps([call("a"), {"method": "tools/list"}]).encode()) == {"a"}
    assert called_tools(b"not json") == set()
