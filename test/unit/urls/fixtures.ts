import { readFileSync } from "node:fs";
import { type Coverage, coverageFromMapDates } from "../../../src/sources/index.js";

/** The day the map-date fixture was captured; builders are tested as if it were today. */
export const TODAY = "2026-11-18";

/** FIRMS map date service response captured on 2026-11-18. */
export const MAP_DATES: unknown = JSON.parse(
  readFileSync("test/fixtures/map-dates_2026-11-18.json", "utf8"),
);

/**
 * Coverage as the service reported it on 2026-11-18. Standard processing ends 2026-07-31 for
 * every VIIRS satellite and 2026-08-31 for MODIS; Suomi NPP NRT ends 2026-11-02.
 */
export const COVERAGE: Coverage = coverageFromMapDates(MAP_DATES, TODAY);
