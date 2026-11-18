import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { parseMissingData } from "../../../scripts/ts/faq-sync/missing-data.js";
import { loadMissingData, MISSING_DATA_PAGE } from "../../../src/knowledge/missing-data.js";

const feed = JSON.parse(readFileSync("test/fixtures/missing-data-feed.json", "utf8"));

describe("missing-data snapshot", () => {
  it("[REQ-FR-KB-013] splits the table into standard and NRT gaps with the date it was saved", () => {
    const snapshot = parseMissingData(feed, "2026-11-18");
    expect(snapshot.page_url).toBe(MISSING_DATA_PAGE);
    expect(snapshot.retrieved).toBe("2026-11-18");
    expect(snapshot.standard[0]).toEqual({ date: "2026-07-16", satellite: "Suomi NPP (VIIRS)" });
    expect(snapshot.nrt[0]).toEqual({ date: "2024-03-06", satellite: "NOAA-21 (VIIRS)" });
    expect(snapshot.standard).toHaveLength(5);
    expect(snapshot.nrt).toHaveLength(3); // the last rows have no NRT half
  });

  it("[REQ-FR-KB-013] rejects a feed that failed or holds unexpected values", () => {
    expect(() => parseMissingData({ success: false }, "2026-11-18")).toThrow(/success/);
    const bad = { success: true, html: "<tr><td>yesterday</td><td>x</td><td></td><td></td></tr>" };
    expect(() => parseMissingData(bad, "2026-11-18")).toThrow();
    const short = { success: true, html: "<tr><td>2026-01-01</td></tr>" };
    expect(() => parseMissingData(short, "2026-11-18")).toThrow(/cells/);
  });

  it("[REQ-FR-KB-013] loads the saved snapshot", () => {
    const dir = mkdtempSync(join(tmpdir(), "firms-md-"));
    mkdirSync(join(dir, "reference"));
    writeFileSync(
      join(dir, "reference", "missing-data.json"),
      JSON.stringify(parseMissingData(feed, "2026-11-18")),
    );
    expect(loadMissingData(dir)?.retrieved).toBe("2026-11-18");
    expect(loadMissingData(mkdtempSync(join(tmpdir(), "firms-md-")))).toBeUndefined();
  });
});
