import * as z from "zod/v4";
import { EntryOutput, entryOutput, knowledge } from "../common.js";
import { defineTool, READ_ONLY } from "../definition.js";

export const getKnowledgeEntry = defineTool({
  name: "firms_get_knowledge_entry",
  version: "1.0.0",
  title: "Get FIRMS documentation entries",
  description: [
    "Return FIRMS knowledge-base entries by ID, each with FIRMS's text verbatim in `body`, its `source_url`, and its `retrieved` date.",
    "Use it to open entry IDs cited in other results (for example the FAQ entry on standard versus near real-time data), to follow an entry's `related` IDs, or to read an entry found with firms_list_knowledge_topics. Unknown IDs are listed in `not_found` with the closest existing IDs. Entries FIRMS no longer publishes have `status: retired` and a `notice`; say so if you rely on one.",
  ].join("\n\n"),
  inputSchema: z.strictObject({
    entry_ids: z
      .array(z.string().min(1).max(200))
      .min(1)
      .max(10)
      .describe(
        "Entry IDs (1-10), from search results, `related`, notes, or the table of contents",
      ),
  }),
  outputSchema: z.object({
    entries: z.array(EntryOutput),
    not_found: z.array(
      z.object({
        id: z.string(),
        suggestions: z.array(z.string()).describe("Closest existing IDs"),
      }),
    ),
  }),
  annotations: READ_ONLY,
  async run({ entry_ids }) {
    const kb = knowledge();
    const ids = [...new Set(entry_ids)];
    return {
      entries: ids.flatMap((id) => {
        const entry = kb.get(id);
        return entry ? [entryOutput(entry)] : [];
      }),
      not_found: ids
        .filter((id) => !kb.get(id))
        .map((id) => ({ id, suggestions: kb.suggestions(id) })),
    };
  },
});
