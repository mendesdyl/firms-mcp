"""MCP Registry metadata (FR-MCP-005; ADR-0002, ADR-0010)."""

from __future__ import annotations

import json
import re
import tomllib

import pytest

from tests.conftest import REPO_ROOT

NAME_PATTERN = re.compile(r"^[a-zA-Z0-9.-]+/[a-zA-Z0-9._-]+$")  # reverse-DNS namespace / name


@pytest.mark.req("FR-MCP-005")
def test_server_json_matches_the_package() -> None:
    server = json.loads((REPO_ROOT / "server.json").read_text(encoding="utf-8"))
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    assert NAME_PATTERN.match(server["name"])
    assert server["name"].endswith("/firms-mcp")
    assert server["version"] == project["version"]
    assert len(server["description"]) <= 100  # registry limit
    assert "independent" in server["description"]
    (package,) = server["packages"]
    assert package["registryType"] == "pypi"
    assert package["identifier"] == project["name"]
    assert package["version"] == project["version"]
    assert package["transport"] == {"type": "stdio"}
    (variable,) = package["environmentVariables"]
    assert variable["name"] == "FIRMS_MAP_KEY"
    assert variable["isSecret"] is True and variable["isRequired"] is False


@pytest.mark.req("FR-MCP-005")
def test_readme_carries_the_registry_name_for_pypi_verification() -> None:
    server = json.loads((REPO_ROOT / "server.json").read_text(encoding="utf-8"))
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert f"mcp-name: {server['name']}" in readme
