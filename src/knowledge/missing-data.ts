/**
 * FIRMS's missing-data table, saved by the weekly sync (ADR-0011 §7, FR-KB-013). The live
 * table is keyless but undocumented and can take over a minute to load, so the server answers
 * from this snapshot, always with the date it was saved and the live page URL.
 */
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import * as z from "zod/v4";
import { defaultKnowledgeDir } from "./loader.js";

export const MISSING_DATA_PAGE = "https://firms.modaps.eosdis.nasa.gov/api/missing_data/";
export const MISSING_DATA_FILE = join("reference", "missing-data.json");

const Gap = z.strictObject({
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  satellite: z.string().min(1).max(80),
});

export const MissingDataSchema = z.strictObject({
  page_url: z.literal(MISSING_DATA_PAGE),
  retrieved: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  /** Days missing from the standard-processing (science quality) archive. */
  standard: z.array(Gap),
  /** Days missing from the near-real-time archive. */
  nrt: z.array(Gap),
});
export type MissingData = z.infer<typeof MissingDataSchema>;

export function loadMissingData(dir = defaultKnowledgeDir()): MissingData | undefined {
  const path = join(dir, MISSING_DATA_FILE);
  if (!existsSync(path)) return undefined;
  return MissingDataSchema.parse(JSON.parse(readFileSync(path, "utf8")));
}
