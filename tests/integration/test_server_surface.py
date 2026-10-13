"""The assembled server through the MCP client, in both protocol eras (ADR-0003, ADR-0008).

``legacy`` pins the initialize handshake (2025-11-25); ``auto`` negotiates 2026-07-28
through ``server/discover``.
"""

from __future__ import annotations

import json

import pytest
from fastmcp import Client

from firms_mcp.instructions import SERVER_INSTRUCTIONS
from firms_mcp.tools.loader import discover_tools
from tests.fixtures.services import ERAS, make_server, repo_knowledge

pytestmark = pytest.mark.parametrize("mode", list(ERAS))

ANNOTATION_HINTS = ("readOnlyHint", "destructiveHint", "idempotentHint", "openWorldHint")
SECRET_NAMES = ("key", "token", "secret", "password", "credential", "auth")


def _property_names(schema: object) -> set[str]:
    """Every property name anywhere in a JSON schema."""
    names: set[str] = set()
    if isinstance(schema, dict):
        for name, value in schema.items():
            if name == "properties" and isinstance(value, dict):
                names.update(value)
            names |= _property_names(value)
    elif isinstance(schema, list):
        for item in schema:
            names |= _property_names(item)
    return names


@pytest.mark.req("FR-MCP-007")
async def test_both_protocol_eras_negotiate(mode: str) -> None:
    async with Client(make_server(), mode=mode) as client:
        assert client.protocol_version == ERAS[mode]


@pytest.mark.req("FR-MCP-001", "NFR-002", "NFR-003", "FR-MCP-007")
async def test_tools_come_from_their_manifests(mode: str) -> None:
    loaded = {t.manifest.name: t for t in discover_tools()}
    async with Client(make_server(), mode=mode) as client:
        tools = await client.list_tools()
    assert {t.name for t in tools} == set(loaded)
    for tool in tools:
        manifest = loaded[tool.name].manifest
        assert tool.description == manifest.description
        assert tool.title == manifest.title
        assert tool.meta["fastmcp"]["version"] == manifest.version
        assert tool.meta["firms_mcp"]["require_auth"] is manifest.require_auth
        # NFR-002: every tool declares an output schema (structured content is checked below).
        assert tool.output_schema and tool.output_schema["type"] == "object"
        assert "status" in tool.output_schema["properties"]
        # NFR-003: title and all four behaviour hints.
        annotations = tool.annotations.model_dump(by_alias=True)
        for hint in ANNOTATION_HINTS:
            assert isinstance(annotations[hint], bool), (tool.name, hint)
        assert annotations["readOnlyHint"] is True
        assert annotations["destructiveHint"] is False
        assert annotations["title"] == manifest.title
        # Input schemas are the models the code validates with; unknown arguments rejected.
        assert tool.input_schema.get("additionalProperties") is False


@pytest.mark.req("FR-MCP-008")
async def test_tool_order_is_deterministic(mode: str) -> None:
    server = make_server()
    async with Client(server, mode=mode) as client:
        first = [t.name for t in await client.list_tools()]
        second = [t.name for t in await client.list_tools()]
    assert first == second == sorted(first)


@pytest.mark.req("SEC-002")
async def test_no_tool_accepts_a_key_as_a_parameter(mode: str) -> None:
    async with Client(make_server(), mode=mode) as client:
        tools = await client.list_tools()
    for tool in tools:
        names = {n.lower() for n in _property_names(tool.input_schema)}
        offending = sorted(n for n in names if any(s in n for s in SECRET_NAMES))
        assert not offending, f"{tool.name} accepts {offending}"


@pytest.mark.req("FR-MCP-002")
async def test_instructions_reach_clients_in_both_eras(mode: str) -> None:
    async with Client(make_server(), mode=mode) as client:
        assert client.instructions == SERVER_INSTRUCTIONS
    text = SERVER_INSTRUCTIONS
    assert "ORIENT → RETRIEVE → CONTEXTUALIZE → LINK" in text
    assert "Do not use for the preservation of life or property" in text  # FIRMS's disclaimer
    assert "UTC" in text
    assert "does not answer science questions" in text
    assert "NEVER ask the user to type or paste a key" in text
    assert "NEVER add" in text  # no summing across sources


@pytest.mark.req("FR-AUTH-002", "NFR-002")
async def test_tools_that_need_no_key_work_anonymously(mode: str) -> None:
    calls = {
        "search_knowledge": {"query": "what is UTC", "limit": 1},
        "get_knowledge_entry": {"entry_ids": ["faq.getting-started.what-is-utc"]},
        "list_knowledge_topics": {},
        "get_fire_data_sources": {},
        "build_fire_map_link": {"center": {"longitude": -116.2, "latitude": 43.6}, "zoom": 8},
        "get_fire_footprint_kml_links": {"region": "canada"},
    }
    async with Client(make_server(), mode=mode) as client:  # no MAP_KEY anywhere
        for name, arguments in calls.items():
            result = await client.call_tool(name, arguments)
            assert result.is_error is False, name
            assert result.structured_content["status"] == "success", name
            # The text content is the same JSON as the structured content.
            assert json.loads(result.content[0].text) == result.structured_content


@pytest.mark.req("FR-DATA-002")
async def test_invalid_arguments_return_structured_errors(mode: str) -> None:
    async with Client(make_server(), mode=mode) as client:
        result = await client.call_tool(
            "build_fire_map_link", {"zoom": 30, "bogus": 1}, raise_on_error=False
        )
    assert result.is_error is True
    content = result.structured_content
    assert content["status"] == "error" and content["error_code"] == "invalid_request"
    assert "zoom" in content["error_message"] and "bogus" in content["error_message"]


@pytest.mark.req("FR-MCP-003")
async def test_prompts_render_guided_workflows(mode: str) -> None:
    async with Client(make_server(), mode=mode) as client:
        prompts = {p.name: p for p in await client.list_prompts()}
        assert set(prompts) == {"investigate_fire_activity", "explain_detection"}
        rendered = await client.get_prompt(
            "investigate_fire_activity", {"place": "Boise, Idaho", "days": 2}
        )
        text = rendered.messages[0].content.text
        assert "Boise, Idaho" in text and "get_fire_detections" in text
        assert "day_range 2" in text and "local emergency services" in text
        explained = await client.get_prompt("explain_detection", {"detection": "frp_mw 12.5"})
        assert "frp_mw 12.5" in explained.messages[0].content.text


@pytest.mark.req("FR-KB-010", "FR-KB-001")
async def test_knowledge_and_sources_resources(mode: str) -> None:
    knowledge = repo_knowledge()
    entry = knowledge.get("faq.getting-started.what-does-a-fire-detection-mean-on-the-ground")
    async with Client(make_server(), mode=mode) as client:
        listed = {str(r.uri) for r in await client.list_resources()}
        templates = {t.uri_template for t in await client.list_resource_templates()}
        assert listed == {"firms://knowledge/index", "firms://sources"}
        assert templates == {"firms://knowledge/{entry_id}"}

        index = json.loads((await client.read_resource("firms://knowledge/index"))[0].text)
        assert sum(len(s["entries"]) for s in index["sections"]) == len(knowledge.ordered())

        page = (await client.read_resource(f"firms://knowledge/{entry.id}"))[0]
        assert page.mime_type == "text/markdown"
        assert entry.body in page.text  # verbatim
        assert entry.source_url in page.text

        sources = json.loads((await client.read_resource("firms://sources"))[0].text)
        assert len(sources["sources"]) == 8

        with pytest.raises(Exception, match="No knowledge entry"):
            await client.read_resource("firms://knowledge/faq.getting-started.what-is-gmt")
