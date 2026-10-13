# Integration Issues Log

Technical issues found while bringing the components together, and how each was worked
out. This log is evidence for **ARL4-M1** (*components brought together; technical
integration issues worked out*); organizational and human-process issues (ARL4-M2) are in
[Operations and governance](OPERATIONS_AND_GOVERNANCE.md). Entries are added as issues are
found and are not deleted; a resolution is recorded by updating the status and evidence.

Status: **Resolved** (fixed and covered by a test or check) · **Mitigated** (risk reduced;
residual noted) · **Accepted** (no change needed; reason given) · **Open** (work package
named).

| ID | Found | Issue | Resolution | Status | Evidence |
|---|---|---|---|---|---|
| II-01 | 2026-10-10, WP6 spike | Server instructions reach 2026-07-28 clients only through `server/discover`. A client that pins the protocol version without calling `server/discover` receives no instructions | Clients that negotiate (the normal case) receive them in both eras. Every tool description restates the rules that tool depends on (longitude-first areas, UTC, never summing across sources, never asking for the key in the chat), so a client without the instructions still sees them | Mitigated | `tests/integration/test_server_surface.py::test_instructions_reach_clients_in_both_eras`; manifests |
| II-02 | 2026-10-10, owner | `.env` values are read by `pydantic-settings` but not exported to `os.environ`, and the knowledge loader read `FIRMS_MCP_KNOWLEDGE_DIRS` from `os.environ`, so a value in `.env` was ignored | The variable is now a `Settings` field (`knowledge_dirs`) and the loader takes `Settings` | Resolved | `tests/unit/test_credentials_config.py::test_extra_knowledge_dirs_come_from_settings_including_dotenv` |
| II-03 | 2026-10-10, WP7 | FastMCP function tools validate arguments from the Python signature and report failures as protocol errors without the `status` / `error_code` / remediation structure ADR-0002 requires | Tools are registered as `ManifestTool`, a FastMCP `Tool` subclass that validates with the tool's own input model (unknown arguments rejected) and returns every outcome as structured content, flagged `isError` for errors. The published input schema is that model's schema | Resolved | `test_invalid_arguments_return_structured_errors`; `test_invalid_requests_never_reach_firms` |
| II-04 | 2026-10-10, WP7 | FastMCP advertises the `logging` capability to handshake-era clients, although MCP 2026-07-28 deprecates protocol logging and ADR-0003 says the server does not use it | The server never sends log notifications; logs are JSON lines on stderr. No client depends on the capability | Accepted | Raw `initialize` response in `test_older_handshake_revision_is_accepted` |
| II-05 | 2026-10-10, WP7 | The Streamable HTTP app needs its Starlette lifespan (the session manager) to run, so in-process tests that skip it fail | Test helpers enter `app.router.lifespan_context` before connecting | Resolved | `tests/fixtures/services.py` (`http_client`, `raw_http`) |
| II-06 | 2026-10-10, WP7 | Only 2026-07-28 requests carry `Mcp-Method` / `Mcp-Name` headers; handshake-era requests name the tool only in the JSON-RPC body. The per-tool step-up of ADR-0004 must handle both | WP8: read the headers when present, otherwise buffer and parse the body (as the Earthdata MCP's `StepUpAuth` does) | Open (WP8) | Header capture in `test_streamable_http_in_both_eras` |
| II-07 | 2026-10-10, WP7 | Two HTTP stacks are in play: FIRMS calls use `httpx` (mocked with `respx`), while FastMCP's client uses `httpx2`. Mocking one does not affect the other | Tests mock FIRMS with `respx` and drive MCP over `httpx2`'s ASGI transport, so MCP traffic is never intercepted by FIRMS mocks and vice versa | Resolved | Tool and integration tests |
| II-08 | 2026-10-10, WP7 | With `ruff` 0.17, four files from WP3–WP5 are no longer formatted as the formatter expects and nine lint findings (unused `noqa` directives, one `SIM905`) appear in earlier modules | Fix in a separate style commit when the CI quality gate is added | Open (WP10) | `uv run ruff check src tests scripts` |
