/**
 * KML fire footprint download links (FR-DATA-011), from the FIRMS `kml_fire_footprints` page
 * (checked 2026-11-18): no MAP_KEY; the regions, periods, and sensors below; Landsat only for
 * Canada and the contiguous US and Hawaii. The files are near real-time only and download to
 * the user's computer, so tools offer them only to users who work with GIS tools (ADR-0011 §7).
 */
import { UrlBuilderError } from "../common/errors.js";
import { FIRMS_BASE_URL, LIMITATIONS } from "../common/links.js";
import { getSensor, type SensorId } from "../sources/catalog.js";

export const KML_REGIONS = {
  canada: "Canada",
  alaska: "Alaska",
  usa_contiguous_and_hawaii: "USA (Conterminous) and Hawaii",
  central_america: "Central America",
  south_america: "South America",
  europe: "Europe",
  northern_and_central_africa: "Northern and Central Africa",
  southern_africa: "Southern Africa",
  russia_asia: "Russia and Asia",
  south_asia: "South Asia",
  southeast_asia: "South East Asia",
  australia_newzealand: "Australia and New Zealand",
} as const;
export type KmlRegion = keyof typeof KML_REGIONS;

export const KML_PERIODS = {
  "24h": "24 hours",
  "48h": "48 hours",
  "72h": "72 hours",
  "7d": "7 days",
} as const;
export type KmlPeriod = keyof typeof KML_PERIODS;

export const LANDSAT_KML_REGIONS: readonly KmlRegion[] = ["canada", "usa_contiguous_and_hawaii"];

export interface KmlInput {
  region: KmlRegion;
  period: KmlPeriod;
  sensor: SensorId;
}

export interface KmlResult {
  url: string;
  region: KmlRegion;
  region_label: string;
  period: KmlPeriod;
  period_label: string;
  sensor: SensorId;
  sensor_label: string;
  downloads_file: true;
  note: string;
  limitations: string;
}

export const KML_NOTE =
  "The link downloads a KML file of fire points and footprints (near real-time data only); it opens in a GIS tool such as Google Earth or QGIS, not in a browser. Footprint colors show time since detection.";

export function buildKmlFootprintUrl(input: KmlInput): KmlResult {
  if (!Object.hasOwn(KML_REGIONS, input.region)) {
    throw new UrlBuilderError(
      `unknown region ${JSON.stringify(input.region)}; valid regions: ${Object.keys(KML_REGIONS).join(", ")}`,
    );
  }
  if (!Object.hasOwn(KML_PERIODS, input.period)) {
    throw new UrlBuilderError(
      `unknown period ${JSON.stringify(input.period)}; valid periods: ${Object.keys(KML_PERIODS).join(", ")}`,
    );
  }
  const sensor = getSensor(input.sensor);
  if (sensor.id === "landsat" && !LANDSAT_KML_REGIONS.includes(input.region)) {
    throw new UrlBuilderError(
      `Landsat footprints are only offered for ${LANDSAT_KML_REGIONS.join(" and ")}`,
    );
  }
  const query = new URLSearchParams({
    region: input.region,
    date_span: input.period,
    sensor: sensor.kml_sensor,
  });
  return {
    url: `${FIRMS_BASE_URL}/api/kml_fire_footprints/?${query}`,
    region: input.region,
    region_label: KML_REGIONS[input.region],
    period: input.period,
    period_label: KML_PERIODS[input.period],
    sensor: sensor.id,
    sensor_label: sensor.label,
    downloads_file: true,
    note: KML_NOTE,
    limitations: LIMITATIONS,
  };
}
