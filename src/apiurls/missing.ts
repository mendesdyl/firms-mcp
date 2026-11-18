/**
 * Days FIRMS lists as missing (ADR-0011 §7; FR-KB-013), from the missing-data table the weekly
 * sync saves. Answers always give the date the table was saved and the live page.
 */
import { describeDates, type IsoDate } from "../common/dates.js";
import type { MissingData } from "../knowledge/missing-data.js";
import { getSensor, type Processing, type SensorId } from "../sources/index.js";

export type MissingTable = "standard" | "nrt";
export interface MissingGap {
  date: IsoDate;
  satellite: string;
}

const TABLE_TEXT: Record<MissingTable, string> = {
  standard: "standard-processing",
  nrt: "near real-time",
};

export function tableFor(processing: Processing): MissingTable {
  return processing === "SP" ? "standard" : "nrt";
}

/** Gaps in one table for the given sensors (all when omitted) and dates, newest first. */
export function missingDays(
  data: MissingData,
  table: MissingTable,
  sensors?: readonly SensorId[],
  start?: IsoDate,
  end?: IsoDate,
): MissingGap[] {
  const names = sensors?.length
    ? new Set(sensors.flatMap((s) => getSensor(s).missing_data_names))
    : undefined;
  return data[table].filter(
    (gap) =>
      (!names || names.has(gap.satellite)) &&
      (start === undefined || gap.date >= start) &&
      (end === undefined || gap.date <= end),
  );
}

/** A note for an area request whose dates include days FIRMS lists as missing. */
export function missingNote(
  data: MissingData,
  sensor: SensorId,
  processing: Processing,
  start: IsoDate,
  end: IsoDate,
): string | undefined {
  const table = tableFor(processing);
  const gaps = missingDays(data, table, [sensor], start, end);
  if (!gaps.length) return undefined;
  const dates = [...new Set(gaps.map((g) => g.date))].sort();
  return `FIRMS's missing-data table (saved ${data.retrieved}) lists ${dates.join(", ")} as missing from the ${TABLE_TEXT[table]} archive for ${getSensor(sensor).label} (requested ${describeDates(start, end)}); the live table is ${data.page_url}.`;
}
