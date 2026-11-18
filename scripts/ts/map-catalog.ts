/**
 * Checks the Fire Map layer catalog (`src/maplinks/catalog.json`) against the live map's
 * configuration (WK-29; risk R2, running-list LU-05). The map silently drops layers it does
 * not know (II-29), so a renamed or removed layer would make links show nothing.
 *
 *   npm run map-catalog          report differences; exit 1 if a layer the builders use is gone
 *
 * Contacts FIRMS (two requests); run by hand or before a release, never in CI tests.
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { MAP_CATALOG } from "../../src/maplinks/catalog.js";
import { SOURCES } from "../../src/sources/catalog.js";

export const MAP_PAGE = "https://firms.modaps.eosdis.nasa.gov/map/";

/** The bundle path in the map page, quoted or not (`src=/dist/firms_map.<hash>.js`). */
export function bundlePath(page: string): string | undefined {
  return /\/dist\/firms_map\.[0-9a-f]+\.js/.exec(page)?.[0];
}

/** Values the bundle embeds with `JSON.parse('…')`. */
export function jsonBlobs(bundle: string): unknown[] {
  const blobs: unknown[] = [];
  for (const match of bundle.matchAll(/JSON\.parse\('((?:[^'\\]|\\.)*)'\)/g)) {
    const text = match[1] ?? "";
    for (const candidate of [text, text.replaceAll("\\'", "'")]) {
      try {
        blobs.push(JSON.parse(candidate));
        break;
      } catch {
        // try the unescaped form, then give up on this blob
      }
    }
  }
  return blobs;
}

/** Layer IDs in the bundle's layer configuration (objects with `properties` and `layers`). */
export function liveLayerIds(bundle: string): Set<string> {
  const ids = new Set<string>();
  for (const blob of jsonBlobs(bundle)) {
    if (typeof blob !== "object" || blob === null || !("properties" in blob)) continue;
    const layers = (blob as { layers?: unknown }).layers;
    if (!Array.isArray(layers)) continue;
    for (const layer of layers) {
      const id = (layer as { id?: unknown })?.id;
      if (typeof id === "string") ids.add(id);
    }
  }
  return ids;
}

/** Layers the builders put in links: source layers, the Basic fire layer, defaults. */
export function criticalLayers(): Set<string> {
  return new Set([
    ...SOURCES.flatMap((s) => s.map_layers),
    "fire_layers_basic",
    ...MAP_CATALOG.defaultView.layers,
    "earth",
    "street",
    "topo",
    "firefly",
    "country-outline",
  ]);
}

export interface CatalogDiff {
  added: string[];
  missing: string[];
  critical: string[];
}

export function diffCatalog(live: Set<string>, shipped: Iterable<string>): CatalogDiff {
  const shippedIds = new Set(shipped);
  // Runtime-only layers (drawing tools, virtual groups) are not in the bundle configuration.
  const missing = [...shippedIds]
    .filter((id) => !live.has(id) && !id.startsWith("_vl_") && !id.startsWith("draw"))
    .sort();
  const critical = criticalLayers();
  return {
    added: [...live].filter((id) => !shippedIds.has(id)).sort(),
    missing,
    critical: missing.filter((id) => critical.has(id)),
  };
}

async function main(): Promise<number> {
  const page = await (await fetch(MAP_PAGE)).text();
  const path = bundlePath(page);
  if (!path) {
    console.error("could not find the map bundle in the map page");
    return 2;
  }
  const bundle = await (await fetch(new URL(path, MAP_PAGE))).text();
  const live = liveLayerIds(bundle);
  if (live.size === 0) {
    console.error(`no layer configuration found in ${path}; the bundle format may have changed`);
    return 2;
  }
  const shipped = JSON.parse(readFileSync("src/maplinks/catalog.json", "utf8")) as {
    retrieved: string;
    layers: { id: string }[];
  };
  const diff = diffCatalog(
    live,
    shipped.layers.map((l) => l.id),
  );
  console.log(`bundle: ${path}`);
  console.log(
    `layers in live config: ${live.size}; in catalog (${shipped.retrieved}): ${shipped.layers.length}`,
  );
  console.log(`added layers: ${diff.added.join(", ") || "none"}`);
  console.log(`layers no longer configured: ${diff.missing.join(", ") || "none"}`);
  if (diff.critical.length) {
    console.log(
      `CRITICAL: layers the link builders use are missing from the live map: ${diff.critical.join(", ")}`,
    );
    return 1;
  }
  console.log("ok: every layer the link builders use is configured on the live map");
  return 0;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  process.exitCode = await main();
}
