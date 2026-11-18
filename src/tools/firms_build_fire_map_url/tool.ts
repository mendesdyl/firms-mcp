import * as z from "zod/v4";
import { buildFireMapUrls, PERIODS } from "../../maplinks/index.js";
import {
  BoxInput,
  CoverageOutput,
  currentCoverage,
  IsoDateInput,
  ModeInput,
  READ_ONLY_FIRMS,
  SensorsInput,
  today,
} from "../common.js";
import { defineTool } from "../definition.js";

export const buildFireMapUrl = defineTool({
  name: "firms_build_fire_map_url",
  version: "1.0.0",
  title: "Build a FIRMS Fire Map link",
  description: [
    "Build links that open the FIRMS Fire Map (global, or the US/Canada map) on a place, dates, and fire layers, each with a plain-language `description` of what it will show. No MAP_KEY is needed.",
    "Standard data first: for past dates, each sensor shows its standard-processing (SP) layer where FIRMS's SP data cover the dates and its near real-time (NRT) layer after that; if that choice changes inside the period, you get one link per stretch. Recent periods (`today` … `7days`) use NRT, because SP cannot exist yet. With neither dates nor sensors the link is the map's own default (Basic mode, last 24 hours). Coverage comes from FIRMS's map date service; `coverage.checked: false` means it could not be reached and saved dates were used.",
    "Give either `area` (the map fits and draws the box) or `center` with `zoom`; and either `period` or `start_date`/`end_date` (UTC). Pass the links and their descriptions to the user with `notes`. You have not seen the map: do not describe fires on it.",
  ].join("\n\n"),
  inputSchema: z.strictObject({
    map: z
      .enum(["global", "us-canada"])
      .default("global")
      .describe("'us-canada' opens FIRMS US/Canada, which has extra US/Canada layers"),
    area: BoxInput.optional(),
    center: z
      .strictObject({
        longitude: z.number().min(-180).max(180),
        latitude: z.number().min(-90).max(90),
      })
      .optional()
      .describe("Map center, if no area is given"),
    zoom: z
      .number()
      .min(1)
      .max(16)
      .optional()
      .describe("Zoom with `center` (global 1-16, US/Canada 4-16)"),
    period: z.enum(PERIODS).optional().describe("A recent period; default 24hrs"),
    start_date: IsoDateInput.optional().describe("First UTC day (YYYY-MM-DD), for past dates"),
    end_date: IsoDateInput.optional().describe("Last UTC day; defaults to start_date"),
    sensors: SensorsInput.optional(),
    mode: ModeInput.optional().describe(
      "Map mode; chosen automatically (advanced for sensors or past dates, else basic)",
    ),
    basemap: z
      .string()
      .max(80)
      .optional()
      .describe("Basemap layer ID; default 'earth' (Blue Marble)"),
    overlays: z
      .array(z.string().max(80))
      .max(10)
      .optional()
      .describe("Overlay layer IDs; default ['country-outline']"),
    extra_layers: z
      .array(z.string().max(80))
      .max(10)
      .optional()
      .describe("Further Fire Map layer IDs to show (must exist in the chosen mode)"),
  }),
  outputSchema: z.object({
    links: z.array(
      z.object({
        url: z.string(),
        map: z.string(),
        mode: z.string(),
        dates: z.string().describe("The map's d: value"),
        start_date: z.string().nullable(),
        end_date: z.string().nullable(),
        layers: z.array(z.string()),
        description: z.string().describe("What the link shows; repeat it to the user"),
      }),
    ),
    notes: z.array(z.string()),
    coverage: CoverageOutput,
    limitations: z.string(),
  }),
  annotations: READ_ONLY_FIRMS,
  async run(input, signal) {
    return buildFireMapUrls(input, await currentCoverage(signal), today());
  },
});
