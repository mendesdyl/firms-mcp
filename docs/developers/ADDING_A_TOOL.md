# Adding a Tool

Each tool is one `defineTool({...})` value in `src/tools/<name>/tool.ts`
([ADR-0012](../decisions/0012-typescript-project-layout-and-tool-contracts.md)). Its Zod
schemas are the single source of truth: the SDK derives the JSON Schema clients see, and
`npm run contracts` writes the same schemas to `contracts/tools.json`.

## 1. Define the tool

```ts
// src/tools/firms_example/tool.ts
import * as z from "zod/v4";
import { defineTool, READ_ONLY } from "../definition.js";

export const example = defineTool({
  name: "firms_example", // snake_case, firms_ prefix; the directory has the same name
  version: "1.0.0",
  title: "Short title for people",
  description: "What it does, when to use it, and what the result means. Written for the model.",
  inputSchema: z.strictObject({ // strict: unknown arguments are rejected
    place: z.string().min(1).max(200).describe("What the model should pass, in plain words"),
  }),
  outputSchema: z.object({ items: z.array(z.string()) }),
  annotations: READ_ONLY,
  async run({ place }, signal) {
    if (!place.trim()) throw new Error("place must not be empty; give a place name.");
    return { items: [place] };
  },
});
```

- **Describe every field** for the model that will call the tool, and bound every string,
  list, and page size (NFR-004).
- **Errors** are thrown; the message becomes an `isError` result the model reads, so say how
  to recover. Builders throw `UrlBuilderError` with such messages.
- **Annotations:** `READ_ONLY`, or `READ_ONLY_FIRMS` (`src/tools/common.ts`) when the tool
  asks a FIRMS service, which sets `openWorldHint`.
- **Shared pieces** are in `src/tools/common.ts`: the knowledge base, the missing-data table,
  `currentCoverage(signal)` and `today()` for URL tools, and schemas for boxes, dates,
  sensors, coverage, and MAP_KEY guidance.
- **Never accept a MAP_KEY** (SEC-002). URLs that need one carry `[MAP_KEY]` and the
  `MAP_KEY_GUIDANCE` from `src/common/links.ts`; URL results carry `LIMITATIONS`.

## 2. Register it

Add it to `src/tools/index.ts`; the order there is the order of `tools/list` (FR-MCP-008).

## 3. Test and document it

1. Tests in `test/unit/tools/`, through an in-memory client (`test/helpers.ts`), each named
   with the requirement it verifies (`[REQ-…]`).
2. A section `### \`firms_example\` (v1.0.0)` in the [tool catalog](../design/TOOLS.md) that
   names every parameter, and a row in its overview table (a test checks both).
3. If the server instructions should mention it, update `src/server/instructions.ts`.
4. `npm run contracts`, `npm run traceability`, then `npm run check`.
5. Bump the server version (minor) and record the tool in the changelog
   ([Versioning and releasing](RELEASING.md)).
