import { readFileSync } from "node:fs";
import type { Client } from "@modelcontextprotocol/client";
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { MAP_KEY_PLACEHOLDER } from "../../../src/common/index.js";
import { createServer } from "../../../src/server/create.js";
import { INSTRUCTIONS } from "../../../src/server/instructions.js";
import { TOOLS } from "../../../src/tools/index.js";
import { connect } from "../../helpers.js";
import { repoKb } from "../knowledge/fixtures.js";
import { MAP_DATES } from "../urls/fixtures.js";

const TOOL_NAMES = [
  "firms_search_knowledge",
  "firms_get_knowledge_entry",
  "firms_list_knowledge_topics",
  "firms_build_fire_map_url",
  "firms_build_api_url",
  "firms_build_kml_footprint_url",
  "firms_list_data_sources",
];
/** Tools that ask FIRMS's map date service for coverage. */
const OPEN_WORLD = ["firms_build_fire_map_url", "firms_build_api_url", "firms_list_data_sources"];
const BOX = { west: -119.2, south: 33.8, east: -117.6, north: 34.6 };

let client: Client;
let mapDates: () => Promise<Response>;

beforeAll(async () => {
  client = await connect(createServer());
});

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date("2026-11-18T15:00:00Z"));
  mapDates = async () => new Response(JSON.stringify(MAP_DATES), { status: 200 });
  vi.stubGlobal("fetch", async (url: string) => {
    expect(url).toBe("https://firms.modaps.eosdis.nasa.gov/api/map_dates/");
    return mapDates();
  });
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

// biome-ignore lint/suspicious/noExplicitAny: structured content is checked field by field
async function call(name: string, args: Record<string, unknown> = {}): Promise<any> {
  const result = await client.callTool({ name, arguments: args });
  if (result.isError) {
    throw new Error((result.content as { text: string }[])[0]?.text ?? "tool error");
  }
  expect(JSON.parse((result.content as { text: string }[])[0]?.text ?? "")).toEqual(
    result.structuredContent,
  );
  return result.structuredContent;
}

describe("tool list", () => {
  it("[REQ-FR-MCP-008] lists the seven firms_ tools in a fixed order", async () => {
    const { tools } = await client.listTools();
    expect(tools.map((t) => t.name)).toEqual(TOOL_NAMES);
    expect(TOOLS.map((t) => t.name)).toEqual(TOOL_NAMES);
  });

  it("[REQ-NFR-002] [REQ-NFR-003] declares titles, output schemas, and annotations", async () => {
    const { tools } = await client.listTools();
    for (const tool of tools) {
      expect(tool.title, tool.name).toBeTruthy();
      expect(tool.outputSchema?.type, tool.name).toBe("object");
      expect(tool.annotations, tool.name).toEqual({
        readOnlyHint: true,
        destructiveHint: false,
        idempotentHint: true,
        openWorldHint: OPEN_WORLD.includes(tool.name),
      });
    }
  });

  it("[REQ-SEC-002] [REQ-FR-AUTH-002] [REQ-FR-URL-002] accepts no MAP_KEY and needs no authentication", async () => {
    const { tools } = await client.listTools();
    for (const tool of tools) {
      const names = Object.keys(tool.inputSchema.properties ?? {});
      expect(
        names.filter((n) => /key|token|secret/i.test(n)),
        tool.name,
      ).toEqual([]);
      expect(tool.inputSchema.additionalProperties, tool.name).toBe(false);
    }
    await expect(
      call("firms_build_api_url", { request: "map_key_status", map_key: "x" }),
    ).rejects.toThrow();
  });

  it("[REQ-NFR-004] bounds result sizes", async () => {
    await expect(call("firms_search_knowledge", { query: "fire", limit: 11 })).rejects.toThrow();
    await expect(
      call("firms_get_knowledge_entry", { entry_ids: Array(11).fill("x") }),
    ).rejects.toThrow();
  });
});

describe("knowledge tools", () => {
  it("[REQ-FR-KB-005] returns ranked entries with FIRMS's text in full", async () => {
    const result = await call("firms_search_knowledge", { query: "VIIRS detection confidence" });
    expect(result.total).toBe(3);
    const [first] = result.results;
    const entry = repoKb.get(first.id);
    expect(first.body).toBe(entry?.body);
    expect(first).toMatchObject({
      title: entry?.title,
      source_url: entry?.source_url,
      retrieved: entry?.retrieved,
      content_sha256: entry?.content_sha256,
      status: "current",
    });
    expect(first.score).toBeGreaterThan(0);
    expect(typeof first.snippet).toBe("string");
  });

  it("[REQ-FR-KB-005] says so when nothing matches", async () => {
    const result = await call("firms_search_knowledge", { query: "zzzqqq" });
    expect(result.results).toEqual([]);
    expect(result.suggestion).toMatch(/firms_list_knowledge_topics/);
  });

  it("[REQ-FR-KB-006] gets entries by ID and suggests IDs for unknown ones", async () => {
    const id = "faq.getting-started.what-are-the-key-differences-between-urt-rt-nrt-and-standard";
    const result = await call("firms_get_knowledge_entry", {
      entry_ids: [id, "faq.getting-started.what-are-the-key-differences"],
    });
    expect(result.entries.map((e: { id: string }) => e.id)).toEqual([id]);
    expect(result.entries[0].body).toBe(repoKb.get(id)?.body);
    expect(result.not_found).toEqual([
      {
        id: "faq.getting-started.what-are-the-key-differences",
        suggestions: expect.arrayContaining([id]),
      },
    ]);
  });

  it("[REQ-FR-KB-007] lists sections, and a section's entries", async () => {
    const all = await call("firms_list_knowledge_topics");
    expect(all.total_entries).toBe(repoKb.ordered().length);
    expect(all.sections.map((s: { id: string }) => s.id)).toContain("caveats");
    expect(all.sections[0].entries).toBeUndefined();
    expect(all.sources.length).toBeGreaterThan(0);
    const caveats = await call("firms_list_knowledge_topics", { section: "caveats" });
    expect(caveats.sections).toHaveLength(1);
    expect(caveats.sections[0].entries.length).toBe(caveats.sections[0].entry_count);
    await expect(call("firms_list_knowledge_topics", { section: "nope" })).rejects.toThrow(
      /unknown section "nope"; sections: .*caveats/,
    );
  });

  it("[REQ-FR-KB-010] exposes the index, each entry, and the source catalog as resources", async () => {
    const { resources } = await client.listResources();
    expect(resources.map((r) => r.uri)).toEqual(
      expect.arrayContaining(["firms://knowledge/index", "firms://sources"]),
    );
    const { resourceTemplates } = await client.listResourceTemplates();
    expect(resourceTemplates.map((t) => t.uriTemplate)).toContain("firms://knowledge/{entry_id}");

    const id = "faq.getting-started.what-is-the-detection-confidence";
    const read = await client.readResource({ uri: `firms://knowledge/${id}` });
    const text = (read.contents[0] as { text: string }).text;
    const entry = repoKb.get(id);
    expect(text.startsWith(`# ${entry?.title}\n\n${entry?.body}`)).toBe(true);
    expect(text).toContain(`Source: ${entry?.source_url} (retrieved ${entry?.retrieved})`);

    const index = JSON.parse(
      (
        (await client.readResource({ uri: "firms://knowledge/index" })).contents[0] as {
          text: string;
        }
      ).text,
    );
    expect(index.entry_uri_template).toBe("firms://knowledge/{entry_id}");
    const sources = JSON.parse(
      ((await client.readResource({ uri: "firms://sources" })).contents[0] as { text: string })
        .text,
    );
    expect(sources.sources[0].processing).toBe("SP");
    await expect(client.readResource({ uri: "firms://knowledge/no.such.entry" })).rejects.toThrow(
      /no knowledge entry/i,
    );
  });
});

describe("URL tools", () => {
  it("[REQ-FR-MAP-007] [REQ-FR-DATA-008] builds Fire Map links from live coverage", async () => {
    const result = await call("firms_build_fire_map_url", {
      area: BOX,
      sensors: ["viirs_noaa20"],
      start_date: "2026-07-30",
      end_date: "2026-08-01",
    });
    expect(result.links.map((l: { layers: string[] }) => l.layers[0])).toEqual([
      "fires_viirs_noaa20_sp",
      "fires_viirs_noaa20",
    ]);
    expect(result.coverage.checked).toBe(true);
    expect(result.limitations).toMatch(/cannot fetch, summarize, count, or chart/);
  });

  it("[REQ-FR-DATA-008] still answers when the map date service fails, and says so", async () => {
    mapDates = async () => new Response("busy", { status: 503 });
    const result = await call("firms_build_fire_map_url", { start_date: "2026-07-01" });
    expect(result.coverage).toMatchObject({ checked: false, source: "snapshot" });
    expect(result.links).toHaveLength(1);
  });

  it("[REQ-FR-URL-001] [REQ-FR-URL-002] [REQ-FR-URL-003] builds area API URLs with [MAP_KEY]", async () => {
    const result = await call("firms_build_api_url", {
      request: "area",
      area: BOX,
      sensors: ["modis"],
      start_date: "2026-08-30",
      end_date: "2026-09-01",
    });
    expect(result.urls.map((u: { source: string; url: string }) => [u.source, u.url])).toEqual([
      [
        "MODIS_SP",
        "https://firms.modaps.eosdis.nasa.gov/api/area/csv/[MAP_KEY]/MODIS_SP/-119.2,33.8,-117.6,34.6/2/2026-08-30",
      ],
      [
        "MODIS_NRT",
        "https://firms.modaps.eosdis.nasa.gov/api/area/csv/[MAP_KEY]/MODIS_NRT/-119.2,33.8,-117.6,34.6/1/2026-09-01",
      ],
    ]);
    expect(result.map_key.placeholder).toBe(MAP_KEY_PLACEHOLDER);
    expect(result.limitations).toMatch(/cannot fetch/);
    expect(result.coverage.checked).toBe(true);
  });

  it("[REQ-FR-URL-004] builds the data_availability and MAP_KEY status URLs", async () => {
    const availability = await call("firms_build_api_url", {
      request: "data_availability",
      source: "VIIRS_NOAA21_SP",
    });
    expect(availability.urls[0].url).toBe(
      "https://firms.modaps.eosdis.nasa.gov/api/data_availability/csv/[MAP_KEY]/VIIRS_NOAA21_SP",
    );
    expect(availability.related.archive_download_page).toBe(
      "https://firms.modaps.eosdis.nasa.gov/download/",
    );
    const status = await call("firms_build_api_url", { request: "map_key_status" });
    expect(status.urls[0].url).toBe(
      "https://firms.modaps.eosdis.nasa.gov/mapserver/mapkey_status/?MAP_KEY=[MAP_KEY]",
    );
  });

  it("[REQ-FR-KB-013] answers missing-data questions from the saved table, with its date and the live page", async () => {
    const saved = JSON.parse(readFileSync("knowledge/reference/missing-data.json", "utf8"));
    const result = await call("firms_build_api_url", {
      request: "missing_data",
      sensors: ["viirs_snpp"],
      start_date: "2026-07-10",
      end_date: "2026-07-20",
    });
    expect(result.missing_data.retrieved).toBe(saved.retrieved);
    expect(result.missing_data.page_url).toBe(
      "https://firms.modaps.eosdis.nasa.gov/api/missing_data/",
    );
    expect(result.missing_data.standard.map((g: { date: string }) => g.date)).toEqual([
      "2026-07-16",
      "2026-07-15",
      "2026-07-14",
      "2026-07-13",
      "2026-07-12",
      "2026-07-11",
    ]);
    expect(result.missing_data.note).toMatch(/saved on 2026-11-18/);
    expect(result.urls[0].url).toBe("https://firms.modaps.eosdis.nasa.gov/api/missing_data/");
  });

  it("[REQ-FR-KB-013] flags known missing days inside an area request", async () => {
    const result = await call("firms_build_api_url", {
      request: "area",
      area: "world",
      sensors: ["viirs_snpp"],
      start_date: "2026-07-14",
      end_date: "2026-07-18",
    });
    expect(result.notes.join("\n")).toMatch(
      /missing-data table \(saved 2026-11-18\) lists 2026-07-14, 2026-07-15, 2026-07-16 as missing from the standard-processing archive for VIIRS Suomi NPP/,
    );
  });

  it("[REQ-FR-DATA-002] returns an error that says how to fix the input", async () => {
    await expect(
      call("firms_build_api_url", { request: "area", area: "world", start_date: "2026-11-30" }),
    ).rejects.toThrow(/2026-11-30 is in the future \(today is 2026-11-18 UTC\)/);
    await expect(call("firms_build_api_url", { request: "area" })).rejects.toThrow(
      /area is required/,
    );
  });

  it("[REQ-FR-DATA-011] builds KML footprint links", async () => {
    const result = await call("firms_build_kml_footprint_url", {
      region: "canada",
      period: "24h",
      sensor: "viirs_noaa21",
    });
    expect(result.url).toBe(
      "https://firms.modaps.eosdis.nasa.gov/api/kml_fire_footprints/?region=canada&date_span=24h&sensor=noaa-21-viirs-c2",
    );
    expect(result.downloads_file).toBe(true);
    const { tools } = await client.listTools();
    expect(tools.find((t) => t.name === "firms_build_kml_footprint_url")?.description).toMatch(
      /only when the user mentions GIS, footprints, Google Earth, or QGIS/,
    );
  });

  it("[REQ-FR-DATA-015] [REQ-FR-DATA-010] lists sources SP first, with current dates", async () => {
    const result = await call("firms_list_data_sources");
    expect(result.sources[0]).toMatchObject({ id: "VIIRS_NOAA20_SP", preferred: true });
    expect(result.sources.find((s: { id: string }) => s.id === "VIIRS_NOAA21_SP").dates).toEqual({
      start: "2023-03-01",
      end: "2026-07-31",
    });
    expect(result.sensors.map((s: { id: string }) => s.id)).toEqual([
      "viirs_noaa20",
      "viirs_noaa21",
      "viirs_snpp",
      "modis",
      "landsat",
    ]);
    expect(result.coverage.checked).toBe(true);
  });
});

describe("server instructions", () => {
  it("[REQ-FR-MCP-002] [REQ-FR-MCP-009] set the rules the tools cannot enforce", () => {
    for (const phrase of [
      "not an official NASA product",
      "does not answer science questions",
      "Do not use for the preservation of life or property",
      "faq.getting-started.what-are-the-key-differences-between-urt-rt-nrt-and-standard",
      "[MAP_KEY]",
      "stays in the conversation transcript",
      "Never estimate",
      "GIS",
      "UTC",
      "LONGITUDE FIRST",
    ]) {
      expect(INSTRUCTIONS, phrase).toContain(phrase);
    }
    for (const name of TOOL_NAMES) expect(INSTRUCTIONS, name).toContain(name);
  });
});

describe("tool catalog", () => {
  it("[REQ-DOC-002] documents every tool with its version and parameters", () => {
    const doc = readFileSync("docs/design/TOOLS.md", "utf8");
    for (const tool of TOOLS) {
      expect(doc, tool.name).toContain(`### \`${tool.name}\` (v${tool.version})`);
      expect(doc, tool.name).toContain(`| \`${tool.name}\` | ${tool.version} |`);
      const section = doc.split(`### \`${tool.name}\``)[1]?.split(/\n### /)[0] ?? "";
      for (const parameter of Object.keys(tool.inputSchema.shape)) {
        expect(section, `${tool.name}.${parameter}`).toContain(`\`${parameter}\``);
      }
    }
  });
});
