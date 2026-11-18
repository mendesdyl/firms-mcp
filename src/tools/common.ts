/**
 * What the tools share: the knowledge base and catalogs (loaded once per process, then read
 * only), coverage for the URL tools, and the Zod schemas several tools use. The server keeps
 * no state between requests (ADR-0011 §8): coverage is asked for on every call.
 */
import type { ToolAnnotations } from "@modelcontextprotocol/server";
import * as z from "zod/v4";
import { todayUtc } from "../common/dates.js";
import { type KnowledgeBase, type KnowledgeEntry, loadKnowledgeBase } from "../knowledge/index.js";
import { loadMissingData, type MissingData } from "../knowledge/missing-data.js";
import { LINKABLE_MODES } from "../maplinks/catalog.js";
import { type Coverage, fetchCoverage, SENSOR_IDS, SOURCE_IDS } from "../sources/index.js";
import { READ_ONLY } from "./definition.js";

/** Read-only tools that also ask a FIRMS service (the map date service) for coverage. */
export const READ_ONLY_FIRMS: ToolAnnotations = { ...READ_ONLY, openWorldHint: true };

let knowledgeBase: KnowledgeBase | undefined;
/** The knowledge base, loaded on first use and then shared by every server instance. */
export function knowledge(): KnowledgeBase {
  knowledgeBase ??= loadKnowledgeBase();
  return knowledgeBase;
}

let missing: { data: MissingData | undefined } | undefined;
export function missingData(): MissingData | undefined {
  missing ??= { data: loadMissingData() };
  return missing.data;
}

export function today(): string {
  return todayUtc();
}

export function currentCoverage(signal: AbortSignal): Promise<Coverage> {
  return fetchCoverage({ today: today(), signal });
}

// --- Schemas -------------------------------------------------------------------------------

const DATE_HINT = "UTC date, YYYY-MM-DD";

export const IsoDateInput = z
  .string()
  .regex(/^\d{4}-\d{2}-\d{2}$/, "use YYYY-MM-DD")
  .describe(DATE_HINT);

export const BoxInput = z
  .strictObject({
    west: z.number().min(-180).max(180).describe("Western longitude, decimal degrees"),
    south: z.number().min(-90).max(90).describe("Southern latitude"),
    east: z.number().min(-180).max(180).describe("Eastern longitude"),
    north: z.number().min(-90).max(90).describe("Northern latitude"),
  })
  .describe(
    "Bounding box in decimal degrees, longitude first: west < east, south < north. Split a box that crosses the 180° meridian into two calls.",
  );

export const SensorsInput = z
  .array(z.enum(SENSOR_IDS))
  .min(1)
  .max(SENSOR_IDS.length)
  .describe(
    "Sensors to use. Omit for the defaults (VIIRS NOAA-20, NOAA-21, Suomi NPP, MODIS; each only for dates FIRMS has its data). landsat covers US/Canada only.",
  );

export const SourceIdOutput = z.enum(SOURCE_IDS);
export const ModeInput = z.enum(LINKABLE_MODES);

export const CoverageOutput = z.object({
  checked: z.boolean().describe("False when FIRMS's map date service could not be reached"),
  as_of: z.string(),
  source: z.enum(["map_dates_service", "snapshot"]),
  note: z.string(),
});

export const MapKeyOutput = z.object({
  placeholder: z.literal("[MAP_KEY]"),
  get_a_key: z.string(),
  where_it_goes: z.string(),
});

export const RelatedOutput = z.object({
  data_availability_url: z.string(),
  missing_data_page: z.string(),
  archive_download_page: z.string(),
  map_key_page: z.string(),
});

export const EntryOutput = z.object({
  id: z.string(),
  title: z.string().describe("FIRMS's question or heading, verbatim"),
  kind: z.string(),
  section: z.string(),
  section_title: z.string(),
  status: z.enum(["current", "retired"]),
  body: z.string().describe("FIRMS's text, verbatim (Markdown)"),
  source_url: z.string(),
  retrieved: z.string(),
  content_sha256: z.string(),
  related: z.array(z.string()),
  notice: z.string().nullable().describe("Set when FIRMS no longer publishes the entry"),
});
export type EntryOutput = z.infer<typeof EntryOutput>;

export function entryOutput(entry: KnowledgeEntry): EntryOutput {
  return {
    id: entry.id,
    title: entry.title,
    kind: entry.kind,
    section: entry.section,
    section_title: entry.section_title,
    status: entry.status,
    body: entry.body,
    source_url: entry.source_url,
    retrieved: entry.retrieved,
    content_sha256: entry.content_sha256,
    related: entry.related,
    notice:
      entry.status === "retired"
        ? "FIRMS no longer publishes this entry; it is kept for provenance. Say so if you rely on it."
        : null,
  };
}
