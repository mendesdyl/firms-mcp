/**
 * FIRMS area API URLs (ADR-0011 §2 and §4; FR-URL-001 … FR-URL-004, FR-DATA-002):
 *
 *     /api/area/csv/[MAP_KEY]/[SOURCE]/[AREA_COORDINATES]/[DAY_RANGE]            most recent days
 *     /api/area/csv/[MAP_KEY]/[SOURCE]/[AREA_COORDINATES]/[DAY_RANGE]/[DATE]     DATE .. DATE+DAY_RANGE-1
 *
 * DAY_RANGE is 1 to 5 (FIRMS area-API page, 2026-11-18), so longer periods become several
 * URLs. Each sensor uses its standard-processing source for the dates SP covers and NRT after
 * that; the key stays the literal placeholder `[MAP_KEY]`.
 */
import { areaCoordinates, type BoundingBox } from "../common/area.js";
import { addDays, checkDate, daysInclusive, describeDates, type IsoDate } from "../common/dates.js";
import { UrlBuilderError } from "../common/errors.js";
import {
  ARCHIVE_DOWNLOAD_URL,
  FIRMS_BASE_URL,
  LIMITATIONS,
  MAP_KEY_GUIDANCE,
  MAP_KEY_PLACEHOLDER,
  type MapKeyGuidance,
  type RelatedLinks,
  relatedLinks,
} from "../common/links.js";
import {
  type Coverage,
  type CoverageSummary,
  getSensor,
  type Processing,
  type ProcessingPreference,
  planSensors,
  RECENT_NOTE,
  type SensorId,
  type SourceId,
  summarizeCoverage,
} from "../sources/index.js";

/** FIRMS area API limit on DAY_RANGE. */
export const MAX_DAY_RANGE = 5;
/** Longest period one request may cover; longer periods belong to the archive download page. */
export const MAX_REQUEST_DAYS = 31;

export interface AreaUrlInput {
  area: BoundingBox | "world";
  /** Sensors to query; the four global sensors when omitted. */
  sensors?: readonly SensorId[] | undefined;
  /** The most recent 1–5 days (NRT); or give start_date (and end_date). */
  recent_days?: number | undefined;
  start_date?: string | undefined;
  /** Defaults to start_date. */
  end_date?: string | undefined;
  processing?: ProcessingPreference | undefined;
}

export interface AreaRequest {
  sensor: SensorId;
  source: SourceId;
  processing: Processing;
  label: string;
  start_date: IsoDate;
  end_date: IsoDate;
  day_range: number;
  url: string;
}

export interface AreaUrlResult {
  requests: AreaRequest[];
  notes: string[];
  coverage: CoverageSummary;
  map_key: MapKeyGuidance;
  related: RelatedLinks;
  limitations: string;
}

const PROCESSING_TEXT: Record<Processing, string> = {
  SP: "standard processing",
  NRT: "near real-time (NRT)",
};

function areaUrl(source: SourceId, area: string, dayRange: number, date?: IsoDate): string {
  const base = `${FIRMS_BASE_URL}/api/area/csv/${MAP_KEY_PLACEHOLDER}/${source}/${area}/${dayRange}`;
  return date === undefined ? base : `${base}/${date}`;
}

function request(
  sensor: SensorId,
  source: SourceId,
  processing: Processing,
  start: IsoDate,
  end: IsoDate,
  url: string,
): AreaRequest {
  return {
    sensor,
    source,
    processing,
    label: `${getSensor(sensor).label.replace(/ \(.*\)$/, "")}, ${PROCESSING_TEXT[processing]}, ${describeDates(start, end)}`,
    start_date: start,
    end_date: end,
    day_range: daysInclusive(start, end),
    url,
  };
}

function resolveDates(
  input: AreaUrlInput,
  today: IsoDate,
): { start: IsoDate; end: IsoDate } | number {
  const hasDates = input.start_date !== undefined || input.end_date !== undefined;
  if (input.recent_days !== undefined) {
    if (hasDates)
      throw new UrlBuilderError("give either recent_days or start_date/end_date, not both");
    const n = input.recent_days;
    if (!Number.isInteger(n) || n < 1 || n > MAX_DAY_RANGE) {
      throw new UrlBuilderError(
        `recent_days must be a whole number from 1 to ${MAX_DAY_RANGE} (FIRMS limit)`,
      );
    }
    return n;
  }
  if (input.start_date === undefined) {
    throw new UrlBuilderError(
      "give recent_days (1 to 5) for the most recent data, or start_date (and end_date) in YYYY-MM-DD",
    );
  }
  const start = checkDate(input.start_date, "start_date", today);
  const end = checkDate(input.end_date ?? input.start_date, "end_date", today);
  if (start > end) throw new UrlBuilderError("start_date is after end_date");
  const days = daysInclusive(start, end);
  if (days > MAX_REQUEST_DAYS) {
    throw new UrlBuilderError(
      `a request may cover at most ${MAX_REQUEST_DAYS} days (this one covers ${days}); for longer periods use the FIRMS archive download page, ${ARCHIVE_DOWNLOAD_URL}`,
    );
  }
  return { start, end };
}

export function buildAreaUrls(
  input: AreaUrlInput,
  coverage: Coverage,
  today: IsoDate,
): AreaUrlResult {
  const area = areaCoordinates(input.area);
  const dates = resolveDates(input, today);
  const requests: AreaRequest[] = [];
  const notes: string[] = [];

  if (typeof dates === "number") {
    // The URL asks for "the most recent N days", so a sensor whose NRT data stopped before
    // that window (Suomi NPP after 2026-11-02) would only return an empty file.
    const start = addDays(today, 1 - dates);
    const planned = planSensors(input.sensors, start, today, coverage, "nrt");
    notes.push(RECENT_NOTE, ...planned.notes.filter((note) => !note.includes("are preferred")));
    for (const plan of planned.plans) {
      const sensor = getSensor(plan.sensor);
      if (!plan.runs.length) {
        notes.push(`${sensor.label}: no URL was built for the most recent days.`);
        continue;
      }
      requests.push(
        request(
          sensor.id,
          sensor.nrt_source,
          "NRT",
          start,
          today,
          areaUrl(sensor.nrt_source, area, dates),
        ),
      );
    }
  } else {
    const planned = planSensors(input.sensors, dates.start, dates.end, coverage, input.processing);
    notes.push(...planned.notes);
    for (const run of planned.plans.flatMap((plan) => plan.runs)) {
      for (let chunk = run.start; chunk <= run.end; chunk = addDays(chunk, MAX_DAY_RANGE)) {
        const chunkEnd = [addDays(chunk, MAX_DAY_RANGE - 1), run.end].sort()[0] as IsoDate;
        const days = daysInclusive(chunk, chunkEnd);
        requests.push(
          request(
            run.sensor,
            run.source,
            run.processing,
            chunk,
            chunkEnd,
            areaUrl(run.source, area, days, chunk),
          ),
        );
      }
    }
  }

  return {
    requests,
    notes,
    coverage: summarizeCoverage(coverage),
    map_key: MAP_KEY_GUIDANCE,
    related: relatedLinks(),
    limitations: LIMITATIONS,
  };
}
