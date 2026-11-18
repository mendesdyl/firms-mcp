/**
 * Which dates each source covers (FR-DATA-008), from FIRMS's keyless map date service
 * (`/api/map_dates/`): the dates the FIRMS Fire Map currently shows. The service is
 * undocumented (running list LU-17), so any failure, timeout, or unexpected shape falls back to
 * the snapshot saved in `sources.json`, and the result says coverage could not be checked.
 */
import { type IsoDate, isIsoDate } from "../common/dates.js";
import { FIRMS_BASE_URL } from "../common/links.js";
import { COVERAGE_SNAPSHOT, SOURCES, type SourceId } from "./catalog.js";

export const MAP_DATES_URL = `${FIRMS_BASE_URL}/api/map_dates/`;
export const COVERAGE_TIMEOUT_MS = 10_000;

export interface DateRange {
  start: IsoDate;
  end: IsoDate;
}

export interface Coverage {
  /** True when the map date service answered; false when the saved snapshot is used. */
  checked: boolean;
  source: "map_dates_service" | "snapshot";
  /** When the dates were obtained: today, or the day the snapshot was saved. */
  as_of: IsoDate;
  /** One or two sentences for the user about where the dates come from. */
  note: string;
  ranges: Record<SourceId, DateRange>;
}

function readRange(value: unknown): DateRange | undefined {
  if (!Array.isArray(value) || value.length !== 2) return undefined;
  const [start, end] = value as unknown[];
  if (typeof start !== "string" || typeof end !== "string") return undefined;
  if (!isIsoDate(start) || !isIsoDate(end) || start > end) return undefined;
  return { start, end };
}

function snapshotRange(source: (typeof SOURCES)[number]): DateRange {
  const range = readRange(COVERAGE_SNAPSHOT.dates[source.map_dates_key]);
  if (!range) throw new Error(`sources.json: no coverage snapshot for ${source.map_dates_key}`);
  return range;
}

/** What a tool result reports about coverage (the ranges themselves stay internal). */
export type CoverageSummary = Omit<Coverage, "ranges">;

export function summarizeCoverage(coverage: Coverage): CoverageSummary {
  const { checked, as_of, source, note } = coverage;
  return { checked, as_of, source, note };
}

/** Coverage from a map date service response; throws if the response is unusable. */
export function coverageFromMapDates(response: unknown, today: IsoDate): Coverage {
  if (typeof response !== "object" || response === null || Array.isArray(response)) {
    throw new Error("the map date service did not return a JSON object");
  }
  const dates = response as Record<string, unknown>;
  const ranges = {} as Record<SourceId, DateRange>;
  const missing: SourceId[] = [];
  for (const source of SOURCES) {
    const range = readRange(dates[source.map_dates_key]);
    if (range) {
      ranges[source.id] = range;
    } else {
      ranges[source.id] = snapshotRange(source);
      missing.push(source.id);
    }
  }
  if (missing.length === SOURCES.length) {
    throw new Error("the map date service listed none of the FIRMS API sources");
  }
  const note = [
    `Coverage is the dates the FIRMS Fire Map currently shows (FIRMS map date service, checked ${today}).`,
    ...(missing.length
      ? [
          `The service did not list ${missing.join(", ")}; for those, the dates saved on ${COVERAGE_SNAPSHOT.retrieved} are used.`,
        ]
      : []),
  ].join(" ");
  return { checked: true, source: "map_dates_service", as_of: today, note, ranges };
}

/** Coverage from the snapshot saved with the catalog, saying why the service was not used. */
export function snapshotCoverage(reason: string): Coverage {
  const ranges = {} as Record<SourceId, DateRange>;
  for (const source of SOURCES) ranges[source.id] = snapshotRange(source);
  return {
    checked: false,
    source: "snapshot",
    as_of: COVERAGE_SNAPSHOT.retrieved,
    note: `Coverage could not be checked (${reason}); the dates FIRMS listed on ${COVERAGE_SNAPSHOT.retrieved} are used and may be out of date. The data_availability URL shows current coverage.`,
    ranges,
  };
}

export type FetchLike = (url: string, init?: RequestInit) => Promise<Response>;

export interface FetchCoverageOptions {
  today: IsoDate;
  fetchImpl?: FetchLike;
  timeoutMs?: number;
  signal?: AbortSignal;
}

/** Asks the map date service, falling back to the snapshot on any failure. Never throws. */
export async function fetchCoverage(options: FetchCoverageOptions): Promise<Coverage> {
  const { today, fetchImpl = globalThis.fetch, timeoutMs = COVERAGE_TIMEOUT_MS } = options;
  const timeout = AbortSignal.timeout(timeoutMs);
  const signal = options.signal ? AbortSignal.any([options.signal, timeout]) : timeout;
  try {
    const response = await fetchImpl(MAP_DATES_URL, {
      signal,
      headers: { accept: "application/json" },
    });
    if (!response.ok)
      return snapshotCoverage(`the map date service answered HTTP ${response.status}`);
    let body: unknown;
    try {
      body = await response.json();
    } catch {
      return snapshotCoverage("the map date service did not return JSON");
    }
    return coverageFromMapDates(body, today);
  } catch (error) {
    const reason = timeout.aborted
      ? `the map date service did not answer within ${timeoutMs / 1000} s`
      : `the map date service failed: ${error instanceof Error ? error.message : String(error)}`;
    return snapshotCoverage(reason);
  }
}
