import { describe, expect, it } from "vitest";
import { allowedLayers, MAP_CATALOG } from "../../../src/maplinks/index.js";
import {
  COVERAGE_SNAPSHOT,
  coverageFromMapDates,
  DEFAULT_SENSORS,
  fetchCoverage,
  getSensor,
  getSource,
  listSources,
  SENSORS,
  SOURCES,
} from "../../../src/sources/index.js";
import { repoKb } from "../knowledge/fixtures.js";
import { MAP_DATES, TODAY } from "./fixtures.js";

describe("source catalog", () => {
  it("[REQ-FR-DATA-015] lists standard-processing sources first and marks them preferred", () => {
    const listed = listSources();
    const firstNrt = listed.findIndex((s) => s.processing === "NRT");
    expect(firstNrt).toBeGreaterThan(0);
    expect(listed.slice(0, firstNrt).every((s) => s.processing === "SP" && s.preferred)).toBe(true);
    expect(listed.slice(firstNrt).every((s) => s.processing === "NRT" && !s.preferred)).toBe(true);
    expect(listed.map((s) => s.id)).toEqual(SOURCES.map((s) => s.id));
  });

  it("[REQ-FR-DATA-010] describes every source: sensor, platforms, resolution, coverage, tier, API ID, map layers", () => {
    expect(SOURCES.map((s) => s.id).sort()).toEqual(
      [
        "LANDSAT_NRT",
        "MODIS_NRT",
        "MODIS_SP",
        "VIIRS_NOAA20_NRT",
        "VIIRS_NOAA20_SP",
        "VIIRS_NOAA21_NRT",
        "VIIRS_NOAA21_SP",
        "VIIRS_SNPP_NRT",
        "VIIRS_SNPP_SP",
      ].sort(),
    );
    for (const source of SOURCES) {
      expect(source.platforms.length, source.id).toBeGreaterThan(0);
      expect(source.nominal_resolution_m, source.id).toBeGreaterThan(0);
      expect(source.map_layers.length, source.id).toBeGreaterThan(0);
      for (const id of source.knowledge_entries) expect(repoKb.get(id), id).toBeDefined();
    }
  });

  it("[REQ-FR-DATA-010] pairs each sensor with its standard and NRT sources", () => {
    for (const sensor of SENSORS) {
      expect(getSource(sensor.nrt_source).processing).toBe("NRT");
      expect(getSource(sensor.nrt_source).sensor).toBe(sensor.id);
      if (sensor.sp_source !== null) {
        expect(getSource(sensor.sp_source).processing).toBe("SP");
        expect(getSource(sensor.sp_source).sensor).toBe(sensor.id);
      }
    }
    expect(getSensor("landsat").sp_source).toBeNull();
    expect(getSensor("viirs_noaa21").sp_source).toBe("VIIRS_NOAA21_SP");
    expect(DEFAULT_SENSORS).toEqual(["viirs_noaa20", "viirs_noaa21", "viirs_snpp", "modis"]);
  });

  it("[REQ-FR-DATA-002] rejects unknown source and sensor IDs with the valid values", () => {
    expect(() => getSource("VIIRS_X")).toThrow(/valid sources: VIIRS_NOAA20_SP/);
    expect(() => getSensor("goes")).toThrow(/valid sensors: viirs_noaa20/);
  });

  it("[REQ-FR-MAP-003] maps every source to Fire Map layers available in advanced mode", () => {
    const advanced = allowedLayers("advanced");
    for (const source of SOURCES) {
      for (const layer of source.map_layers) expect(advanced.has(layer), layer).toBe(true);
    }
    expect(getSource("MODIS_SP").map_layers).toEqual([
      "fires_modis_terra_sp",
      "fires_modis_aqua_sp",
    ]);
    expect(MAP_CATALOG.layers.has("fires_viirs_noaa21_sp")).toBe(true);
  });
});

describe("coverage", () => {
  it("[REQ-FR-DATA-008] re-keys the map date service to API sources", () => {
    const coverage = coverageFromMapDates(MAP_DATES, TODAY);
    expect(coverage.checked).toBe(true);
    expect(coverage.as_of).toBe(TODAY);
    expect(coverage.ranges.VIIRS_NOAA21_SP).toEqual({ start: "2023-03-01", end: "2026-07-31" });
    expect(coverage.ranges.MODIS_SP).toEqual({ start: "2000-11-01", end: "2026-08-31" });
    expect(coverage.ranges.VIIRS_SNPP_NRT).toEqual({ start: "2019-09-01", end: "2026-11-02" });
    expect(coverage.note).toMatch(/dates the FIRMS Fire Map currently shows/);
  });

  it("[REQ-FR-DATA-008] fetches the keyless map date service", async () => {
    const requested: string[] = [];
    const coverage = await fetchCoverage({
      today: TODAY,
      fetchImpl: async (url) => {
        requested.push(String(url));
        return new Response(JSON.stringify(MAP_DATES), { status: 200 });
      },
    });
    expect(requested).toEqual(["https://firms.modaps.eosdis.nasa.gov/api/map_dates/"]);
    expect(coverage.checked).toBe(true);
    expect(coverage.source).toBe("map_dates_service");
  });

  it.each([
    ["a network failure", async () => Promise.reject(new Error("ECONNRESET"))],
    ["an HTTP error", async () => new Response("busy", { status: 503 })],
    ["a body that is not JSON", async () => new Response("<html>", { status: 200 })],
    ["an unexpected shape", async () => new Response(JSON.stringify([1, 2]), { status: 200 })],
    ["no known products", async () => new Response(JSON.stringify({ x: ["a", "b"] }))],
  ])("[REQ-FR-DATA-008] falls back to the saved snapshot on %s", async (_, fetchImpl) => {
    const coverage = await fetchCoverage({ today: TODAY, fetchImpl });
    expect(coverage.checked).toBe(false);
    expect(coverage.source).toBe("snapshot");
    expect(coverage.as_of).toBe(COVERAGE_SNAPSHOT.retrieved);
    expect(coverage.note).toMatch(/could not be checked/);
    expect(coverage.ranges.MODIS_SP).toEqual({ start: "2000-11-01", end: "2026-08-31" });
  });

  it("[REQ-FR-DATA-008] gives up after the timeout", async () => {
    const coverage = await fetchCoverage({
      today: TODAY,
      timeoutMs: 20,
      fetchImpl: (_url, init) =>
        new Promise((_resolve, reject) => {
          init?.signal?.addEventListener("abort", () => reject(new Error("aborted")));
        }),
    });
    expect(coverage.checked).toBe(false);
  });

  it("[REQ-FR-DATA-008] uses the snapshot for a product the service no longer lists, and says so", () => {
    const partial = { ...(MAP_DATES as Record<string, unknown>) };
    delete partial.jpss2_viirs_c2;
    partial.modis_v6 = ["2000-11-01", "not a date"];
    const coverage = coverageFromMapDates(partial, TODAY);
    expect(coverage.checked).toBe(true);
    expect(coverage.ranges.VIIRS_NOAA21_SP).toEqual({ start: "2023-03-01", end: "2026-07-31" });
    expect(coverage.note).toMatch(/VIIRS_NOAA21_SP/);
    expect(coverage.note).toMatch(/MODIS_SP/);
  });
});
