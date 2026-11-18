/**
 * Resources for hosts that let users attach context (FR-KB-010; ADR-0005):
 *
 * - `firms://knowledge/index`: table of contents (JSON)
 * - `firms://knowledge/{entry_id}`: one entry: its title as a heading, FIRMS's text verbatim,
 *   then a provenance line (Markdown)
 * - `firms://sources`: the source catalog, standard processing first (JSON)
 *
 * All three are fixed for a given server version.
 */
import {
  type McpServer,
  ResourceNotFoundError,
  ResourceTemplate,
} from "@modelcontextprotocol/server";
import type { KnowledgeEntry } from "../knowledge/index.js";
import { CATALOG_PROVENANCE, CATALOG_RETRIEVED, listSources } from "../sources/index.js";
import { knowledge } from "../tools/common.js";

export const INDEX_URI = "firms://knowledge/index";
export const ENTRY_TEMPLATE = "firms://knowledge/{entry_id}";
export const SOURCES_URI = "firms://sources";

export function renderEntry(entry: KnowledgeEntry): string {
  const retired =
    entry.status === "retired" ? " This entry is retired: FIRMS no longer publishes it." : "";
  return (
    `# ${entry.title}\n\n${entry.body}\n\n---\n\n` +
    `Source: ${entry.source_url} (retrieved ${entry.retrieved}). ` +
    `Knowledge entry \`${entry.id}\`, SHA-256 ${entry.content_sha256}.${retired}\n`
  );
}

function knowledgeIndex() {
  const kb = knowledge();
  return {
    sections: kb.sections().map((section) => ({
      id: section.id,
      title: section.title,
      entries: section.entry_ids.map((id) => ({ id, title: kb.get(id)?.title ?? id })),
    })),
    sources: [...kb.sources.values()].map((s) => ({
      id: s.id,
      title: s.title,
      url: s.url,
      retrieved: s.retrieved,
    })),
    entry_uri_template: ENTRY_TEMPLATE,
  };
}

const json = (uri: URL, value: unknown) => ({
  contents: [{ uri: uri.href, mimeType: "application/json", text: JSON.stringify(value, null, 2) }],
});

export function registerResources(server: McpServer): void {
  server.registerResource(
    "knowledge-index",
    INDEX_URI,
    {
      title: "FIRMS knowledge base: table of contents",
      description: "Sections, entry IDs, and titles of FIRMS's documentation, with its sources",
      mimeType: "application/json",
    },
    async (uri) => json(uri, knowledgeIndex()),
  );

  server.registerResource(
    "knowledge-entry",
    new ResourceTemplate(ENTRY_TEMPLATE, {
      list: async () => ({
        resources: knowledge()
          .ordered()
          .map((entry) => ({
            uri: `firms://knowledge/${entry.id}`,
            name: entry.id,
            title: entry.title,
            mimeType: "text/markdown",
          })),
      }),
    }),
    {
      title: "FIRMS knowledge entry",
      description: "One entry of FIRMS's documentation, verbatim, with its provenance",
      mimeType: "text/markdown",
    },
    async (uri, variables) => {
      const id = String(variables.entry_id ?? "");
      const entry = knowledge().get(id);
      if (!entry) {
        const suggestions = knowledge().suggestions(id);
        throw new ResourceNotFoundError(
          uri.href,
          `No knowledge entry ${JSON.stringify(id)}.${suggestions.length ? ` Closest IDs: ${suggestions.join(", ")}.` : ""}`,
        );
      }
      return { contents: [{ uri: uri.href, mimeType: "text/markdown", text: renderEntry(entry) }] };
    },
  );

  server.registerResource(
    "sources",
    SOURCES_URI,
    {
      title: "FIRMS fire data sources",
      description: "Source catalog, standard processing first (dates: use firms_list_data_sources)",
      mimeType: "application/json",
    },
    async (uri) =>
      json(uri, {
        retrieved: CATALOG_RETRIEVED,
        provenance: CATALOG_PROVENANCE,
        sources: listSources(),
      }),
  );
}
