"""Register MCP tools from per-tool ``manifest.json`` files (ADR-0002; FR-MCP-001).

Each tool lives in ``firms_mcp/tools/<name>/``:

* ``manifest.json`` — name, SemVer version, title, LLM-facing description, tags, the four
  behaviour annotations, ``require_auth``, ``enabled``, ``entry_function``, and examples;
* ``models.py`` — a Pydantic input model (unknown arguments rejected) and an output model
  derived from ``ToolOutput``;
* ``tool.py`` — the async entry function ``(params: <Input>, services: Services) -> <Output>``.

The loader reads the input and output models from the entry function's type hints, so
the JSON schemas published to clients are exactly the models the code validates with.
Invalid manifests stop the server (fail fast, as the Earthdata MCP loader does). Tools are
registered in name order so ``tools/list`` is deterministic (FR-MCP-008).
"""

from __future__ import annotations

import importlib
import inspect
import json
import logging
import typing
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from importlib import resources
from typing import Any

from fastmcp import FastMCP
from fastmcp.tools.base import Tool, ToolResult
from mcp_types import TextContent, ToolAnnotations
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from firms_mcp.firms.errors import FirmsError
from firms_mcp.services import Services
from firms_mcp.tools.common import ToolOutput

logger = logging.getLogger(__name__)

TOOLS_PACKAGE = "firms_mcp.tools"
SEMVER = r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$"

EntryFunction = Callable[[BaseModel, Services], Awaitable[ToolOutput]]


class ManifestError(ValueError):
    """A tool directory is invalid; the message names the tool and the problem."""


class ManifestAnnotations(BaseModel):
    """All four behaviour hints are required (NFR-003). Field names are MCP's own."""

    model_config = ConfigDict(extra="forbid")

    readOnlyHint: bool
    destructiveHint: bool
    idempotentHint: bool
    openWorldHint: bool


class ManifestExample(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str
    params: dict[str, Any]


class ToolManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    version: str = Field(pattern=SEMVER)
    title: str = Field(min_length=3)
    description: str = Field(min_length=40)
    entry_function: str
    tags: list[str] = Field(default_factory=list)
    annotations: ManifestAnnotations
    require_auth: bool = False
    enabled: bool = True
    examples: dict[str, ManifestExample] = Field(default_factory=dict)


@dataclass(frozen=True)
class LoadedTool:
    manifest: ToolManifest
    entry: EntryFunction
    input_model: type[BaseModel]
    output_model: type[ToolOutput]


def _tool_directories() -> list[str]:
    root = resources.files(TOOLS_PACKAGE)
    return sorted(
        item.name
        for item in root.iterdir()
        if item.is_dir() and item.joinpath("manifest.json").is_file()
    )


def load_tool(directory: str) -> LoadedTool:
    """Load and check one tool directory; raise ManifestError on any problem."""
    where = f"tool directory {directory!r}"
    try:
        raw = json.loads(
            resources.files(TOOLS_PACKAGE).joinpath(directory, "manifest.json").read_text("utf-8")
        )
        manifest = ToolManifest.model_validate(raw)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        raise ManifestError(f"{where}: invalid manifest.json: {exc}") from exc
    if manifest.name != directory:
        raise ManifestError(f"{where}: manifest name {manifest.name!r} must match the directory")

    module = importlib.import_module(f"{TOOLS_PACKAGE}.{directory}.tool")
    entry = getattr(module, manifest.entry_function, None)
    if entry is None or not inspect.iscoroutinefunction(entry):
        raise ManifestError(f"{where}: tool.py has no async function {manifest.entry_function!r}")
    hints = typing.get_type_hints(entry)
    input_model = hints.get("params")
    output_model = hints.get("return")
    if not (inspect.isclass(input_model) and issubclass(input_model, BaseModel)):
        raise ManifestError(f"{where}: the entry function needs a 'params: <InputModel>' argument")
    if input_model.model_config.get("extra") != "forbid":
        raise ManifestError(f"{where}: the input model must reject unknown arguments")
    if not (inspect.isclass(output_model) and issubclass(output_model, ToolOutput)):
        raise ManifestError(f"{where}: the entry function must return a ToolOutput subclass")
    for name, example in manifest.examples.items():
        try:
            input_model.model_validate(example.params)
        except ValidationError as exc:
            raise ManifestError(f"{where}: example {name!r} is not valid input: {exc}") from exc
    return LoadedTool(manifest, entry, input_model, output_model)


def discover_tools() -> list[LoadedTool]:
    """Every tool directory, in name order (disabled tools included)."""
    return [load_tool(directory) for directory in _tool_directories()]


def describe_validation_error(exc: ValidationError) -> str:
    parts = []
    for error in exc.errors(include_url=False):
        location = ".".join(str(p) for p in error["loc"]) or "arguments"
        parts.append(f"{location}: {error['msg']}")
    return "Invalid arguments — " + "; ".join(parts)


class ManifestTool(Tool):
    """A FastMCP tool whose interface comes from a manifest and Pydantic models."""

    loaded: LoadedTool = Field(exclude=True)
    services: Services = Field(exclude=True)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def build(cls, loaded: LoadedTool, services: Services) -> ManifestTool:
        manifest = loaded.manifest
        return cls(
            name=manifest.name,
            version=manifest.version,
            title=manifest.title,
            description=manifest.description,
            tags=set(manifest.tags),
            parameters=loaded.input_model.model_json_schema(),
            output_schema=loaded.output_model.model_json_schema(mode="serialization"),
            annotations=ToolAnnotations(title=manifest.title, **manifest.annotations.model_dump()),
            meta={"firms_mcp": {"require_auth": manifest.require_auth}},
            loaded=loaded,
            services=services,
        )

    async def execute(self, arguments: dict[str, Any]) -> ToolOutput:
        loaded = self.loaded
        try:
            params = loaded.input_model.model_validate(arguments or {})
        except ValidationError as exc:
            return loaded.output_model.invalid(describe_validation_error(exc))
        try:
            return await loaded.entry(params, self.services)
        except FirmsError as exc:
            return loaded.output_model.from_error(exc)
        except Exception:
            logger.exception("tool %s failed", self.name)
            return loaded.output_model(
                status="error",
                error_code="internal_error",
                error_message="The server failed while handling this request.",
                remediation="Try again; if it keeps failing, report it to the server operator.",
                retryable=True,
            )

    async def run(self, arguments: dict[str, Any]) -> ToolResult:
        output = await self.execute(arguments)
        data = output.model_dump(mode="json", exclude_none=True)
        return ToolResult(
            content=[TextContent(type="text", text=json.dumps(data, ensure_ascii=False))],
            structured_content=data,
            is_error=output.status == "error",
        )


def register_tools(mcp: FastMCP, services: Services) -> list[LoadedTool]:
    """Register every enabled tool on ``mcp``; return what was registered."""
    registered = []
    for loaded in discover_tools():
        if not loaded.manifest.enabled:
            logger.info("tool %s is disabled in its manifest", loaded.manifest.name)
            continue
        mcp.add_tool(ManifestTool.build(loaded, services))
        registered.append(loaded)
    return registered
