import * as z from "zod/v4";
import { buildAreaUrls, missingDays, missingNote } from "../../apiurls/index.js";
import { checkDate, describeDates } from "../../common/dates.js";
import { UrlBuilderError } from "../../common/errors.js";
import {
  dataAvailabilityUrl,
  LIMITATIONS,
  MAP_KEY_GUIDANCE,
  mapKeyStatusUrl,
  relatedLinks,
} from "../../common/links.js";
import { MISSING_DATA_PAGE } from "../../knowledge/missing-data.js";
import { getSensor, SOURCE_IDS } from "../../sources/index.js";
import {
  BoxInput,
  CoverageOutput,
  currentCoverage,
  IsoDateInput,
  MapKeyOutput,
  missingData,
  READ_ONLY_FIRMS,
  RelatedOutput,
  SensorsInput,
  today,
} from "../common.js";
import { defineTool } from "../definition.js";

const REQUESTS = ["area", "data_availability", "map_key_status", "missing_data"] as const;

const Gap = z.object({ date: z.string(), satellite: z.string() });

const UrlItem = z.object({
  label: z.string(),
  url: z.string(),
  sensor: z.string().nullable(),
  source: z.string().nullable(),
  processing: z.enum(["SP", "NRT"]).nullable(),
  start_date: z.string().nullable(),
  end_date: z.string().nullable(),
  day_range: z.number().int().nullable(),
});
type UrlItem = z.infer<typeof UrlItem>;

function link(label: string, url: string): UrlItem {
  return {
    label,
    url,
    sensor: null,
    source: null,
    processing: null,
    start_date: null,
    end_date: null,
    day_range: null,
  };
}

const OutputSchema = z.object({
  request: z.enum(REQUESTS),
  urls: z.array(UrlItem),
  notes: z.array(z.string()),
  coverage: CoverageOutput.nullable().describe("How SP/NRT coverage was determined (area only)"),
  map_key: MapKeyOutput.nullable().describe("Set when the URLs contain [MAP_KEY]"),
  missing_data: z
    .object({
      retrieved: z.string().describe("When the weekly sync saved FIRMS's table"),
      page_url: z.string().describe("The live table"),
      note: z.string(),
      standard: z.array(Gap).describe("Days missing from the standard-processing archive"),
      nrt: z.array(Gap).describe("Days missing from the near real-time archive"),
    })
    .nullable(),
  related: RelatedOutput,
  limitations: z.string(),
});
type Output = z.infer<typeof OutputSchema>;

export const buildApiUrl = defineTool({
  name: "firms_build_api_url",
  version: "1.0.0",
  title: "Build FIRMS API URLs",
  description: [
    "Build FIRMS API URLs for the user to open; this server does not fetch them. `request` chooses what:",
    "- `area`: CSV of fire detections for a box (or 'world') and dates. Standard data first: dates FIRMS's standard-processing (SP) data cover use the SP source, dates after that use near real-time (NRT), and a period that spans both gets labelled SP and NRT URLs. `recent_days` (1-5) gives the most recent data (NRT). Periods are cut into URLs of at most 5 days; at most 31 days per call (longer: the archive download page in `related`). Known missing days from FIRMS's missing-data table are noted.",
    "- `data_availability`: CSV of the dates each source covers (`source`, default ALL).",
    "- `map_key_status`: the transactions the user's key has used.",
    "- `missing_data`: days FIRMS lists as missing, from the copy saved by the weekly sync (filter with `sensors` and dates), with the date it was saved and the live page.",
    "URLs that need a key contain the placeholder [MAP_KEY]; `map_key` says where the user gets a free key and where it goes. Never ask for a key. If the user has already shared theirs in the conversation, you may put it into the URLs for them. Pass on `notes` and `limitations`: you have not seen the data.",
  ].join("\n"),
  inputSchema: z.strictObject({
    request: z.enum(REQUESTS).describe("Which FIRMS URL to build"),
    area: z
      .union([z.literal("world"), BoxInput])
      .optional()
      .describe("For `area`: a bounding box, or 'world'"),
    sensors: SensorsInput.optional(),
    recent_days: z
      .number()
      .int()
      .min(1)
      .max(5)
      .optional()
      .describe("For `area`: the most recent 1-5 UTC days (instead of dates)"),
    start_date: IsoDateInput.optional().describe("First UTC day (YYYY-MM-DD)"),
    end_date: IsoDateInput.optional().describe("Last UTC day; defaults to start_date"),
    processing: z
      .enum(["standard_first", "nrt"])
      .default("standard_first")
      .describe("For `area`: 'nrt' only when the user explicitly asks for near real-time data"),
    source: z
      .enum(["ALL", ...SOURCE_IDS])
      .default("ALL")
      .describe("For `data_availability`: one source ID, or ALL"),
  }),
  outputSchema: OutputSchema,
  annotations: READ_ONLY_FIRMS,
  async run(input, signal): Promise<Output> {
    const base = {
      request: input.request,
      coverage: null,
      map_key: null,
      missing_data: null,
      related: relatedLinks(),
      limitations: LIMITATIONS,
    };
    if (input.request !== "area") {
      const unused = (["area", "recent_days"] as const).filter((f) => input[f] !== undefined);
      if (unused.length) {
        throw new UrlBuilderError(`${unused.join(" and ")} only apply to request 'area'`);
      }
    }

    if (input.request === "data_availability") {
      return {
        ...base,
        urls: [
          link(
            `Dates covered by ${input.source === "ALL" ? "every FIRMS source" : input.source} (CSV)`,
            dataAvailabilityUrl(input.source),
          ),
        ],
        notes: [],
        map_key: MAP_KEY_GUIDANCE,
      };
    }
    if (input.request === "map_key_status") {
      return {
        ...base,
        urls: [
          link("Transactions this MAP_KEY has used in the current interval", mapKeyStatusUrl()),
        ],
        notes: ["FIRMS allows 5,000 transactions per MAP_KEY every 10 minutes."],
        map_key: MAP_KEY_GUIDANCE,
      };
    }
    if (input.request === "missing_data") {
      const now = today();
      const start =
        input.start_date === undefined ? undefined : checkDate(input.start_date, "start_date", now);
      const end = input.end_date === undefined ? start : checkDate(input.end_date, "end_date", now);
      if (start !== undefined && end !== undefined && start > end) {
        throw new UrlBuilderError("start_date is after end_date");
      }
      const data = missingData();
      const urls = [
        link("FIRMS missing-data table (live; can take a minute to load)", MISSING_DATA_PAGE),
      ];
      if (!data) {
        return {
          ...base,
          urls,
          notes: ["No saved copy of FIRMS's missing-data table is available; open the live page."],
        };
      }
      for (const s of input.sensors ?? []) getSensor(s);
      const standard = missingDays(data, "standard", input.sensors, start, end);
      const nrt = missingDays(data, "nrt", input.sensors, start, end);
      const scope = [
        input.sensors?.length
          ? input.sensors.map((s) => getSensor(s).label).join(", ")
          : "all satellites",
        start !== undefined && end !== undefined ? describeDates(start, end) : "all dates",
      ].join(", ");
      return {
        ...base,
        urls,
        notes: [],
        missing_data: {
          retrieved: data.retrieved,
          page_url: data.page_url,
          note: `From FIRMS's missing-data table as saved on ${data.retrieved} (${scope}); days added since then appear only on the live page, ${data.page_url}.`,
          standard,
          nrt,
        },
      };
    }

    if (input.area === undefined) {
      throw new UrlBuilderError("area is required for request 'area': a bounding box, or 'world'");
    }
    const result = buildAreaUrls(
      {
        area: input.area,
        sensors: input.sensors,
        recent_days: input.recent_days,
        start_date: input.start_date,
        end_date: input.end_date,
        processing: input.processing,
      },
      await currentCoverage(signal),
      today(),
    );
    const data = missingData();
    const missingNotes = data
      ? result.requests.flatMap(
          (r) => missingNote(data, r.sensor, r.processing, r.start_date, r.end_date) ?? [],
        )
      : [];
    return {
      ...base,
      urls: result.requests.map((r) => ({
        label: r.label,
        url: r.url,
        sensor: r.sensor,
        source: r.source,
        processing: r.processing,
        start_date: r.start_date,
        end_date: r.end_date,
        day_range: r.day_range,
      })),
      notes: [...result.notes, ...missingNotes],
      coverage: result.coverage,
      map_key: result.map_key,
    };
  },
});
