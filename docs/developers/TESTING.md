# Testing

How the project is tested, following [ADR-0008](../decisions/0008-testing-and-verification-strategy.md).
Tests check that the software does what its requirements say; whether it improves the
answers people get is the separate [evaluation](../design/EVALUATION.md).

## Running the tests

```bash
uv sync --extra dev --extra sync
```

```bash
uv run pytest
```

Useful variations:

```bash
uv run pytest tests/integration -q
```

```bash
uv run pytest --cov --cov-report=term
```

The same checks run in CI (`.github/workflows/ci.yml`) on Python 3.12, 3.13, and 3.14,
together with `ruff check`, `ruff format --check`, `python -m firms_mcp.knowledge validate`,
the traceability check, a wheel-contents check, and a container smoke test.

## Layers

| Directory | What it tests | Network |
|---|---|---|
| `tests/unit/` | One component at a time: knowledge base, FIRMS client and parser, map links, each tool (through the in-memory MCP client), token codec, step-up middleware, settings | None (FIRMS mocked with `respx`) |
| `tests/contract/` | The knowledge base against the owner-provided FAQ text, line by line | None |
| `tests/integration/` | The assembled server: both protocol eras, in memory, over Streamable HTTP (in-process ASGI), over stdio (the real `python -m firms_mcp` process), and the OAuth connect flow end to end | Loopback only |
| `tests/test_traceability.py`, `tests/test_documentation.py` | Requirements are well formed and implemented ones are tested; the tool catalog matches the manifests | None |
| `tests/live/` *(WP11)* | The real FIRMS API with a real MAP_KEY | Real; opt-in |

## Rules

- **No real network.** An autouse fixture in `tests/conftest.py` makes every non-loopback
  connection fail with `NetworkAccessBlocked` (NFR-001). Mock FIRMS with `respx`
  (FIRMS host `https://firms.test` in `tests/fixtures/services.py`).
- **Requirements.** Mark each test with the requirements it verifies:
  `@pytest.mark.req("FR-DATA-005")`. A requirement whose status is `implemented` must have
  at least one test; after adding tests or changing requirements run
  `uv run python scripts/gen_traceability.py` to regenerate
  [TRACEABILITY.md](../project/TRACEABILITY.md) (CI checks it is current).
- **Fixed time.** Server tests use a fixed clock (2026-10-10 12:00 UTC) so date windows and
  map links are deterministic.
- **Secrets.** Tests use the 32-character test keys in `tests/fixtures/firms_csv.py`; never
  a real key. Tests assert that keys never appear in results, links, or logs.
- **Both eras.** Server behaviour is tested with the FastMCP client in `legacy` mode
  (handshake, 2025-11-25) and `auto` mode (negotiates 2026-07-28).

## Helpers

`tests/fixtures/services.py` provides `make_services(...)` (settings, knowledge base, FIRMS
client, credential mode, clock), `make_server(...)`, `http_client(server, mode)` (an MCP
client over in-process Streamable HTTP that also records the `mcp-*` headers of each
request), and `raw_http(server)` for operational routes and hand-built requests. The OAuth
tests build an app with `create_auth_provider` and drive `/register`, `/authorize`,
`/connect`, and `/token` with `httpx2`.

## Live tests *(WP11)*

Live tests are marked `live`, excluded by default (`addopts = -m "not live"`), and skipped
unless `FIRMS_MAP_KEY` is set. Run them with:

```bash
uv run pytest -m live
```

Their results are ARL 5 evidence and are recorded in the work summary, not in CI.
