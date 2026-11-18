# Development

How to build, run, and test the iteration-2 server. The design is in
[ADR-0011](../decisions/0011-keyless-scope-typescript-rewrite-standard-data-first.md) and
[ADR-0012](../decisions/0012-typescript-project-layout-and-tool-contracts.md).

## Setup

Node.js 24 or 26 (the repository's `.node-version` says 26).

```bash
npm ci
```

## Everyday commands

| Command | What it does |
|---|---|
| `npm run check` | Everything CI runs: lint, types, tests, contracts, traceability, build, smoke |
| `npm test` | vitest (no network; loopback only) |
| `npm run lint` / `npm run format` | Biome check / format in place |
| `npm run typecheck` | TypeScript, no output |
| `npm run build` | Compile to `dist/` |
| `npm run smoke` | Start `dist/index.js` over stdio and check the handshake and tool list |
| `npm run contracts` | Regenerate `contracts/tools.json` after changing a tool |
| `npm run traceability` | Regenerate `docs/project/TRACEABILITY.md` after changing requirements or tests |
| `npm run dev` | Run from source, restarting on change |
| `npm run map-catalog` | Compare the Fire Map layer catalog with the live map (contacts FIRMS; run by hand) |
| `npm run knowledge -- <command>` | Knowledge base: `validate`, `sync`, `check`, `missing-data` ([Adding knowledge](ADDING_KNOWLEDGE.md)) |

## Running the server

```bash
npm run build
node dist/index.js          # stdio, for Claude Desktop, Claude Code, and other local hosts
node dist/index.js http     # Streamable HTTP on http://127.0.0.1:8000/mcp, health at /health
```

HTTP settings:

| Variable | Default | Meaning |
|---|---|---|
| `FIRMS_MCP_HOST` | `127.0.0.1` | Interface to bind |
| `FIRMS_MCP_PORT` | `8000` | Port |
| `FIRMS_MCP_ALLOWED_HOSTS` | — | Comma-separated host names accepted in the `Host` header. Required when `FIRMS_MCP_HOST` is not a loopback address |

To explore interactively: `npx @modelcontextprotocol/inspector node dist/index.js`.

## Tests and requirements

- Put the requirement a test verifies in its name: `it("[REQ-FR-URL-001] uses SP for covered dates", …)`.
- A requirement in [requirements.yaml](../project/requirements.yaml) whose verification is
  `test` and status `implemented` must have at least one tagged test;
  `npm run traceability:check` fails otherwise.
- When a requirement is implemented, change its status to `implemented` in the same change
  as its tests, and run `npm run traceability`.
- Tests cannot reach the network (`test/setup/no-network.ts`). Use fixtures for FIRMS
  responses; never a real MAP_KEY.

## Adding a tool

See [Adding a tool](ADDING_A_TOOL.md) for the full guide. In short:


1. Create `src/tools/<name>/tool.ts` exporting `defineTool({...})` with a `firms_` name, a
   `version`, a description that says when to use it, strict input and output schemas, and
   `READ_ONLY` annotations.
2. Add it to `src/tools/index.ts`.
3. Write tests tagged with its requirements.
4. Run `npm run contracts` and `npm run traceability`, then `npm run check`.

## Dependencies

Versions are pinned exactly. Wait a week after a release before adopting it (Dependabot is
configured that way); install with `npm install --save-exact --before=<date a week ago>`.
Run `npm audit --omit=dev` before merging; triage development-only advisories in the
[integration issues log](../project/INTEGRATION_ISSUES.md).
