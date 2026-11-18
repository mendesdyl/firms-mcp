/**
 * Standard data first (ADR-0011 §4; FR-URL-001, FR-MAP-007): for each sensor and day, choose
 * the standard-processing (SP) source if SP covers the day, otherwise the NRT source if NRT
 * covers it, otherwise nothing. Consecutive days with the same choice form one run. Both the API
 * URL builder and the Fire Map link builder use these runs, so they always agree.
 */
import { describeDates, eachDay, type IsoDate } from "../common/dates.js";
import { SP_VS_NRT_ENTRY } from "../common/links.js";
import { getSensor, type Processing, type SensorId, type SourceId } from "./catalog.js";
import type { Coverage, DateRange } from "./coverage.js";

/** `standard_first` is the default; `nrt` is for a user who asks for NRT data explicitly. */
export type ProcessingPreference = "standard_first" | "nrt";

export interface Run {
  sensor: SensorId;
  source: SourceId;
  processing: Processing;
  start: IsoDate;
  end: IsoDate;
}

export interface SensorPlan {
  runs: Run[];
  /** Days no source covers, as ranges. */
  uncovered: DateRange[];
  notes: string[];
}

const within = (day: IsoDate, range: DateRange | undefined) =>
  range !== undefined && range.start <= day && day <= range.end;

/** Groups consecutive days with the same key into ranges. */
function group<K>(
  days: IsoDate[],
  key: (day: IsoDate) => K,
): { key: K; start: IsoDate; end: IsoDate }[] {
  const groups: { key: K; start: IsoDate; end: IsoDate }[] = [];
  for (const day of days) {
    const k = key(day);
    const last = groups.at(-1);
    if (last && last.key === k) last.end = day;
    else groups.push({ key: k, start: day, end: day });
  }
  return groups;
}

export function planSensor(
  sensorId: SensorId,
  start: IsoDate,
  end: IsoDate,
  coverage: Coverage,
  preference: ProcessingPreference = "standard_first",
): SensorPlan {
  const sensor = getSensor(sensorId);
  const sp = sensor.sp_source;
  const spRange = sp === null ? undefined : coverage.ranges[sp];
  const nrtRange = coverage.ranges[sensor.nrt_source];
  const days = eachDay(start, end);

  const choose = (day: IsoDate): SourceId | null => {
    if (preference === "standard_first" && sp !== null && within(day, spRange)) return sp;
    if (within(day, nrtRange)) return sensor.nrt_source;
    return null;
  };
  const groups = group(days, choose);
  const runs: Run[] = groups.flatMap((g) =>
    g.key === null
      ? []
      : [
          {
            sensor: sensor.id,
            source: g.key,
            processing: g.key === sp ? ("SP" as const) : ("NRT" as const),
            start: g.start,
            end: g.end,
          },
        ],
  );
  const uncovered = groups
    .filter((g) => g.key === null)
    .map((g) => ({ start: g.start, end: g.end }));

  const notes: string[] = [];
  if (sp === null) {
    notes.push(
      `${sensor.label}: FIRMS has no standard-processing product for this sensor; near real-time (NRT) data are used.`,
    );
  } else if (preference === "standard_first" && spRange) {
    const afterSp = runs.filter((r) => r.processing === "NRT" && r.start > spRange.end);
    if (afterSp.length) {
      const first = afterSp[0] as Run;
      const last = afterSp.at(-1) as Run;
      notes.push(
        `${sensor.label}: standard-processing data currently end on ${spRange.end}; ${describeDates(first.start, last.end)} use near real-time (NRT) data, which are provisional until standard processing covers those dates (FAQ entry ${SP_VS_NRT_ENTRY}).`,
      );
    }
  } else if (preference === "nrt") {
    const spDays = group(days, (day) => within(day, spRange)).filter((g) => g.key);
    for (const g of spDays) {
      notes.push(
        `${sensor.label}: standard-processing data exist for ${describeDates(g.start, g.end)} and are preferred; NRT is used because it was asked for (FAQ entry ${SP_VS_NRT_ENTRY}).`,
      );
    }
  }
  for (const gap of uncovered) {
    notes.push(
      `${sensor.label}: no data for ${describeDates(gap.start, gap.end)} in the dates FIRMS lists for this sensor (${coverage.checked ? `checked ${coverage.as_of}` : `as saved on ${coverage.as_of}`}).`,
    );
  }
  return { runs, uncovered, notes };
}

/** The note for "today" or "the last N days", where SP cannot exist yet. */
export const RECENT_NOTE = `For the most recent days, standard-processing data cannot exist yet; near real-time (NRT) data are used (FAQ entry ${SP_VS_NRT_ENTRY}).`;
