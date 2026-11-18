import * as z from "zod/v4";
import { SP_VS_NRT_ENTRY } from "../../common/links.js";
import { listSources, SENSORS, summarizeCoverage } from "../../sources/index.js";
import { CoverageOutput, currentCoverage, READ_ONLY_FIRMS } from "../common.js";
import { defineTool } from "../definition.js";

export const listDataSources = defineTool({
  name: "firms_list_data_sources",
  version: "1.0.0",
  title: "List FIRMS fire data sources",
  description: [
    "The FIRMS active-fire sources: for each, the sensor, satellites, nominal pixel size, coverage, processing (standard or near real-time), FIRMS API source ID, Fire Map layers, the knowledge entries that explain it, and the dates FIRMS currently has (from FIRMS's map date service). No MAP_KEY is needed.",
    "Standard-processing (SP) sources come first and are marked `preferred`: use them wherever their dates cover the request. Near real-time sources cover the recent months SP has not reached yet. The URL tools apply this automatically.",
  ].join("\n\n"),
  inputSchema: z.strictObject({}),
  outputSchema: z.object({
    sources: z.array(
      z.object({
        id: z.string(),
        label: z.string(),
        sensor: z.string(),
        processing: z.enum(["SP", "NRT"]),
        preferred: z.boolean(),
        instrument: z.string(),
        platforms: z.array(z.string()),
        nominal_resolution_m: z.number(),
        coverage: z.string(),
        map_layers: z.array(z.string()),
        knowledge_entries: z.array(z.string()),
        dates: z.object({ start: z.string(), end: z.string() }),
      }),
    ),
    sensors: z.array(
      z.object({
        id: z.string(),
        label: z.string(),
        sp_source: z.string().nullable(),
        nrt_source: z.string(),
        default: z.boolean(),
      }),
    ),
    coverage: CoverageOutput,
    notes: z.array(z.string()),
  }),
  annotations: READ_ONLY_FIRMS,
  async run(_input, signal) {
    const coverage = await currentCoverage(signal);
    return {
      sources: listSources().map(({ map_dates_key: _key, ...source }) => ({
        ...source,
        dates: coverage.ranges[source.id],
      })),
      sensors: SENSORS.map((s) => ({
        id: s.id,
        label: s.label,
        sp_source: s.sp_source,
        nrt_source: s.nrt_source,
        default: s.default,
      })),
      coverage: summarizeCoverage(coverage),
      notes: [
        `Standard-processing sources are preferred wherever they cover the dates (FAQ entry ${SP_VS_NRT_ENTRY}).`,
      ],
    };
  },
});
