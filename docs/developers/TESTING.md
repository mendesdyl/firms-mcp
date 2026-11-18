# Testing

How the server is verified ([ADR-0008](../decisions/0008-testing-and-verification-strategy.md)).
Every check CI runs is one command:

```bash
npm run check
```

It runs Biome (lint and format), TypeScript, knowledge-base validation, the vitest suite, the
tool-contract check, the traceability check, the build, and a stdio smoke test against
`dist/`. CI (`.github/workflows/ci.yml`) runs it on Node 24 and 26, audits the dependencies
the server ships with (`npm audit --omit=dev`), and builds the container image and checks its
`/health` and `tools/list`.

## Layout

| Directory | What it covers | Network |
|---|---|---|
| `test/unit/knowledge/` | Loader, front matter, search (including parity with iteration 1 on a frozen corpus) | None |
| `test/unit/sync/` | The FAQ sync: page parsing, conversion, guard, missing-data table | None (fixtures) |
| `test/unit/urls/` | Source catalog, coverage and its fallback, standard-first selection, API URLs, KML, Fire Map links, the map catalog check's parsing | None (fixtures) |
| `test/unit/tools/` | The seven tools, the resources, and the server instructions through an in-memory MCP client; the tool catalog (DOC-002) | None (`fetch` stubbed) |
| `test/unit/*.test.ts` | `defineTool`, contracts, traceability, version, the network guard | None |
| `test/contract/` | FAQ completeness: every line of the synced page is in the knowledge base (FR-KB-001) | None |
| `test/integration/` | The assembled server over stdio and stateless Streamable HTTP, current and handshake-era clients | Loopback only |

## Rules

- **No real network** (NFR-001). `test/setup/no-network.ts` makes every non-loopback
  connection or `fetch` throw. FIRMS responses come from `test/fixtures/` (for example the
  map date service response captured on 2026-11-18); tool tests stub `fetch` and pin the
  date with `vi.setSystemTime`.
- **Requirements in test names.** `it("[REQ-FR-URL-001] …")`. A requirement whose status is
  `implemented` and verification `test` must have at least one tagged test;
  `npm run traceability:check` fails otherwise and `npm run traceability` regenerates
  [TRACEABILITY.md](../project/TRACEABILITY.md).
- **No secrets.** The server never sees a MAP_KEY; tests use the `[MAP_KEY]` placeholder.

## Checks against live FIRMS

Not part of `npm run check`; run by hand:

| Command | Checks |
|---|---|
| `npm run map-catalog` | The Fire Map layer catalog against the live map (II-29) |
| `npm run knowledge -- check` | The knowledge base against the live FAQ page, without writing |
| A Fire Map link opened in a browser | The map keeps every layer in the link ([map links](../design/MAP_LINKS.md)) |
