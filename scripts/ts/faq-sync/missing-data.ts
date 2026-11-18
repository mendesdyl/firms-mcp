/** Fetch and parse FIRMS's missing-data table (undocumented; running list LU-17). */
import {
  MISSING_DATA_PAGE,
  type MissingData,
  MissingDataSchema,
} from "../../../src/knowledge/missing-data.js";
import { collapse } from "./convert.js";
import { children, findAll, getText, isTag, parseHtml } from "./dom.js";

export const MISSING_DATA_FEED = `${MISSING_DATA_PAGE}?action=fetch_data`;

/**
 * The page's table rows: standard date, standard satellite, NRT date, NRT satellite. Either
 * half of a row may be empty. Every value is checked against the schema, since this is data
 * from a page, not from a documented API.
 */
export function parseMissingData(feed: unknown, retrieved: string): MissingData {
  const data = feed as { success?: unknown; html?: unknown };
  if (data?.success !== true || typeof data.html !== "string") {
    throw new Error("missing-data feed did not report success");
  }
  const standard: MissingData["standard"] = [];
  const nrt: MissingData["nrt"] = [];
  for (const row of findAll(parseHtml(data.html), ["tr"])) {
    const cells = children(row)
      .filter(isTag)
      .filter((cell) => cell.name === "td")
      .map((cell) => collapse(getText(cell)).trim());
    if (cells.length !== 4) throw new Error(`unexpected row with ${cells.length} cells`);
    const [sDate, sSat, nDate, nSat] = cells as [string, string, string, string];
    if (sDate || sSat) standard.push({ date: sDate, satellite: sSat });
    if (nDate || nSat) nrt.push({ date: nDate, satellite: nSat });
  }
  if (!standard.length && !nrt.length) throw new Error("missing-data table is empty");
  return MissingDataSchema.parse({ page_url: MISSING_DATA_PAGE, retrieved, standard, nrt });
}
