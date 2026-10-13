"""Manifest loading and shared tool helpers (FR-MCP-001, FR-DATA-005)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from firms_mcp.tools.common import InvalidCursor, decode_cursor, encode_cursor
from firms_mcp.tools.loader import ToolManifest, discover_tools

EXPECTED_TOOLS = [
    "build_fire_map_link",
    "get_data_availability",
    "get_fire_data_sources",
    "get_fire_detections",
    "get_fire_footprint_kml_links",
    "get_knowledge_entry",
    "get_map_key_status",
    "list_knowledge_topics",
    "search_knowledge",
]
AUTH_TOOLS = {"get_fire_detections", "get_map_key_status"}


def valid_manifest(**overrides: object) -> dict:
    manifest = {
        "name": "example_tool",
        "version": "1.0.0",
        "title": "Example",
        "description": "An example tool description that is long enough to be useful.",
        "entry_function": "example_tool",
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    }
    manifest.update(overrides)
    return manifest


@pytest.mark.req("FR-MCP-001", "FR-AUTH-002")
def test_every_tool_directory_loads_with_its_models() -> None:
    tools = discover_tools()
    assert [t.manifest.name for t in tools] == EXPECTED_TOOLS
    for tool in tools:
        assert tool.manifest.enabled
        assert tool.manifest.examples, tool.manifest.name  # examples validated on load
        assert tool.manifest.require_auth is (tool.manifest.name in AUTH_TOOLS)
        assert "MAP_KEY" in tool.manifest.description, tool.manifest.name


@pytest.mark.req("FR-MCP-001", "NFR-003")
@pytest.mark.parametrize(
    "overrides",
    [
        {"version": "1.0"},  # not SemVer
        {"name": "Bad-Name"},
        {"description": "short"},
        {"annotations": {"readOnlyHint": True}},  # all four hints are required
        {"unexpected": True},
    ],
)
def test_invalid_manifests_are_rejected(overrides: dict) -> None:
    with pytest.raises(ValidationError):
        ToolManifest.model_validate(valid_manifest(**overrides))


@pytest.mark.req("FR-DATA-005")
def test_cursors_are_tool_scoped() -> None:
    cursor = encode_cursor("get_fire_detections", {"area": "world"}, 50, w="2026-10-10")
    payload = decode_cursor("get_fire_detections", cursor)
    assert payload["q"] == {"area": "world"} and payload["o"] == 50
    with pytest.raises(InvalidCursor, match="different tool"):
        decode_cursor("search_knowledge", cursor)
    with pytest.raises(InvalidCursor):
        decode_cursor("get_fire_detections", "%%%")
