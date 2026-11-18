/**
 * The FIRMS Fire Map layer catalog (ADR-0006), read from the language-neutral `catalog.json`:
 * maps, modes, modules, and layers from the map's own configuration. A mode can display, for
 * each of its modules, the module's explicit `layer_refs`, or else every layer with the
 * module's `tag`. The map silently drops layers a mode cannot display, so links are checked
 * against this before they are returned (FR-MAP-002).
 */
import * as z from "zod/v4";
import data from "./catalog.json" with { type: "json" };

const MapSchema = z.object({ path: z.string(), min_zoom: z.number(), max_zoom: z.number() });
const ModeSchema = z.object({
  id: z.string(),
  label: z.string(),
  modules: z.array(z.string()).default([]),
});
const ModuleSchema = z.object({
  id: z.string(),
  label: z.string().optional(),
  tag: z.string().optional(),
  layer_refs: z.array(z.string()).optional(),
});
const LayerSchema = z.object({
  id: z.string(),
  title: z.string(),
  category: z.enum(["basemap", "layer", "overlay"]),
  tag: z.string(),
});
const CatalogSchema = z.object({
  retrieved: z.string(),
  source: z.string(),
  maps: z.record(z.string(), MapSchema),
  default_view: z.object({ dates: z.string(), layers: z.array(z.string()) }),
  modes: z.array(ModeSchema),
  modules: z.array(ModuleSchema),
  layers: z.array(LayerSchema),
});

export type MapName = "global" | "us-canada";
export type MapLayer = z.infer<typeof LayerSchema>;
export type MapMode = z.infer<typeof ModeSchema>;

const parsed = CatalogSchema.parse(data);

export const MAP_CATALOG = {
  retrieved: parsed.retrieved,
  source: parsed.source,
  maps: parsed.maps as Record<MapName, z.infer<typeof MapSchema>>,
  defaultView: parsed.default_view,
  modes: new Map(parsed.modes.map((m) => [m.id, m])),
  modules: new Map(parsed.modules.map((m) => [m.id, m])),
  layers: new Map(parsed.layers.map((l) => [l.id, l])),
};

/** Modes a link may name (the others are pages, not map views). */
export const LINKABLE_MODES = [
  "basic",
  "advanced",
  "burned_area",
  "smoke",
  "experimental",
] as const;
export type LinkableMode = (typeof LINKABLE_MODES)[number];

const allowedCache = new Map<string, ReadonlySet<string>>();

/** Layer IDs `mode` can display. */
export function allowedLayers(mode: string): ReadonlySet<string> {
  const cached = allowedCache.get(mode);
  if (cached) return cached;
  const allowed = new Set<string>();
  for (const moduleId of MAP_CATALOG.modes.get(mode)?.modules ?? []) {
    const module = MAP_CATALOG.modules.get(moduleId);
    if (module?.layer_refs?.length) {
      for (const id of module.layer_refs) allowed.add(id);
    } else if (module?.tag) {
      for (const layer of MAP_CATALOG.layers.values())
        if (layer.tag === module.tag) allowed.add(layer.id);
    }
  }
  for (const id of allowed) if (!MAP_CATALOG.layers.has(id)) allowed.delete(id);
  allowedCache.set(mode, allowed);
  return allowed;
}

export function layerTitle(id: string): string {
  return (MAP_CATALOG.layers.get(id)?.title ?? id).trim();
}
