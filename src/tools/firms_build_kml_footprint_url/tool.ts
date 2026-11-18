import * as z from "zod/v4";
import {
  buildKmlFootprintUrl,
  KML_PERIODS,
  KML_REGIONS,
  type KmlPeriod,
  type KmlRegion,
} from "../../apiurls/index.js";
import { SENSOR_IDS } from "../../sources/index.js";
import { defineTool, READ_ONLY } from "../definition.js";

const regions = Object.keys(KML_REGIONS) as [KmlRegion, ...KmlRegion[]];
const periods = Object.keys(KML_PERIODS) as [KmlPeriod, ...KmlPeriod[]];

export const buildKmlFootprintTool = defineTool({
  name: "firms_build_kml_footprint_url",
  version: "1.0.0",
  title: "Build a KML fire footprint link",
  description: [
    "Build FIRMS's keyless download link for a KML file of recent fire points and pixel footprints for a region (near real-time data, last 24 hours to 7 days). The file opens in a GIS tool such as Google Earth or QGIS, not in a browser.",
    "Offer it only when the user mentions GIS, footprints, Google Earth, or QGIS; otherwise ask whether they work with KML files before suggesting it. Say that the link downloads a file. Landsat footprints exist only for canada and usa_contiguous_and_hawaii.",
  ].join("\n\n"),
  inputSchema: z.strictObject({
    region: z.enum(regions).describe("FIRMS KML region"),
    period: z.enum(periods).describe("How far back: 24h, 48h, 72h, or 7d"),
    sensor: z.enum(SENSOR_IDS).describe("Sensor whose footprints to download"),
  }),
  outputSchema: z.object({
    url: z.string(),
    region: z.string(),
    region_label: z.string(),
    period: z.string(),
    period_label: z.string(),
    sensor: z.string(),
    sensor_label: z.string(),
    downloads_file: z.literal(true),
    note: z.string(),
    limitations: z.string(),
  }),
  annotations: READ_ONLY,
  async run(input) {
    return buildKmlFootprintUrl(input);
  },
});
