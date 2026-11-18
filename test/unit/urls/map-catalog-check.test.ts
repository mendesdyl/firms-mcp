import { describe, expect, it } from "vitest";
import {
  bundlePath,
  criticalLayers,
  diffCatalog,
  liveLayerIds,
} from "../../../scripts/ts/map-catalog.js";

const CONFIG = JSON.stringify({
  properties: { version: "2.0.0" },
  layers: [{ id: "earth" }, { id: "fire_layers_basic" }, { id: "fires_new_layer" }],
}).replaceAll("'", "\\'");
const BUNDLE = `var a=1;const c=JSON.parse('${CONFIG}');const m=JSON.parse('[1,2]');`;

describe("map catalog check", () => {
  it("[REQ-FR-MAP-002] finds the bundle in the map page, quoted or not", () => {
    expect(bundlePath("<script type=module src=/dist/firms_map.8994472e.js>")).toBe(
      "/dist/firms_map.8994472e.js",
    );
    expect(bundlePath('<script src="/dist/firms_map.927094f8.js"></script>')).toBe(
      "/dist/firms_map.927094f8.js",
    );
    expect(bundlePath("<html></html>")).toBeUndefined();
  });

  it("[REQ-FR-MAP-002] reads layer IDs from the bundle's embedded configuration", () => {
    expect([...liveLayerIds(BUNDLE)].sort()).toEqual([
      "earth",
      "fire_layers_basic",
      "fires_new_layer",
    ]);
  });

  it("[REQ-FR-MAP-002] flags a missing layer the builders use as critical", () => {
    const diff = diffCatalog(new Set(["earth", "fires_new_layer"]), [
      "earth",
      "fire_layers_basic",
      "_vl_group",
      "fires_old_unused",
    ]);
    expect(diff).toEqual({
      added: ["fires_new_layer"],
      missing: ["fire_layers_basic", "fires_old_unused"],
      critical: ["fire_layers_basic"],
    });
    expect(criticalLayers().has("fires_viirs_noaa21_sp")).toBe(true);
  });
});
