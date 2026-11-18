import { describe, expect, it } from "vitest";
import {
  buildAreaUrls,
  buildKmlFootprintUrl,
  dataAvailabilityUrl,
  mapKeyStatusUrl,
} from "../../../src/apiurls/index.js";
import {
  LIMITATIONS,
  MAP_KEY_PLACEHOLDER,
  MAP_KEY_SIGNUP_URL,
  UrlBuilderError,
} from "../../../src/common/index.js";
import { COVERAGE, TODAY } from "./fixtures.js";

const API = "https://firms.modaps.eosdis.nasa.gov/api/area/csv/[MAP_KEY]";
const BOX = { west: -119.2, south: 33.8, east: -117.6, north: 34.6 };

function build(input: Parameters<typeof buildAreaUrls>[0]) {
  return buildAreaUrls(input, COVERAGE, TODAY);
}

describe("area API URLs, standard data first", () => {
  it("[REQ-FR-URL-001] uses the standard source for dates standard data covers", () => {
    const result = build({
      area: "world",
      sensors: ["viirs_noaa20"],
      start_date: "2026-07-01",
      end_date: "2026-07-03",
    });
    expect(result.requests).toEqual([
      {
        sensor: "viirs_noaa20",
        source: "VIIRS_NOAA20_SP",
        processing: "SP",
        label: "VIIRS NOAA-20, standard processing, 2026-07-01 to 2026-07-03",
        start_date: "2026-07-01",
        end_date: "2026-07-03",
        day_range: 3,
        url: `${API}/VIIRS_NOAA20_SP/world/3/2026-07-01`,
      },
    ]);
  });

  it("[REQ-FR-URL-001] splits at the end of standard coverage into labelled SP and NRT URLs", () => {
    const result = build({
      area: BOX,
      sensors: ["viirs_noaa21"],
      start_date: "2026-07-29",
      end_date: "2026-08-02",
    });
    expect(result.requests.map((r) => [r.processing, r.start_date, r.end_date, r.url])).toEqual([
      [
        "SP",
        "2026-07-29",
        "2026-07-31",
        `${API}/VIIRS_NOAA21_SP/-119.2,33.8,-117.6,34.6/3/2026-07-29`,
      ],
      [
        "NRT",
        "2026-08-01",
        "2026-08-02",
        `${API}/VIIRS_NOAA21_NRT/-119.2,33.8,-117.6,34.6/2/2026-08-01`,
      ],
    ]);
    expect(result.requests[1]?.label).toBe(
      "VIIRS NOAA-21, near real-time (NRT), 2026-08-01 to 2026-08-02",
    );
    expect(result.notes.join("\n")).toMatch(
      /VIIRS NOAA-21: standard-processing data currently end on 2026-07-31/,
    );
  });

  it("[REQ-FR-URL-001] uses NRT after standard coverage, with a note", () => {
    const result = build({
      area: "world",
      sensors: ["modis"],
      start_date: "2026-10-01",
      end_date: "2026-10-01",
    });
    expect(result.requests.map((r) => r.url)).toEqual([`${API}/MODIS_NRT/world/1/2026-10-01`]);
    expect(result.notes.join("\n")).toMatch(/MODIS.*2026-08-31.*provisional/s);
    expect(result.notes.join("\n")).toMatch(
      /faq\.getting-started\.what-are-the-key-differences-between-urt-rt-nrt-and-standard/,
    );
  });

  it("[REQ-FR-URL-001] says so for a sensor with no standard product", () => {
    const result = build({
      area: BOX,
      sensors: ["landsat"],
      start_date: "2026-07-01",
      end_date: "2026-07-01",
    });
    expect(result.requests.map((r) => r.source)).toEqual(["LANDSAT_NRT"]);
    expect(result.notes.join("\n")).toMatch(/Landsat.*no standard-processing product/);
    expect(result.notes.join("\n")).toMatch(/US\/Canada only/);
  });

  it("[REQ-FR-URL-001] uses NRT for the most recent days, where standard data cannot exist yet", () => {
    const result = build({ area: "world", sensors: ["viirs_noaa20"], recent_days: 2 });
    expect(result.requests).toEqual([
      expect.objectContaining({
        source: "VIIRS_NOAA20_NRT",
        start_date: "2026-11-17",
        end_date: "2026-11-18",
        day_range: 2,
        url: `${API}/VIIRS_NOAA20_NRT/world/2`,
      }),
    ]);
    expect(result.notes.join("\n")).toMatch(/standard-processing data cannot exist yet/);
  });

  it("[REQ-FR-URL-001] builds no recent-days URL for a sensor whose NRT data have stopped", () => {
    const result = build({ area: "world", recent_days: 3 });
    expect(result.requests.map((r) => r.source)).toEqual([
      "VIIRS_NOAA20_NRT",
      "VIIRS_NOAA21_NRT",
      "MODIS_NRT",
    ]);
    expect(result.notes.join("\n")).toMatch(
      /VIIRS Suomi NPP: no data for 2026-11-16 to 2026-11-18.*\n.*VIIRS Suomi NPP: no URL was built/,
    );
  });

  it("[REQ-FR-URL-001] queries the four global sensors when none is chosen", () => {
    const result = build({ area: "world", start_date: "2026-06-01", end_date: "2026-06-01" });
    expect(result.requests.map((r) => r.source)).toEqual([
      "VIIRS_NOAA20_SP",
      "VIIRS_NOAA21_SP",
      "VIIRS_SNPP_SP",
      "MODIS_SP",
    ]);
  });

  it("[REQ-FR-URL-001] reports dates no product covers instead of building a URL for them", () => {
    const result = build({
      area: "world",
      sensors: ["viirs_snpp"],
      start_date: "2026-11-01",
      end_date: "2026-11-05",
    });
    expect(result.requests.map((r) => [r.source, r.start_date, r.end_date])).toEqual([
      ["VIIRS_SNPP_NRT", "2026-11-01", "2026-11-02"],
    ]);
    expect(result.notes.join("\n")).toMatch(
      /VIIRS Suomi NPP: no data for 2026-11-03 to 2026-11-05/,
    );
  });

  it("[REQ-FR-URL-001] honours an explicit request for NRT and says standard data are preferred", () => {
    const result = build({
      area: "world",
      sensors: ["viirs_noaa20"],
      start_date: "2026-07-30",
      end_date: "2026-08-01",
      processing: "nrt",
    });
    expect(result.requests.map((r) => r.source)).toEqual(["VIIRS_NOAA20_NRT"]);
    expect(result.notes.join("\n")).toMatch(
      /standard-processing data exist for 2026-07-30 to 2026-07-31 and are preferred/,
    );
  });

  it("[REQ-FR-URL-001] splits long periods into requests of at most five days (the API limit)", () => {
    const result = build({
      area: "world",
      sensors: ["modis"],
      start_date: "2026-06-01",
      end_date: "2026-06-12",
    });
    expect(result.requests.map((r) => [r.start_date, r.day_range])).toEqual([
      ["2026-06-01", 5],
      ["2026-06-06", 5],
      ["2026-06-11", 2],
    ]);
  });

  it("[REQ-FR-URL-002] puts [MAP_KEY] in every URL and says where to get a key and where it goes", () => {
    const result = build({ area: "world", recent_days: 1 });
    for (const request of result.requests) expect(request.url).toContain(MAP_KEY_PLACEHOLDER);
    expect(result.map_key.placeholder).toBe("[MAP_KEY]");
    expect(result.map_key.get_a_key).toBe(MAP_KEY_SIGNUP_URL);
    expect(result.map_key.where_it_goes).toMatch(/Replace \[MAP_KEY\]/);
  });

  it("[REQ-FR-URL-003] states what the server cannot do with the URLs", () => {
    const result = build({ area: "world", recent_days: 1 });
    expect(result.limitations).toBe(LIMITATIONS);
    expect(LIMITATIONS).toMatch(/cannot fetch, summarize, count, or chart/);
  });

  it("[REQ-FR-URL-004] offers the data_availability URL and the related FIRMS pages", () => {
    const { related } = build({ area: "world", recent_days: 1 });
    expect(related).toEqual({
      data_availability_url:
        "https://firms.modaps.eosdis.nasa.gov/api/data_availability/csv/[MAP_KEY]/ALL",
      missing_data_page: "https://firms.modaps.eosdis.nasa.gov/api/missing_data/",
      archive_download_page: "https://firms.modaps.eosdis.nasa.gov/download/",
      map_key_page: "https://firms.modaps.eosdis.nasa.gov/api/map_key/",
    });
    expect(dataAvailabilityUrl("VIIRS_NOAA21_SP")).toBe(
      "https://firms.modaps.eosdis.nasa.gov/api/data_availability/csv/[MAP_KEY]/VIIRS_NOAA21_SP",
    );
    expect(mapKeyStatusUrl()).toBe(
      "https://firms.modaps.eosdis.nasa.gov/mapserver/mapkey_status/?MAP_KEY=[MAP_KEY]",
    );
  });

  it("[REQ-FR-URL-001] reports how coverage was determined", () => {
    const result = build({ area: "world", recent_days: 1 });
    expect(result.coverage).toEqual({
      checked: true,
      as_of: TODAY,
      source: "map_dates_service",
      note: COVERAGE.note,
    });
  });
});

describe("input validation", () => {
  it.each([
    [{ start_date: "2026-11-19" }, /2026-11-19 is in the future \(today is 2026-11-18 UTC\)/],
    [{ start_date: "2026-07-05", end_date: "2026-07-01" }, /start_date is after end_date/],
    [{ start_date: "2026-13-01" }, /start_date must be a real date in YYYY-MM-DD form/],
    [{ start_date: "07/01/2026" }, /start_date must be a real date in YYYY-MM-DD form/],
    [{ recent_days: 6 }, /recent_days must be a whole number from 1 to 5/],
    [{ recent_days: 2, start_date: "2026-07-01" }, /either recent_days or start_date/],
    [
      { start_date: "2026-01-01", end_date: "2026-03-01" },
      /at most 31 days.*https:\/\/firms\.modaps\.eosdis\.nasa\.gov\/download\//,
    ],
  ])("[REQ-FR-DATA-002] rejects %o", (dates, message) => {
    expect(() => build({ area: "world", ...dates })).toThrow(message);
  });

  it("[REQ-FR-DATA-002] requires a date choice", () => {
    expect(() => build({ area: "world" })).toThrow(/give recent_days.*or start_date/);
  });

  it.each([
    [{ west: -117, south: 33, east: -119, north: 34 }, /west must be less than east.*antimeridian/],
    [{ west: -119, south: 35, east: -117, north: 34 }, /south must be less than north/],
    [{ west: -190, south: 33, east: -117, north: 34 }, /west must be between -180 and 180/],
    [{ west: -119, south: 33, east: -117, north: 95 }, /north must be between -90 and 90/],
    [{ west: Number.NaN, south: 33, east: -117, north: 34 }, /west must be a number/],
  ])("[REQ-FR-DATA-002] rejects the area %o", (area, message) => {
    expect(() => build({ area, recent_days: 1 })).toThrow(message);
  });

  it("[REQ-FR-DATA-002] raises UrlBuilderError for unknown sensors", () => {
    expect(() => build({ area: "world", sensors: ["goes" as "modis"], recent_days: 1 })).toThrow(
      UrlBuilderError,
    );
  });
});

describe("KML fire footprints", () => {
  it("[REQ-FR-DATA-011] builds the keyless download link and says it downloads a file", () => {
    const result = buildKmlFootprintUrl({
      region: "canada",
      period: "48h",
      sensor: "viirs_noaa20",
    });
    expect(result.url).toBe(
      "https://firms.modaps.eosdis.nasa.gov/api/kml_fire_footprints/?region=canada&date_span=48h&sensor=noaa-20-viirs-c2",
    );
    expect(result.url).not.toContain(MAP_KEY_PLACEHOLDER);
    expect(result).toMatchObject({
      region_label: "Canada",
      period_label: "48 hours",
      sensor_label: "VIIRS NOAA-20",
      downloads_file: true,
      limitations: LIMITATIONS,
    });
    expect(result.note).toMatch(/downloads a KML file.*Google Earth or QGIS/);
    expect(result.note).toMatch(/near real-time/);
  });

  it("[REQ-FR-DATA-011] offers Landsat only for Canada and the contiguous US and Hawaii", () => {
    expect(
      buildKmlFootprintUrl({ region: "usa_contiguous_and_hawaii", period: "7d", sensor: "landsat" })
        .url,
    ).toMatch(/sensor=landsat$/);
    expect(() =>
      buildKmlFootprintUrl({ region: "europe", period: "24h", sensor: "landsat" }),
    ).toThrow(/Landsat footprints are only offered for canada and usa_contiguous_and_hawaii/);
  });

  it("[REQ-FR-DATA-002] rejects unknown regions and periods with the valid values", () => {
    expect(() =>
      buildKmlFootprintUrl({ region: "mars" as "canada", period: "24h", sensor: "modis" }),
    ).toThrow(/valid regions: canada, alaska/);
    expect(() =>
      buildKmlFootprintUrl({ region: "canada", period: "30d" as "7d", sensor: "modis" }),
    ).toThrow(/valid periods: 24h, 48h, 72h, 7d/);
  });
});
