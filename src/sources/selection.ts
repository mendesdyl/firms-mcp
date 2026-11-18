/**
 * Standard data first (ADR-0011 §4; FR-URL-001, FR-MAP-007): for each sensor and day, choose
 * the standard-processing (SP) source if SP covers the day, otherwise the NRT source if NRT
 * covers it, otherwise nothing. Consecutive days with the same choice form one run. Both the API
 * URL builder and the Fire Map link builder use these runs, so they always agree.
 */
import { describeDates, eachDay, type IsoDate } from "../common/dates.js";
import { SP_VS_NRT_ENTRY } from "../common/links.js";
import {
  DEFAULT_SENSORS,
  getSensor,
  type Processing,
  type SensorId,
  type SourceId,
} from "./catalog.js";
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
  sensor: SensorId;
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
  return { sensor: sensor.id, runs, uncovered, notes };
}

const GAP_NOTE = ": no data for ";

/**
 * Plans for the sensors the user named, or for the default sensors. A default sensor is used
 * only for the dates FIRMS has its data (owner decision 2026-11-18, after Suomi NPP data
 * production ceased on 2026-11-02): it is left out of the other dates with one short note
 * naming the default sensors that cover them, instead of a "no data" warning. A sensor the
 * user named keeps the warning, because they asked for it.
 */
export function planSensors(
  requested: readonly SensorId[] | undefined,
  start: IsoDate,
  end: IsoDate,
  coverage: Coverage,
  preference: ProcessingPreference = "standard_first",
): { plans: SensorPlan[]; notes: string[] } {
  const explicit = requested !== undefined && requested.length > 0;
  const sensors = explicit ? requested : DEFAULT_SENSORS;
  const plans = sensors.map((s) => planSensor(s, start, end, coverage, preference));
  if (explicit) return { plans, notes: plans.flatMap((p) => p.notes) };

  const covers = (plan: SensorPlan, gap: DateRange) =>
    eachDay(gap.start, gap.end).every((day) =>
      plan.runs.some((r) => r.start <= day && day <= r.end),
    );
  const notes: string[] = [];
  plans.forEach((plan, i) => {
    notes.push(...plan.notes.filter((note) => !note.includes(GAP_NOTE)));
    const label = getSensor(plan.sensor).label;
    for (const gap of plan.uncovered) {
      const others = plans
        .filter((other, j) => j !== i && covers(other, gap))
        .map((other) => getSensor(other.sensor).label);
      notes.push(
        `${label} is left out of the default sensors for ${describeDates(gap.start, gap.end)}, where FIRMS has no data for it` +
          (others.length
            ? `; ${others.join(", ")} cover${others.length === 1 ? "s" : ""} those dates.`
            : "."),
      );
    }
  });
  return { plans: plans.filter((plan) => plan.runs.length), notes };
}

/** The note for "today" or "the last N days", where SP cannot exist yet. */
export const RECENT_NOTE = `For the most recent days, standard-processing data cannot exist yet; near real-time (NRT) data are used (FAQ entry ${SP_VS_NRT_ENTRY}).`;
