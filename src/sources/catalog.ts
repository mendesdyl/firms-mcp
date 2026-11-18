/**
 * FIRMS active-fire sources (FR-DATA-010, FR-DATA-015), read from the language-neutral
 * `sources.json`. Each sensor pairs a standard-processing (SP) source, where FIRMS has one, with
 * its near-real-time (NRT) source; the builders prefer SP wherever it covers the dates
 * (ADR-0011 §4).
 */
import * as z from "zod/v4";
import { UrlBuilderError } from "../common/errors.js";
import data from "./sources.json" with { type: "json" };

export const SENSOR_IDS = [
  "viirs_noaa20",
  "viirs_noaa21",
  "viirs_snpp",
  "modis",
  "landsat",
] as const;
export const SOURCE_IDS = [
  "VIIRS_NOAA20_SP",
  "VIIRS_NOAA21_SP",
  "VIIRS_SNPP_SP",
  "MODIS_SP",
  "VIIRS_NOAA20_NRT",
  "VIIRS_NOAA21_NRT",
  "VIIRS_SNPP_NRT",
  "MODIS_NRT",
  "LANDSAT_NRT",
] as const;

export const SensorId = z.enum(SENSOR_IDS);
export type SensorId = z.infer<typeof SensorId>;
export const SourceId = z.enum(SOURCE_IDS);
export type SourceId = z.infer<typeof SourceId>;
export type Processing = "SP" | "NRT";

const IsoDate = z.string().regex(/^\d{4}-\d{2}-\d{2}$/);

const SensorSchema = z.strictObject({
  id: SensorId,
  label: z.string().min(1),
  sp_source: SourceId.nullable(),
  nrt_source: SourceId,
  kml_sensor: z.string().min(1),
  default: z.boolean(),
});
export type Sensor = z.infer<typeof SensorSchema>;

const SourceSchema = z.strictObject({
  id: SourceId,
  label: z.string().min(1),
  sensor: SensorId,
  processing: z.enum(["SP", "NRT"]),
  instrument: z.string().min(1),
  platforms: z.array(z.string().min(1)).min(1),
  nominal_resolution_m: z.number().int().positive(),
  coverage: z.string().min(1),
  map_layers: z.array(z.string().min(1)).min(1),
  map_dates_key: z.string().min(1),
  knowledge_entries: z.array(z.string().min(1)),
});
export type Source = z.infer<typeof SourceSchema>;

const CatalogSchema = z.strictObject({
  retrieved: IsoDate,
  provenance: z.string().min(1),
  sensors: z.array(SensorSchema),
  sources: z.array(SourceSchema),
  coverage_snapshot: z.strictObject({
    retrieved: IsoDate,
    dates: z.record(z.string(), z.tuple([IsoDate, IsoDate])),
  }),
});

const catalog = CatalogSchema.parse(data);

/** Every source, standard processing first (FR-DATA-015). */
export const SOURCES: readonly Source[] = [
  ...catalog.sources.filter((s) => s.processing === "SP"),
  ...catalog.sources.filter((s) => s.processing === "NRT"),
];
export const SENSORS: readonly Sensor[] = catalog.sensors;
/** Sensors used when the caller does not choose: the global ones (Landsat is US/Canada only). */
export const DEFAULT_SENSORS: readonly SensorId[] = SENSORS.filter((s) => s.default).map(
  (s) => s.id,
);
export const CATALOG_RETRIEVED = catalog.retrieved;
export const CATALOG_PROVENANCE = catalog.provenance;
/** Map date service response saved with the catalog; the fallback when the service fails. */
export const COVERAGE_SNAPSHOT = catalog.coverage_snapshot;

const sourceById = new Map(SOURCES.map((s) => [s.id as string, s]));
const sensorById = new Map(SENSORS.map((s) => [s.id as string, s]));

export function getSource(id: string): Source {
  const source = sourceById.get(id.toUpperCase());
  if (!source) {
    throw new UrlBuilderError(
      `unknown FIRMS source ${JSON.stringify(id)}; valid sources: ${SOURCE_IDS.join(", ")}`,
    );
  }
  return source;
}

export function getSensor(id: string): Sensor {
  const sensor = sensorById.get(id.toLowerCase());
  if (!sensor) {
    throw new UrlBuilderError(
      `unknown sensor ${JSON.stringify(id)}; valid sensors: ${SENSOR_IDS.join(", ")}`,
    );
  }
  return sensor;
}

export interface ListedSource extends Source {
  /** Standard-processing sources are preferred wherever they cover the dates. */
  preferred: boolean;
}

/** The catalog as a tool returns it: SP first, each marked preferred or not (FR-DATA-015). */
export function listSources(): ListedSource[] {
  return SOURCES.map((s) => ({ ...s, preferred: s.processing === "SP" }));
}
