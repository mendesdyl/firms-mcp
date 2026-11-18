/**
 * UTC calendar days as `YYYY-MM-DD` strings. FIRMS dates are UTC days, and ISO strings compare
 * correctly as text, so no time zones or Date objects leak into the builders.
 */
import { UrlBuilderError } from "./errors.js";

export type IsoDate = string;

const ISO = /^(\d{4})-(\d{2})-(\d{2})$/;
const DAY_MS = 86_400_000;

export function todayUtc(now: Date = new Date()): IsoDate {
  return now.toISOString().slice(0, 10);
}

function toMs(date: IsoDate): number {
  const match = ISO.exec(date);
  if (!match) return Number.NaN;
  const [, y, m, d] = match.map(Number) as [number, number, number, number];
  const ms = Date.UTC(y, m - 1, d);
  // Date.UTC rolls 2026-02-30 over to March; a real date survives the round trip.
  return new Date(ms).toISOString().slice(0, 10) === date ? ms : Number.NaN;
}

export function isIsoDate(value: string): boolean {
  return !Number.isNaN(toMs(value));
}

/** Checks `value` is a real date in `YYYY-MM-DD` form and not after `today`. */
export function checkDate(value: string, field: string, today: IsoDate): IsoDate {
  if (!isIsoDate(value)) {
    throw new UrlBuilderError(
      `${field} must be a real date in YYYY-MM-DD form (got ${JSON.stringify(value)})`,
    );
  }
  if (value > today) {
    throw new UrlBuilderError(`${field} ${value} is in the future (today is ${today} UTC)`);
  }
  return value;
}

export function addDays(date: IsoDate, days: number): IsoDate {
  return new Date(toMs(date) + days * DAY_MS).toISOString().slice(0, 10);
}

/** Number of days from `start` to `end`, counting both. */
export function daysInclusive(start: IsoDate, end: IsoDate): number {
  return Math.round((toMs(end) - toMs(start)) / DAY_MS) + 1;
}

/** Every day from `start` to `end`, inclusive. */
export function eachDay(start: IsoDate, end: IsoDate): IsoDate[] {
  const days: IsoDate[] = [];
  for (let day = start; day <= end; day = addDays(day, 1)) days.push(day);
  return days;
}

export function describeDates(start: IsoDate, end: IsoDate): string {
  return start === end ? start : `${start} to ${end}`;
}
