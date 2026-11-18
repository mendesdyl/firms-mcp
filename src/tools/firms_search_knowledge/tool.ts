import * as z from "zod/v4";
import { EntryOutput, entryOutput, knowledge } from "../common.js";
import { defineTool, READ_ONLY } from "../definition.js";

export const searchKnowledge = defineTool({
  name: "firms_search_knowledge",
  version: "1.0.0",
  title: "Search FIRMS documentation",
  description: [
    "Search FIRMS's own documentation (the complete FIRMS FAQ, the Fire Map and LANCE disclaimers, the MODIS/VIIRS attribute definitions, and the FIRMS API pages) and return the best-matching entries in full.",
    "Every entry's `body` is FIRMS's text, verbatim, with its `source_url` and `retrieved` date. Quote or closely follow these bodies when you explain what detections mean, caveats, latency, sensors, standard versus near real-time data, or how to use FIRMS; do not answer such questions from memory when an entry covers them. The `snippet` only shows where the query matched.",
    "Ranking is deterministic (BM25 over titles, tags, and bodies). Keep `limit` small (default 3): entries are returned whole. Use `section` (an ID from firms_list_knowledge_topics, such as `caveats`, `viirs`, `modis`, `landsat`, `fire-map`) to narrow a search, and firms_get_knowledge_entry to follow `related` IDs.",
  ].join("\n\n"),
  inputSchema: z.strictObject({
    query: z
      .string()
      .min(1)
      .max(500)
      .describe("What to look for, in plain words, e.g. 'why was a fire not detected'"),
    limit: z
      .number()
      .int()
      .min(1)
      .max(10)
      .default(3)
      .describe("Entries to return (1-10); each is returned in full"),
    section: z
      .string()
      .max(80)
      .optional()
      .describe("Only search one section, by ID from firms_list_knowledge_topics"),
    include_retired: z
      .boolean()
      .default(false)
      .describe("Also search entries FIRMS no longer publishes (kept for provenance)"),
  }),
  outputSchema: z.object({
    query: z.string(),
    total: z.number().int(),
    results: z.array(
      EntryOutput.extend({
        score: z.number().describe("Relevance; comparable only within one search"),
        snippet: z.string().describe("Where the query terms appear; not a quote"),
      }),
    ),
    suggestion: z.string().nullable(),
  }),
  annotations: READ_ONLY,
  async run({ query, limit, section, include_retired }) {
    const hits = knowledge().search(query, {
      limit,
      section,
      includeRetired: include_retired,
    });
    return {
      query,
      total: hits.length,
      results: hits.map((hit) => ({
        ...entryOutput(hit.entry),
        score: hit.score,
        snippet: hit.snippet,
      })),
      suggestion: hits.length
        ? null
        : "No entry matched. Try other words or FIRMS terms, drop `section`, or browse with firms_list_knowledge_topics.",
    };
  },
});
