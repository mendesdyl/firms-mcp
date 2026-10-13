"""Documentation stays consistent with the code (DOC-002)."""

from __future__ import annotations

import re

import pytest

from firms_mcp.tools.loader import discover_tools
from tests.conftest import REPO_ROOT

TOOLS_DOC = REPO_ROOT / "docs" / "design" / "TOOLS.md"


def _sections(text: str) -> dict[str, str]:
    """Tool name -> body of its '### `name` (vX.Y.Z)' section."""
    sections: dict[str, str] = {}
    pattern = re.compile(r"^### `([a-z_]+)` \(v([0-9.]+)\)$", re.MULTILINE)
    matches = list(pattern.finditer(text))
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end() : end].split("\n## ", 1)[0]
        sections[match.group(1)] = f"v{match.group(2)}\n{body}"
    return sections


@pytest.mark.req("DOC-002")
def test_every_tool_is_documented_with_its_version_and_parameters() -> None:
    text = TOOLS_DOC.read_text(encoding="utf-8")
    sections = _sections(text)
    tools = discover_tools()
    assert sorted(sections) == sorted(t.manifest.name for t in tools)
    for tool in tools:
        name, version = tool.manifest.name, tool.manifest.version
        section = sections[name]
        assert section.startswith(f"v{version}\n"), f"{name}: documented version differs"
        assert f"| `{name}` | {version} |" in text, f"{name}: overview row missing or stale"
        for parameter in tool.input_model.model_fields:
            assert f"`{parameter}`" in section, f"{name}: parameter {parameter} not documented"
