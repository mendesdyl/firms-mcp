/**
 * FIRMS Fire Map deep links (ADR-0006; FR-MAP-001 … FR-MAP-010). The map keeps its state in
 * the URL hash; the grammar was derived from the map's own parser and writer and verified with
 * cold page loads on the global (`/map/`) and US/Canada (`/usfs/map/`) maps:
 *
 *     #[m:<mode>;]d:<dates>[,<day>];l:<layer>[=<options>],…;@<lon>,<lat>,<zoom>z
 *
 * Links are written the way the map writes its own hash, so a link looks like one a user
 * copied from the map: fire layers sorted by ID, then other layers, overlays, and the basemap;
 * the view as a center and zoom. The map's other location form, `i:<w>,<s>,<e>,<n>`, is never
 * used: it draws a gray area-of-interest box the user cannot turn off (FR-MAP-008). An area is
 * turned into the center and zoom that frame it instead.
 *
 * `l:` replaces the map's default layers, so a basemap is always included. Per-satellite and
 * standard-processing layers exist only in modes that list them (Advanced has them all).
 *
 * Standard data first (ADR-0011 §4): for explicit past dates, each sensor shows its
 * standard-processing layer where SP covers the dates and its NRT layer after that. Where the
 * choice changes inside the period, the period is split into one link per stretch, so every
 * link shows one consistent set of layers. Smoke / Aerosols mode has no standard-processing
 * layers; it shows the map's own fire layers with the OMPS Aerosol Index (FR-MAP-009).
 */
import { type BoundingBox, checkBox, formatNumber } from "../common/area.js";
import { addDays, checkDate, describeDates, eachDay, type IsoDate } from "../common/dates.js";
import { UrlBuilderError } from "../common/errors.js";
import { FIRMS_BASE_URL, LIMITATIONS } from "../common/links.js";
import {
  type Coverage,
  type CoverageSummary,
  getSensor,
  getSource,
  planSensor,
  planSensors,
  RECENT_NOTE,
  type SensorId,
  type SensorPlan,
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
/** Days before today that each period reaches back (the map's own `getNumDays`). */
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

/**
 * The map is in plain longitude/latitude (EPSG:4326) with 256-pixel tiles: one screen pixel
 * spans 360/256/2^zoom degrees. Measured 2026-11-18 on the US/Canada map at zoom 8.6
 * (0.003624° per pixel both ways).
 */
const DEGREES_PER_PIXEL_AT_ZOOM_0 = 360 / 256;
/**
 * The window links are framed for (CSS pixels): a 14-inch laptop's browser window. Measured
 * 2026-11-18 at this size, the map fills the window below a 52-pixel header, and on load the
 * map covers part of itself: the mode menu down the right (380 pixels wide), the cursor
 * coordinates along the top (23), and the tool bar and timeline along the bottom (107).
 */
export const REFERENCE_WINDOW = { width: 1512, height: 860 } as const;
const MAP_HEADER = 52;
const MAP_COVERED = { top: 23, right: 380, bottom: 107 } as const;
/** The part of the map left in view, where links put their subject. */
export const VISIBLE_MAP = {
  width: REFERENCE_WINDOW.width - MAP_COVERED.right,
  height: REFERENCE_WINDOW.height - MAP_HEADER - MAP_COVERED.top - MAP_COVERED.bottom,
} as const;
/**
 * Boxes an agent writes for a place are rough and padded ("a rectangle around Maryland"), so
 * the view fits 90 % of the box: its outer edges may fall just outside, and the place itself
 * fills the view (the owner's Maryland link, zoom 8.6).
 */
const BOX_FILL = 0.9;
/**
 * Smoke travels hundreds of kilometres from its fires, so smoke links show at least about 12°
 * (some 1,300 km) across the visible map.
 */
export const SMOKE_MAX_ZOOM = 7.1;
/** Zoom for a center given without one. */
const CENTER_ZOOM = 8;

/**
 * OMPS Aerosol Index layers, newest first, with the dates the map's layer configuration gives
 * them (bundle firms_map.8994472e.js, 2026-11-18). Suomi NPP data stopped on 2026-11-02.
 */
const AEROSOL_LAYERS: readonly { id: string; from: IsoDate; to: IsoDate | null }[] = [
  { id: "noaa20_omps_aerosol", from: "2025-04-28", to: null },
  { id: "snpp_omps_aerosol", from: "2012-01-26", to: "2026-11-02" },
];
/**
 * Default palette, stretched ("squashed") to the values on screen, as the map writes it for
 * these layers by default; it makes faint smoke stand out.
 */
const AEROSOL_OPTIONS = "=pal-default..squash";

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

interface Resolved {
  stretches: Stretch[];
  mode: string;
  basic: boolean;
}

/** The zoom (to 0.1, rounded down) at which the visible map shows the box (BOX_FILL of it). */
export function fitZoom(box: BoundingBox): number {
  const pixelsPerDegree = Math.min(
    VISIBLE_MAP.width / ((box.east - box.west) * BOX_FILL),
    VISIBLE_MAP.height / ((box.north - box.south) * BOX_FILL),
  );
  return Math.floor(Math.log2(DEGREES_PER_PIXEL_AT_ZOOM_0 * pixelsPerDegree) * 10) / 10;
}

/**
 * The map center that puts `longitude`, `latitude` in the middle of the visible map: east of it
 * by half the menu's width and south of it by half the difference of the bottom and top bars.
 */
export function mapCenter(
  longitude: number,
  latitude: number,
  zoom: number,
): { longitude: number; latitude: number } {
  const degreesPerPixel = DEGREES_PER_PIXEL_AT_ZOOM_0 / 2 ** zoom;
  return {
    longitude: Math.min(longitude + (MAP_COVERED.right / 2) * degreesPerPixel, 180),
    latitude: Math.max(
      latitude - ((MAP_COVERED.bottom - MAP_COVERED.top) / 2) * degreesPerPixel,
      -90,
    ),
  };
}

/** `@lon,lat,zoomz` with the map's own precision: 1 decimal, 2 from zoom 9, 3 from zoom 11. */
export function formatView(longitude: number, latitude: number, zoom: number): string {
  const digits = zoom >= 11 ? 3 : zoom >= 9 ? 2 : 1;
  const fixed = (value: number) => {
    const text = value.toFixed(digits);
    return Number(text) === 0 ? (0).toFixed(digits) : text;
  };
  return `@${fixed(longitude)},${fixed(latitude)},${fixed(zoom)}z`;
}

/** The newest OMPS Aerosol Index layer with data on `day`, if any. */
export function aerosolLayer(day: IsoDate): string | undefined {
  return AEROSOL_LAYERS.find((l) => l.from <= day && (l.to === null || day <= l.to))?.id;
}

function checkDates(input: FireMapInput, today: IsoDate): { start: IsoDate; end: IsoDate } {
  if (input.start_date === undefined)
    throw new UrlBuilderError("give start_date as well as end_date");
  const start = checkDate(input.start_date, "start_date", today);
  const end = checkDate(input.end_date ?? input.start_date, "end_date", today);
  if (start > end) throw new UrlBuilderError("start_date is after end_date");
  return { start, end };
}

/**
 * Plans for the sensors asked for, or the default sensors plus Landsat where the map shows
 * Landsat by default (the US/Canada map, and Smoke / Aerosols mode) and it has data.
 */
function planFor(
  chosen: SensorId[] | undefined,
  withLandsat: boolean,
  start: IsoDate,
  end: IsoDate,
  coverage: Coverage,
  preference: "standard_first" | "nrt" = "standard_first",
): { plans: SensorPlan[]; notes: string[] } {
  const planned = planSensors(chosen, start, end, coverage, preference);
  if (chosen || !withLandsat) return planned;
  const landsat = planSensor("landsat", start, end, coverage, preference);
  if (!landsat.runs.length) return planned;
  return { plans: [...planned.plans, landsat], notes: [...planned.notes, ...landsat.notes] };
}

function resolveSmoke(
  input: FireMapInput,
  chosen: SensorId[] | undefined,
  coverage: Coverage,
  today: IsoDate,
  notes: string[],
): Resolved {
  let start: IsoDate;
  let end: IsoDate;
  if (input.start_date === undefined && input.end_date === undefined) {
    const period = input.period ?? "24hrs";
    if (!PERIODS.includes(period))
      throw new UrlBuilderError(`period must be one of ${PERIODS.join(", ")}`);
    // Smoke mode's date picker takes days; the period becomes the same days, written out.
    end = today;
    start = addDays(today, -PERIOD_PAST_DAYS[period]);
  } else {
    ({ start, end } = checkDates(input, today));
  }
  // The map's fire layers here are its everyday layers; a sensor is shown if FIRMS has any data
  // for it in the period. Notes about SP versus NRT do not apply to these layers.
  const { plans, notes: planNotes } = planFor(chosen, true, start, end, coverage);
  notes.push(
    ...planNotes.filter(
      (n) => n.includes("left out of the default") || n.includes(": no data for "),
    ),
    "Smoke / Aerosols mode has no standard-processing fire layers; it shows the map's everyday fire layers. For standard-processing detections over the same dates, build an Advanced-mode link.",
  );
  const sources = plans
    .filter((plan) => plan.runs.length)
    .map((plan) => getSensor(plan.sensor).nrt_source);
  // `d:<range>,<day>`: the day picks which daily image (the Aerosol Index) is shown.
  const dates = start === end ? start : `${start}..${end},${end}`;
  return { stretches: [{ dates, start, end, sources }], mode: "smoke", basic: false };
}

function resolveStretches(
  input: FireMapInput,
  mapName: MapName,
  mode: string | undefined,
  coverage: Coverage,
  today: IsoDate,
  notes: string[],
): Resolved {
  const hasDates = input.start_date !== undefined || input.end_date !== undefined;
  if (input.period !== undefined && hasDates) {
    throw new UrlBuilderError("give either a period or start_date/end_date, not both");
  }
  const chosen = input.sensors?.length ? input.sensors.map((s) => getSensor(s).id) : undefined;
  const withLandsat = mapName === "us-canada";
  if (mode === "smoke") return resolveSmoke(input, chosen, coverage, today, notes);

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
    const { plans } = planFor(chosen, withLandsat, windowStart, today, coverage, "nrt");
    notes.push(RECENT_NOTE);
    return {
      stretches: [
        {
          dates: period,
          start: null,
          end: null,
          sources: (chosen ?? plans.map((p) => p.sensor)).map((s) => getSensor(s).nrt_source),
        },
      ],
      mode: resolvedMode,
      basic: false,
    };
  }

  const { start, end } = checkDates(input, today);
  const resolvedMode = mode ?? "advanced";
  if (resolvedMode === "basic" && !chosen) {
    notes.push(
      "Basic mode shows FIRMS's combined fire layer; standard-processing layers need mode 'advanced'.",
    );
    const dates = start === end ? start : `${start}..${end}`;
    return { stretches: [{ dates, start, end, sources: [] }], mode: resolvedMode, basic: true };
  }

  const { plans, notes: planNotes } = planFor(chosen, withLandsat, start, end, coverage);
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

/** A hash layer value's ID, without `=<options>`. */
const layerId = (value: string) => value.split("=")[0] as string;

function checkLayers(layers: string[], mode: string, basemap: string): void {
  const ids = layers.map(layerId);
  const unknown = ids.filter((id) => !MAP_CATALOG.layers.has(id));
  if (unknown.length) throw new UrlBuilderError(`unknown Fire Map layer(s): ${unknown.join(", ")}`);
  const allowed = allowedLayers(mode);
  const notInMode = ids.filter((id) => !allowed.has(id));
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

/**
 * Basemap and overlays when none are given. Fire detections stand out best on Dark Gray; Basic
 * mode has no Dark Gray, and the Aerosol Index reads best over Blue Marble, so those keep the
 * map's own Blue Marble. A view of a place gets the detailed borders and roads overlay as points
 * of reference (owner feedback, 2026-11-18); the map's default world view keeps the basic one.
 */
function defaultBackground(
  mode: string,
  regional: boolean,
): { basemap: string; overlays: string[] } {
  const basemap = allowedLayers(mode).has("dark_gray") && mode !== "smoke" ? "dark_gray" : "earth";
  return { basemap, overlays: [regional ? "countries" : "country-outline"] };
}

function processingText(sources: SourceId[], mode: string): string {
  if (!sources.length) return "FIRMS's combined fire layer";
  if (mode === "smoke") return "the map's everyday fire layers";
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

  const notes: string[] = [];
  const { stretches, mode, basic } = resolveStretches(
    input,
    mapName,
    input.mode,
    coverage,
    today,
    notes,
  );
  const smoke = mode === "smoke";

  // View: always a center and zoom. An area is framed (never drawn as a box, FR-MAP-008), and an
  // area or center is put in the middle of the part of the map left in view.
  const clampZoom = (zoom: number) => Math.min(Math.max(zoom, limits.min_zoom), limits.max_zoom);
  let longitude: number;
  let latitude: number;
  let zoom: number;
  let where: string;
  const regional = input.area !== undefined || input.center !== undefined;
  if (input.area !== undefined) {
    const box = checkBox(input.area);
    longitude = (box.west + box.east) / 2;
    latitude = (box.south + box.north) / 2;
    zoom = clampZoom(smoke ? Math.min(fitZoom(box), SMOKE_MAX_ZOOM) : fitZoom(box));
    where = `the area west ${formatNumber(box.west)}, south ${formatNumber(box.south)}, east ${formatNumber(box.east)}, north ${formatNumber(box.north)}`;
  } else {
    const view = DEFAULT_VIEW[mapName];
    ({ longitude, latitude } = input.center ?? view);
    if (!(Math.abs(longitude) <= 180 && Math.abs(latitude) <= 90)) {
      throw new UrlBuilderError("center must have longitude -180 to 180 and latitude -90 to 90");
    }
    zoom = input.zoom ?? (input.center ? (smoke ? SMOKE_MAX_ZOOM : CENTER_ZOOM) : view.zoom);
    if (!(zoom >= limits.min_zoom && zoom <= limits.max_zoom)) {
      throw new UrlBuilderError(
        `zoom must be between ${limits.min_zoom} and ${limits.max_zoom} for this map`,
      );
    }
    where = input.center
      ? `longitude ${formatNumber(Math.round(longitude * 1e4) / 1e4)}, latitude ${formatNumber(Math.round(latitude * 1e4) / 1e4)}`
      : "";
  }
  const view = regional ? mapCenter(longitude, latitude, zoom) : { longitude, latitude };
  const location = formatView(view.longitude, view.latitude, zoom);
  const zoomText = location.slice(1, -1).split(",")[2];
  where = where
    ? `${where}, in the middle of the map's visible area (left of its menu) at zoom ${zoomText}${smoke ? ", a regional view, because smoke travels far from its fires" : ""}`
    : `the map's default view at zoom ${zoomText}`;

  const background = defaultBackground(mode, regional);
  const basemap = input.basemap ?? background.basemap;
  const overlays = input.overlays ?? background.overlays;
  const query = (input.referral ?? true) ? `?${new URLSearchParams(REFERRAL)}` : "";
  const modeLabel = MAP_CATALOG.modes.get(mode)?.label ?? mode;
  const overlayText = overlays.length ? ` with ${overlays.map(layerTitle).join(", ")}` : "";

  const links = stretches.map((stretch): FireMapLink => {
    // Fire layers sorted by ID, as the map writes them.
    const fireLayers = basic
      ? [BASIC_FIRE_LAYER]
      : stretch.sources.flatMap((id) => getSource(id).map_layers).sort();
    const aerosol = smoke && stretch.end ? aerosolLayer(stretch.end) : undefined;
    const layers = [
      ...new Set([
        ...fireLayers,
        ...(input.extra_layers ?? []),
        ...(aerosol ? [`${aerosol}${AEROSOL_OPTIONS}`] : []),
        ...overlays,
        basemap,
      ]),
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
    const aerosolText = aerosol
      ? `, with the ${layerTitle(aerosol)} for ${stretch.end} (UTC) over them (FIRMS describes this mode as "${MAP_CATALOG.modes.get("smoke")?.description ?? ""}")`
      : "";
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
        `${fireLayers.map(layerTitle).join(", ")} (${processingText(stretch.sources, mode)}) for ${datesText}${aerosolText}, over ${where}, ` +
        `on the ${layerTitle(basemap)} basemap${overlayText}. The map, not this server, renders FIRMS data; times are UTC.`,
    };
  });
  if (smoke && links.length && !links.some((l) => l.layers.some((id) => id.includes("aerosol")))) {
    notes.push(
      "FIRMS has no OMPS Aerosol Index layer for these dates, so the link shows fires only.",
    );
  }
  if (!links.length)
    notes.push("No fire data source covers the requested dates, so no link was built.");

  return { links, notes, coverage: summarizeCoverage(coverage), limitations: LIMITATIONS };
}
