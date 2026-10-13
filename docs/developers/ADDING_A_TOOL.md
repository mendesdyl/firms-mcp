# Adding a Tool

Tools follow the NASA Earthdata MCP layout
([ADR-0002](../decisions/0002-follow-nasa-earthdata-mcp-conventions.md)): one directory per
tool, a versioned manifest, Pydantic models, and an entry function. The loader
(`firms_mcp.tools.loader`) finds the directory, checks it, and registers the tool; nothing
else needs to change for the tool to appear in `tools/list`.

## 1. Create the directory

```
src/firms_mcp/tools/<tool_name>/
├── __init__.py        # docstring only
├── manifest.json
├── models.py
└── tool.py
```

The directory name and the manifest `name` must be the same snake_case name.

## 2. Write the models

```python
# models.py
from pydantic import Field

from firms_mcp.tools.common import InputModel, ToolOutput


class MyToolInput(InputModel):  # InputModel rejects unknown arguments
    place: str = Field(description="What the model should pass, in plain words")
    limit: int = Field(default=10, ge=1, le=50, description="…")


class MyToolOutput(ToolOutput):  # ToolOutput adds status and error fields
    items: list[str] = Field(default_factory=list)
```

Write every `description` for the model that will call the tool. Bound every list and
page size (NFR-004).

## 3. Write the entry function

```python
# tool.py
from firms_mcp.services import Services
from firms_mcp.tools.my_tool.models import MyToolInput, MyToolOutput


async def my_tool(params: MyToolInput, services: Services) -> MyToolOutput:
    if not params.place.strip():
        return MyToolOutput.invalid("place must not be empty.")
    return MyToolOutput(status="success", items=[...])
```

The loader reads the input model from the `params` annotation and the output model from
the return annotation. Use `services` for everything external: `services.knowledge`,
`services.firms`, `services.credentials.require()` (raises `auth_required` when no key is
connected), `services.today()` for UTC dates. Raise `FirmsError` subclasses or return
`.invalid(...)`; the loader turns errors into structured results. Never accept a MAP_KEY
as a parameter (SEC-002) and never put one in a result (SEC-001).

## 4. Write the manifest

```json
{
  "name": "my_tool",
  "version": "1.0.0",
  "title": "Short title for people",
  "description": "What the tool does, when to use it, what the result means, and whether it needs a FIRMS MAP_KEY. Written for the model.",
  "entry_function": "my_tool",
  "tags": ["…"],
  "annotations": {
    "readOnlyHint": true,
    "destructiveHint": false,
    "idempotentHint": true,
    "openWorldHint": false
  },
  "require_auth": false,
  "enabled": true,
  "examples": {
    "basic": {"description": "…", "params": {"place": "Boise"}}
  }
}
```

All four annotations are required; `openWorldHint` is true when the tool calls an external
service. `require_auth: true` marks tools that need the user's MAP_KEY: over HTTP, calls to
them without a token get the OAuth challenge
([Authentication](../design/AUTHENTICATION.md#step-up-fr-auth-003)). Examples are validated
against the input model when the server starts.

## 5. Test and document

- Add tests under `tests/unit/tools/` with `@pytest.mark.req(...)` for the requirements
  they verify, mocking FIRMS with `respx` (see `tests/fixtures/services.py`).
- Add a `### \`my_tool\` (v1.0.0)` section and an overview row to the
  [tool catalog](../design/TOOLS.md); a test checks the name, version, and every parameter.
- Add the tool to `capabilities` in `src/firms_mcp/discovery/ard.json`; a test checks it.
- Run `uv run pytest` and `uv run python scripts/gen_traceability.py`.

## Changing a tool

Bump the manifest version (ADR-0010): **major** for removed or renamed parameters or
output fields, **minor** for additions, **patch** for fixes that do not change the
interface. Update the catalog section heading to the new version and note the change in
the [changelog](../../CHANGELOG.md).
