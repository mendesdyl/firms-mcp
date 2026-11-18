# ADR-0012: TypeScript project layout and tool contracts

- **Status:** Accepted
- **Date:** 2026-11-18
- **Supersedes in part:** [ADR-0002](0002-follow-nasa-earthdata-mcp-conventions.md) (the
  per-tool `manifest.json` file is replaced by a per-tool TypeScript definition plus a
  generated contract file; the other Earthdata conventions stand).
- **ARL linkage:** ARL2-M1, ARL3-M1, ARL4-M1 (the TypeScript components and their
  integration).

## Context

[ADR-0011](0011-keyless-scope-typescript-rewrite-standard-data-first.md) moved the server
to TypeScript on the MCP TypeScript SDK v2, kept stateless, with tool contracts held as
language-neutral data so a later port (for example to FIRMS's PHP backend) rewrites only a
thin layer. It left two questions to this step: whether the Earthdata-style per-tool
`manifest.json` survives in TypeScript, and how the project is laid out and checked.

In iteration 1 the manifest held each tool's name, version, description, annotations, and
input/output schemas as JSON, and Pydantic models repeated the schemas in Python. In
TypeScript the SDK takes Zod schemas directly and derives the JSON Schema clients see; a
hand-written JSON manifest would be a second copy of the same schemas that could drift.

## Decision

### 1. Tool definitions and contracts

- Each tool lives in `src/tools/<name>/` and exports one `defineTool({...})` value: name
  (`firms_` prefix), semantic `version`, title, description, annotations, Zod input schema
  (strict: unknown arguments rejected), Zod output schema, and a `run` function.
- **Zod is the single source of truth.** `npm run contracts` writes every tool's name,
  version, title, description, annotations, and input and output JSON Schemas to
  `contracts/tools.json`. CI fails if the file is out of date. That file is the contract
  another implementation must satisfy, playing the part the Earthdata manifest played.
- Every tool returns structured content validated against its output schema, with the
  same data as JSON text. A thrown error becomes an `isError` result whose message says how
  to recover.
- `src/tools/index.ts` lists the tools in the order `tools/list` returns them.

### 2. Layout

```
src/index.ts            entry point: stdio (default) or `http`
src/server/             server factory, instructions, HTTP app (/mcp, /health)
src/tools/              defineTool, the tool list, one directory per tool
src/version.ts          server name and version (a test keeps it equal to package.json)
contracts/tools.json    generated tool contract
scripts/ts/             contracts, traceability, smoke test
test/                   vitest: unit/, integration/, setup/ (network guard)
```

Later steps add `src/knowledge/`, `src/maplinks/`, `src/apiurls/`, and `src/sources/`
beside these ([ADR-0011](0011-keyless-scope-typescript-rewrite-standard-data-first.md),
[Extending to keyed data §4.1](../design/EXTENDING_TO_KEYED_DATA.md)).

### 3. Toolchain

| Concern | Choice |
|---|---|
| Runtime | Node.js 24 and 26 (the active LTS lines); `engines: >=24`; `.node-version` 26 |
| Package manager | npm with a committed `package-lock.json`; `npm ci` in CI |
| MCP | `@modelcontextprotocol/server` 2.x with the Express and Node adapters; `@modelcontextprotocol/client` for tests and the smoke test |
| Schemas | Zod 4 (`zod/v4`) |
| Compiler | TypeScript 7, strict, with `noUncheckedIndexedAccess` and `exactOptionalPropertyTypes` |
| Lint and format | Biome (one tool, recommended rules) |
| Tests | vitest; no network except loopback (NFR-001) |
| Traceability | `[REQ-<ID>]` in test names; `scripts/ts/traceability.ts` checks `requirements.yaml` and writes `TRACEABILITY.md` |

### 4. Transports and HTTP safety

- stdio by default (`firms-mcp-server`); stateless Streamable HTTP with `firms-mcp-server
  http`, a new server instance per request.
- HTTP binds to `127.0.0.1` by default with Host/Origin checks against DNS rebinding.
  Binding anywhere else requires `FIRMS_MCP_ALLOWED_HOSTS`; the server refuses to start
  without it.

### 5. Supply chain

- Dependencies are pinned exactly in `package.json` and locked in `package-lock.json`.
- New versions are adopted after a one-week cooldown: the initial install used
  `npm install --before=<one week ago>`, and Dependabot is configured with
  `cooldown: default-days: 7` (security updates are not delayed).
- CI fails on a moderate or higher advisory in the dependencies the server ships with
  (`npm audit --omit=dev`). Development-only advisories are triaged in the
  [integration issues log](../project/INTEGRATION_ISSUES.md) (II-18).
- The package is `private: true`; nothing is published (ADR-0011 §9).

### 6. Transition from Python

The Python server stays on `main`, with its own CI jobs, until the TypeScript server
reaches parity for the keyless scope (running list WK-23). Python is then removed in one
change, and the Python knowledge-sync script is retired once its TypeScript port has
produced a reviewed sync pull request (WK-21). Until then:

- requirement statuses describe the TypeScript server
  ([requirements.yaml](../project/requirements.yaml)); the traceability matrix is
  generated from the TypeScript tests;
- the Python suite still runs and its markers must still name known requirements.

## Alternatives considered

| Alternative | Why not |
|---|---|
| Keep a hand-written `manifest.json` per tool | A second copy of the schemas that can drift from the Zod definitions; the generated contract gives the same portable file without the duplication |
| ESLint + Prettier | Two tools and several plugins to keep current; Biome covers lint and format with one dependency |
| Remove Python immediately | `main` would have no working server for several steps |
| A separate `server/` directory for TypeScript | `src/` is the convention the SDK guide and most tools expect; the Python package lives in `src/firms_mcp/`, so the two do not collide during the transition |

## Consequences

- Adding a tool is one directory and one line in `src/tools/index.ts`; `npm run contracts`
  records the change, and a version bump in `defineTool` is visible in review.
- The contract file lets a PHP or other port be checked against the same schemas.
- Two toolchains run in CI until the Python code is removed.
