/** Knowledge-base entries and sources (ADR-0005). The schemas match iteration 1's exactly. */
import { createHash } from "node:crypto";
import * as z from "zod/v4";

const ID = /^[a-z0-9]+(?:[.-][a-z0-9]+)*$/;
const DATE = /^\d{4}-\d{2}-\d{2}$/;

const uniqueList = z
  .array(z.string())
  .default([])
  .transform((items) => [...new Set(items)]);

export const KnowledgeSourceSchema = z.strictObject({
  id: z.string().regex(ID),
  title: z.string(),
  publisher: z.string(),
  url: z.string(),
  retrieved: z.string().regex(DATE),
  license_note: z.string(),
  notes: z.string().nullish(),
});
export type KnowledgeSource = z.infer<typeof KnowledgeSourceSchema>;

export const ENTRY_KINDS = ["faq", "faq-section-intro", "faq-preamble", "supplement"] as const;

export const KnowledgeEntrySchema = z.strictObject({
  /** Stable identifier, e.g. `faq.caveats.…`. */
  id: z.string().regex(ID),
  /** Verbatim question or heading. */
  title: z.string().min(1),
  kind: z.enum(ENTRY_KINDS),
  section: z.string().regex(ID),
  section_title: z.string(),
  /** ID of a source in sources.yaml. */
  source: z.string(),
  source_url: z.string(),
  retrieved: z.string().regex(DATE),
  content_sha256: z.string().regex(/^[0-9a-f]{64}$/),
  /** Position within its source, for tables of contents. */
  order: z.number().int().min(0),
  tags: uniqueList,
  related: uniqueList,
  status: z.enum(["current", "retired"]).default("current"),
  /** Verbatim content (Markdown). */
  body: z.string(),
});
export type KnowledgeEntry = z.infer<typeof KnowledgeEntrySchema>;

/**
 * SHA-256 of an entry body after newline and trailing-whitespace normalization. Must give
 * the same value as iteration 1's Python `content_hash`, because the hashes are stored in
 * the entry files.
 */
export function contentHash(body: string): string {
  const normalized = body
    .replaceAll("\r\n", "\n")
    .split("\n")
    .map((line) => line.trimEnd())
    .join("\n")
    .replace(/^\n+|\n+$/g, "");
  return createHash("sha256").update(normalized, "utf8").digest("hex");
}
