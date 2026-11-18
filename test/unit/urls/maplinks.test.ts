import { describe, expect, it } from "vitest";
import { LIMITATIONS } from "../../../src/common/index.js";
import { allowedLayers, buildFireMapUrls, MAP_CATALOG } from "../../../src/maplinks/index.js";
import { COVERAGE, TODAY } from "./fixtures.js";

const MAP = "https://firms.modaps.eosdis.nasa.gov/map/?utm_source=firms-mcp&utm_medium=mcp";
const BOX = { west: -119.2, south: 33.8, east: -117.6, north: 34.6 };

function build(input: Parameters<typeof buildFireMapUrls>[0] = {}) {
  return buildFireMapUrls(input, COVERAGE, TODAY);
}

describe("Fire Map links", () => {
  it("[REQ-FR-MAP-001] defaults to the map's own view: Basic mode, last 24 hours", () => {
    const result = build();
    expect(result.links.map((l) => l.url)).toEqual([
      `${MAP}#d:24hrs;l:fire_layers_basic,country-outline,earth;@0,0,3.0z`,
    ]);
    expect(result.limitations).toBe(LIMITATIONS);
  });

  it("[REQ-FR-MAP-001] frames an area of interest", () => {
    const [link] = build({ area: BOX, period: "7days" }).links;
    expect(link?.url).toBe(
      `${MAP}#d:7days;l:fire_layers_basic,country-outline,earth;i:-119.2,33.8,-117.6,34.6`,
    );
  });

  it("[REQ-FR-MAP-001] centers on a point at a zoom", () => {
    const [link] = build({ center: { longitude: -118.5, latitude: 34.1 }, zoom: 7 }).links;
    expect(link?.url).toMatch(/;@-118\.5,34\.1,7\.0z$/);
  });

  it("[REQ-FR-MAP-007] uses standard-processing layers for past dates standard data cover", () => {
    const result = build({ area: BOX, start_date: "2026-07-01", end_date: "2026-07-03" });
    expect(result.links.map((l) => l.url)).toEqual([
      `${MAP}#m:advanced;d:2026-07-01..2026-07-03;l:fires_viirs_noaa20_sp,fires_viirs_noaa21_sp,fires_viirs_snpp_sp,fires_modis_terra_sp,fires_modis_aqua_sp,country-outline,earth;i:-119.2,33.8,-117.6,34.6`,
    ]);
    expect(result.links[0]?.description).toMatch(/standard processing/);
  });

  it("[REQ-FR-MAP-007] splits at the end of standard coverage into an SP link and an NRT link", () => {
    const result = build({
      area: BOX,
      sensors: ["viirs_noaa20"],
      start_date: "2026-07-30",
      end_date: "2026-08-02",
    });
    expect(result.links.map((l) => [l.start_date, l.end_date, l.layers])).toEqual([
      ["2026-07-30", "2026-07-31", ["fires_viirs_noaa20_sp", "country-outline", "earth"]],
      ["2026-08-01", "2026-08-02", ["fires_viirs_noaa20", "country-outline", "earth"]],
    ]);
    expect(result.notes.join("\n")).toMatch(
      /VIIRS NOAA-20: standard-processing data currently end on 2026-07-31/,
    );
  });

  it("[REQ-FR-MAP-007] cuts links where any chosen sensor changes between SP and NRT", () => {
    const result = build({
      sensors: ["modis", "viirs_noaa20"],
      start_date: "2026-08-30",
      end_date: "2026-09-02",
    });
    expect(result.links.map((l) => [l.dates, l.layers.slice(0, 3)])).toEqual([
      [
        "2026-08-30..2026-08-31",
        ["fires_modis_terra_sp", "fires_modis_aqua_sp", "fires_viirs_noaa20"],
      ],
      ["2026-09-01..2026-09-02", ["fires_modis_terra", "fires_modis_aqua", "fires_viirs_noaa20"]],
    ]);
  });

  it("[REQ-FR-MAP-007] uses NRT for a sensor with no standard layer and says so", () => {
    const result = build({ area: BOX, sensors: ["landsat"], start_date: "2026-07-01" });
    expect(result.links[0]?.layers[0]).toBe("fires_landsat_landsat");
    expect(result.notes.join("\n")).toMatch(/Landsat.*no standard-processing product/);
    expect(result.links[0]?.description).toMatch(/near real-time/);
  });

  it("[REQ-FR-MAP-007] uses NRT layers for recent periods, with a note", () => {
    const result = build({ sensors: ["viirs_noaa21"], period: "72hrs" });
    expect(result.links[0]?.url).toBe(
      `${MAP}#m:advanced;d:72hrs;l:fires_viirs_noaa21,country-outline,earth;@0,0,3.0z`,
    );
    expect(result.notes.join("\n")).toMatch(/standard-processing data cannot exist yet/);
  });

  it("[REQ-FR-MAP-002] validates layers against the catalog and the mode", () => {
    expect(() => build({ extra_layers: ["no_such_layer"] })).toThrow(
      /unknown Fire Map layer\(s\): no_such_layer/,
    );
    expect(() => build({ mode: "basic", sensors: ["modis"] })).toThrow(
      /not available in basic mode.*mode 'advanced'/,
    );
    expect(() => build({ basemap: "country-outline" })).toThrow(/not a basemap/);
    expect(() => build({ mode: "smoke", sensors: ["modis"], start_date: "2026-07-01" })).toThrow(
      /standard-processing layers.*advanced mode/,
    );
  });

  it("[REQ-FR-MAP-002] always ends the layer list with a basemap", () => {
    for (const link of build({ basemap: "street", overlays: [] }).links) {
      expect(link.layers.at(-1)).toBe("street");
    }
  });

  it("[REQ-FR-MAP-002] knows the renamed Basic-mode fire layer and the NOAA-21 layers", () => {
    expect(MAP_CATALOG.layers.has("fires_all")).toBe(false);
    expect(allowedLayers("basic").has("fire_layers_basic")).toBe(true);
    expect(allowedLayers("advanced").has("fires_viirs_noaa21_sp")).toBe(true);
  });

  it("[REQ-FR-DATA-002] validates dates, places, and zoom", () => {
    expect(() => build({ start_date: "2026-11-19" })).toThrow(/in the future/);
    expect(() => build({ period: "24hrs", start_date: "2026-07-01" })).toThrow(
      /either a period or start_date/,
    );
    expect(() => build({ area: BOX, center: { longitude: 0, latitude: 0 } })).toThrow(
      /either an area or a center/,
    );
    expect(() => build({ zoom: 20 })).toThrow(/zoom must be between 1 and 16/);
  });

  it("[REQ-FR-MAP-004] supports the US/Canada map and its zoom limits", () => {
    const result = build({ map: "us-canada", center: { longitude: -100, latitude: 45 }, zoom: 5 });
    expect(result.links[0]?.url).toMatch(
      /^https:\/\/firms\.modaps\.eosdis\.nasa\.gov\/usfs\/map\/\?utm_source=firms-mcp&utm_medium=mcp#/,
    );
    expect(() => build({ map: "us-canada", zoom: 3 })).toThrow(/zoom must be between 4 and 16/);
  });

  it("[REQ-FR-MAP-005] adds referral parameters unless turned off", () => {
    const [link] = build({ referral: false }).links;
    expect(link?.url.startsWith("https://firms.modaps.eosdis.nasa.gov/map/#")).toBe(true);
  });

  it("[REQ-FR-MAP-006] describes each link in plain language", () => {
    const [link] = build({ area: BOX, sensors: ["modis"], start_date: "2026-07-01" }).links;
    expect(link?.description).toBe(
      "Opens the FIRMS Fire Map (Advanced Mode) showing SP: MODIS / Terra [1km], SP: MODIS / Aqua [1km] (standard processing) for 2026-07-01 (UTC) over the area west -119.2, south 33.8, east -117.6, north 34.6 (the map draws this box), on the Blue Marble basemap with Coastlines / Borders / Roads - BASIC. The map, not this server, renders FIRMS data; times are UTC.",
    );
  });
});
