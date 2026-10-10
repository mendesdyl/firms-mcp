# ADR-0002: Follow NASA Earthdata MCP conventions

- **Status:** Accepted
- **Date:** 2026-10-09
- **ARL linkage:** ARL1-M2 (baseline research includes the Earthdata MCP precedent);
  ARL4-M2 (consistency with NASA practice reduces organizational friction with a future
  partner).

## Context

The owner asked that the project "follow the example, documentation, and information …
about the design process of the earthdata MCP", which NASA has released. The Earthdata MCP
(`nasa/earthdata-mcp`, studied at commit `b071caf`, 2026-10-08) is an actively maintained,
production NASA MCP server. A summary of its practices and which ones this project adopts
is in [References §2](../research/REFERENCES.md#nasa-earthdata-mcp).

## Decision

Adopt the Earthdata MCP's stack and conventions unless there is a FIRMS-specific reason
not to:

1. **Stack:** Python, FastMCP 4 (`fastmcp>=4.1,<5`), the MCP Python SDK 2.x, Pydantic,
   `uv`, `pytest`, `ruff`.
2. **Tool layout:** one directory per tool containing `manifest.json` (name, SemVer
   version, LLM-facing description, tags, annotations, `require_auth`, `enabled`,
   examples), `tool.py` (entry function), and an output model. A loader registers tools
   from manifests and fails fast on invalid manifests.
3. **Models:** Pydantic input models with `extra="forbid"` and structured outputs carrying
   a `status` field (`success`, `no_results`, `error`) and an `error_message`.
4. **Server instructions** that define a workflow and honesty rules, as Earthdata's
   *Discover → Verify → Access*.
5. **Auth posture:** anonymous use for tools that do not need credentials; per-tool
   step-up authentication for those that do.
6. **Pagination:** `limit`, opaque query-scoped `cursor`, optional `fields`.
7. **Operational endpoints:** health check, `/.well-known/ard.json`, and `server.json` for
   the MCP Registry.
8. **Versioning:** server SemVer in `pyproject.toml`; per-tool SemVer in `manifest.json`;
   same bump rules.
9. **Docs:** `docs/consumers/` and `docs/developers/`, plus a per-client connection guide.
10. **Tests:** network blocked by default in tests; live integration tests opt-in and
    excluded from CI.

### Deliberate deviations

| Earthdata MCP | This project | Reason |
|---|---|---|
| Flat repository layout (`server.py`, `tools/`, … at root) | `src/firms_mcp/` package, tools in `firms_mcp/tools/<name>/` | Makes the server installable and runnable with `uvx firms-mcp` for local (stdio) users, which public-chatbot users without a hosted endpoint need |
| Tool entry functions must be synchronous (wrapped with `asyncio.to_thread`) | Async entry functions allowed | FIRMS calls use an async HTTP client; avoids a thread per call |
| OAuth proxy to Earthdata Login | Own authorization server collecting the user's FIRMS MAP_KEY | FIRMS keys are not issued by Earthdata Login ([ADR-0004](0004-authentication-bring-your-own-map-key.md)) |
| Langfuse, CloudWatch, AWS ECS, Terraform, Bamboo | Structured JSON logs; container image; host-agnostic | Infrastructure choices are the operator's; nothing here depends on AWS |
| `requires-python == 3.13.0` | `>=3.12`, developed on 3.13, CI on 3.12–3.14 | Wider compatibility for local installs |

## Alternatives considered

- **TypeScript SDK.** Rejected: diverges from the NASA precedent the owner asked to follow;
  the Python ecosystem also has the FIRMS-adjacent scientific tooling.
- **Low-level MCP SDK without FastMCP.** Rejected: FastMCP 4 provides dual-era protocol
  support, OAuth server scaffolding, CIMD, and MCP Apps support that would otherwise have
  to be rebuilt.

## Consequences

- Contributors familiar with the Earthdata MCP can navigate this repository immediately.
- A future NASA partner could federate the two servers with consistent tool conventions.
- The project inherits FastMCP's release cadence (risk R10 in the plan).

## References

- <https://github.com/nasa/earthdata-mcp> (commit `b071caf`)
- [References §2](../research/REFERENCES.md#nasa-earthdata-mcp)
