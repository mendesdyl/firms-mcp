import * as z from "zod/v4";
import { knowledge } from "../common.js";
import { defineTool, READ_ONLY } from "../definition.js";

export const listKnowledgeTopics = defineTool({
  name: "firms_list_knowledge_topics",
  version: "1.0.0",
  title: "List FIRMS documentation topics",
  description: [
    "Table of contents of the FIRMS knowledge base: the FIRMS FAQ in the FAQ's own sections and order, then supplements (Fire Map disclaimer, LANCE disclaimer and acknowledgments, attribute definitions, FIRMS API pages), with the sources they were taken from.",
    "Without arguments it returns each section's ID, title, and entry count. Pass `section` to list that section's entry IDs and titles, or `include_entries: true` to list every entry. Then read entries with firms_get_knowledge_entry or search them with firms_search_knowledge.",
  ].join("\n\n"),
  inputSchema: z.strictObject({
    section: z
      .string()
      .max(80)
      .optional()
      .describe("List the entries of one section, by ID (e.g. 'caveats')"),
    include_entries: z
      .boolean()
      .default(false)
      .describe("List every entry of every section (about 150 titles) instead of counts"),
    include_retired: z
      .boolean()
      .default(false)
      .describe("Include entries FIRMS no longer publishes"),
  }),
  outputSchema: z.object({
    total_entries: z.number().int(),
    sections: z.array(
      z.object({
        id: z.string(),
        title: z.string(),
        entry_count: z.number().int(),
        entries: z
          .array(
            z.object({
              id: z.string(),
              title: z.string(),
              kind: z.string(),
              status: z.string(),
            }),
          )
          .optional()
          .describe("Present when a section is requested or include_entries is true"),
      }),
    ),
    sources: z.array(
      z.object({
        id: z.string(),
        title: z.string(),
        publisher: z.string(),
        url: z.string(),
        retrieved: z.string(),
      }),
    ),
  }),
  annotations: READ_ONLY,
  async run({ section, include_entries, include_retired }) {
    const kb = knowledge();
    const all = kb.sections({ includeRetired: include_retired });
    const chosen = section === undefined ? all : all.filter((s) => s.id === section);
    if (section !== undefined && chosen.length === 0) {
      throw new Error(
        `unknown section ${JSON.stringify(section)}; sections: ${all.map((s) => s.id).join(", ")}`,
      );
    }
    const withEntries = include_entries || section !== undefined;
    return {
      total_entries: kb.ordered({ includeRetired: include_retired }).length,
      sections: chosen.map((s) => ({
        id: s.id,
        title: s.title,
        entry_count: s.entry_ids.length,
        ...(withEntries
          ? {
              entries: s.entry_ids.flatMap((id) => {
                const entry = kb.get(id);
                return entry
                  ? [{ id, title: entry.title, kind: entry.kind, status: entry.status }]
                  : [];
              }),
            }
          : {}),
      })),
      sources: [...kb.sources.values()].map((s) => ({
        id: s.id,
        title: s.title,
        publisher: s.publisher,
        url: s.url,
        retrieved: s.retrieved,
      })),
    };
  },
});
