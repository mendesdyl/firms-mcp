/**
 * FIRMS Fire Map deep links (ADR-0006; FR-MAP-001 … FR-MAP-007). The map keeps its state in
 * the URL hash; the grammar was derived from the map's own parser and verified with cold page
 * loads on the global (`/map/`) and US/Canada (`/usfs/map/`) maps:
 *
 *     #[m:<mode>;]d:<dates>;l:<layer>,…;(i:<w>,<s>,<e>,<n> | @<lon>,<lat>,<zoom>z)
 *
 * `l:` replaces the map's default layers, so a basemap is always included. Per-satellite and
 * standard-processing layers exist only in modes that list them (Advanced has them all).
 *
 * Standard data first (ADR-0011 §4): for explicit past dates, each sensor shows its
 * standard-processing layer where SP covers the dates and its NRT layer after that. Where the
 * choice changes inside the period, the period is split into one link per stretch, so every
 * link shows one consistent set of layers.
 */
import { type BoundingBox, checkBox, formatBox, formatNumber } from "../common/area.js";
import { addDays, checkDate, describeDates, eachDay, type IsoDate } from "../common/dates.js";
import { UrlBuilderError } from "../common/errors.js";
import { FIRMS_BASE_URL, LIMITATIONS } from "../common/links.js";
import {
  type Coverage,
  type CoverageSummary,
  getSensor,
  getSource,
  planSensors,
  RECENT_NOTE,
  type SensorId,
  type SourceId,
  summarizeCoverage,
} from "../sources/index.js";
import { allowedLayers, LINKABLE_MODES, layerTitle, MAP_CATALOG, type MapName } from "./catalog.js";

export const REFERRAL = { utm_source: "firms-mcp", utm_medium: "mcp" } as const;
export const PERIODS = ["today", "24hrs", "48hrs", "72hrs", "7days"] as const;
export type Period = (typeof PERIODS)[number];
const PERIOD_TEXT: Record<Period, string> = {
  today: "today (00:00 UTC to now)",
  "24hrs": "the last 24 hours",
  "48hrs": "the last 48 hours",
  "72hrs": "the last 72 hours",
  "7days": "the last 7 days",
};
/** Days before today that each period reaches back (24hrs spans yesterday and today). */
const PERIOD_PAST_DAYS: Record<Period, number> = {
  today: 0,
  "24hrs": 1,
  "48hrs": 2,
  "72hrs": 3,
  "7days": 6,
};
/** View when no area or center is given. */
const DEFAULT_VIEW: Record<MapName, { longitude: number; latitude: number; zoom: number }> = {
  global: { longitude: 0, latitude: 0, zoom: 3 },
  "us-canada": { longitude: -100, latitude: 45, zoom: 4 },
};
const BASIC_FIRE_LAYER = "fire_layers_basic";

export interface FireMapInput {
  map?: MapName | undefined;
  area?: BoundingBox | undefined;
  center?: { longitude: number; latitude: number } | undefined;
  zoom?: number | undefined;
  /** A recent period; the default is the map's own default, the last 24 hours. */
  period?: Period | undefined;
  start_date?: string | undefined;
  end_date?: string | undefined;
  /** Sensors shown one by one (Advanced mode); without them recent periods use Basic mode. */
  sensors?: readonly SensorId[] | undefined;
  extra_layers?: readonly string[] | undefined;
  overlays?: readonly string[] | undefined;
  basemap?: string | undefined;
  mode?: string | undefined;
  referral?: boolean | undefined;
}

export interface FireMapLink {
  url: string;
  map: MapName;
  mode: string;
  /** Value of the `d:` segment. */
  dates: string;
  start_date: IsoDate | null;
  end_date: IsoDate | null;
  layers: string[];
  description: string;
}

export interface FireMapResult {
  links: FireMapLink[];
  notes: string[];
  coverage: CoverageSummary;
  limitations: string;
}

/** One stretch of the period and the fire source each sensor shows during it. */
interface Stretch {
  dates: string;
  start: IsoDate | null;
  end: IsoDate | null;
  sources: SourceId[];
}

function resolveStretches(
  input: FireMapInput,
  mode: string | undefined,
  coverage: Coverage,
  today: IsoDate,
  notes: string[],
): { stretches: Stretch[]; mode: string; basic: boolean } {
  const hasDates = input.start_date !== undefined || input.end_date !== undefined;
  if (input.period !== undefined && hasDates) {
    throw new UrlBuilderError("give either a period or start_date/end_date, not both");
  }
  const chosen = input.sensors?.length ? input.sensors.map((s) => getSensor(s).id) : undefined;

  if (!hasDates) {
    const period = input.period ?? "24hrs";
    if (!PERIODS.includes(period))
      throw new UrlBuilderError(`period must be one of ${PERIODS.join(", ")}`);
    const resolvedMode = mode ?? (chosen ? "advanced" : "basic");
    if (resolvedMode === "basic" && !chosen) {
      return {
        stretches: [{ dates: period, start: null, end: null, sources: [] }],
        mode: resolvedMode,
        basic: true,
      };
    }
    // Default sensors appear only if FIRMS has NRT data for them in the period's window.
    const windowStart = addDays(today, -PERIOD_PAST_DAYS[period]);
    const sensors =
      chosen ??
      planSensors(undefined, windowStart, today, coverage, "nrt").plans.map((p) => p.sensor);
    notes.push(RECENT_NOTE);
    return {
      stretches: [
        {
          dates: period,
          start: null,
          end: null,
          sources: sensors.map((s) => getSensor(s).nrt_source),
        },
      ],
      mode: resolvedMode,
      basic: false,
    };
  }

  if (input.start_date === undefined)
    throw new UrlBuilderError("give start_date as well as end_date");
  const start = checkDate(input.start_date, "start_date", today);
  const end = checkDate(input.end_date ?? input.start_date, "end_date", today);
  if (start > end) throw new UrlBuilderError("start_date is after end_date");
  const resolvedMode = mode ?? "advanced";
  if (resolvedMode === "basic" && !chosen) {
    notes.push(
      "Basic mode shows FIRMS's combined fire layer; standard-processing layers need mode 'advanced'.",
    );
    const dates = start === end ? start : `${start}..${end}`;
    return { stretches: [{ dates, start, end, sources: [] }], mode: resolvedMode, basic: true };
  }

  const { plans, notes: planNotes } = planSensors(chosen, start, end, coverage);
  notes.push(...planNotes);
  const sourcesOn = (day: IsoDate): SourceId[] =>
    plans.flatMap((plan) =>
      plan.runs.filter((r) => r.start <= day && day <= r.end).map((r) => r.source),
    );

  const stretches: Stretch[] = [];
  for (const day of eachDay(start, end)) {
    const sources = sourcesOn(day);
    const last = stretches.at(-1);
    if (last && last.sources.join() === sources.join()) last.end = day;
    else stretches.push({ dates: "", start: day, end: day, sources });
  }
  for (const s of stretches) s.dates = s.start === s.end ? `${s.start}` : `${s.start}..${s.end}`;
  if (
    resolvedMode !== "advanced" &&
    stretches.some((s) => s.sources.some((id) => getSource(id).processing === "SP"))
  ) {
    throw new UrlBuilderError(
      `standard-processing layers are only in advanced mode; use mode 'advanced' (or leave mode out) for past dates`,
    );
  }
  return { stretches: stretches.filter((s) => s.sources.length), mode: resolvedMode, basic: false };
}

function checkLayers(layers: string[], mode: string, basemap: string): void {
  const unknown = layers.filter((id) => !MAP_CATALOG.layers.has(id));
  if (unknown.length) throw new UrlBuilderError(`unknown Fire Map layer(s): ${unknown.join(", ")}`);
  const allowed = allowedLayers(mode);
  const notInMode = layers.filter((id) => !allowed.has(id));
  if (notInMode.length) {
    throw new UrlBuilderError(
      `layer(s) ${notInMode.join(", ")} are not available in ${mode} mode` +
        (mode === "basic" ? " (per-satellite fire layers need mode 'advanced')" : ""),
    );
  }
  if (MAP_CATALOG.layers.get(basemap)?.category !== "basemap") {
    throw new UrlBuilderError(`${JSON.stringify(basemap)} is not a basemap`);
  }
}

function processingText(sources: SourceId[]): string {
  if (!sources.length) return "FIRMS's combined fire layer";
  const sp = sources.filter((id) => getSource(id).processing === "SP");
  if (sp.length === sources.length) return "standard processing";
  if (!sp.length) return "near real-time";
  const labels = (ids: SourceId[]) =>
    ids.map((id) => getSensor(getSource(id).sensor).label).join(", ");
  return `standard processing for ${labels(sp)}; near real-time for ${labels(sources.filter((id) => !sp.includes(id)))}`;
}

export function buildFireMapUrls(
  input: FireMapInput,
  coverage: Coverage,
  today: IsoDate,
): FireMapResult {
  const mapName: MapName = input.map ?? "global";
  const limits = MAP_CATALOG.maps[mapName];
  if (!limits)
    throw new UrlBuilderError(`map must be one of ${Object.keys(MAP_CATALOG.maps).join(", ")}`);
  if (input.mode !== undefined && !(LINKABLE_MODES as readonly string[]).includes(input.mode)) {
    throw new UrlBuilderError(`mode must be one of ${LINKABLE_MODES.join(", ")}`);
  }
  if (input.area !== undefined && input.center !== undefined) {
    throw new UrlBuilderError("give either an area or a center, not both");
  }

  // Location: an area of interest (the map fits and draws it) or a center and zoom.
  let location: string;
  let where: string;
  if (input.area !== undefined) {
    const box = checkBox(input.area);
    location = `i:${formatBox(box)}`;
    where = `the area west ${formatNumber(box.west)}, south ${formatNumber(box.south)}, east ${formatNumber(box.east)}, north ${formatNumber(box.north)} (the map draws this box)`;
  } else {
    const view = DEFAULT_VIEW[mapName];
    const { longitude, latitude } = input.center ?? view;
    if (!(Math.abs(longitude) <= 180 && Math.abs(latitude) <= 90)) {
      throw new UrlBuilderError("center must have longitude -180 to 180 and latitude -90 to 90");
    }
    const zoom = input.zoom ?? (input.center ? 8 : view.zoom);
    if (!(zoom >= limits.min_zoom && zoom <= limits.max_zoom)) {
      throw new UrlBuilderError(
        `zoom must be between ${limits.min_zoom} and ${limits.max_zoom} for this map`,
      );
    }
    const lon = formatNumber(Math.round(longitude * 1e4) / 1e4);
    const lat = formatNumber(Math.round(latitude * 1e4) / 1e4);
    location = `@${lon},${lat},${zoom.toFixed(1)}z`;
    where = `longitude ${lon}, latitude ${lat} at zoom ${zoom.toFixed(1)}`;
  }

  const notes: string[] = [];
  const { stretches, mode, basic } = resolveStretches(input, input.mode, coverage, today, notes);
  const basemap = input.basemap ?? "earth";
  const overlays = input.overlays ?? ["country-outline"];
  const query = (input.referral ?? true) ? `?${new URLSearchParams(REFERRAL)}` : "";
  const modeLabel = MAP_CATALOG.modes.get(mode)?.label ?? mode;
  const overlayText = overlays.length ? ` with ${overlays.map(layerTitle).join(", ")}` : "";

  const links = stretches.map((stretch): FireMapLink => {
    const fireLayers = basic
      ? [BASIC_FIRE_LAYER]
      : stretch.sources.flatMap((id) => getSource(id).map_layers);
    const layers = [
      ...new Set([...fireLayers, ...(input.extra_layers ?? []), ...overlays, basemap]),
    ];
    checkLayers(layers, mode, basemap);
    const segments = [
      ...(mode === "basic" ? [] : [`m:${mode}`]),
      `d:${stretch.dates}`,
      `l:${layers.join(",")}`,
      location,
    ];
    const datesText =
      stretch.start === null
        ? PERIOD_TEXT[stretch.dates as Period]
        : `${describeDates(stretch.start, stretch.end ?? stretch.start)} (UTC)`;
    return {
      url: `${FIRMS_BASE_URL}${limits.path}${query}#${segments.join(";")}`,
      map: mapName,
      mode,
      dates: stretch.dates,
      start_date: stretch.start,
      end_date: stretch.end,
      layers,
      description:
        `Opens the FIRMS ${mapName === "us-canada" ? "US/Canada " : ""}Fire Map (${modeLabel}) showing ` +
        `${fireLayers.map(layerTitle).join(", ")} (${processingText(stretch.sources)}) for ${datesText} over ${where}, ` +
        `on the ${layerTitle(basemap)} basemap${overlayText}. The map, not this server, renders FIRMS data; times are UTC.`,
    };
  });
  if (!links.length)
    notes.push("No fire data source covers the requested dates, so no link was built.");

  return { links, notes, coverage: summarizeCoverage(coverage), limitations: LIMITATIONS };
}
