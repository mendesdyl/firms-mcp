# ADR-0006: FIRMS Fire Map deep links

- **Status:** Accepted
- **Date:** 2026-10-09
- **ARL linkage:** ARL2-M1, ARL3-M1 (component and validation), ARL5-M1 (links verified
  in the real map).

## Context

The owner observed that the FIRMS Fire Map URL "builds itself" as the view changes and
asked for links into it. The map's URL state is not documented as an API. It is a hash
fragment parsed by the map application.

The grammar was derived from the map's own parser (bundle `firms_map.927094f8.js`, map
configuration version 2.0.0, 2026-10-09) and verified with cold page loads in a browser
(see [References §5](../research/REFERENCES.md#5-firms-fire-map)):

```
https://firms.modaps.eosdis.nasa.gov/map/#<segment>;<segment>;…;@<lon>,<lat>,<zoom>z
```

| Segment | Meaning | Values |
|---|---|---|
| `t:<tab>` | Open menu tab | map UI tab ID |
| `m:<mode>` | Map mode | `basic` (default), `advanced`, `burned_area`, `smoke`, `experimental`, `learn` |
| `d:<start>[..<end>][,<single>]` | Date or range | `today`, `24hrs`, `48hrs`, `72hrs`, `7days`; `15mins`…`12hrs`; `YYYY-MM-DD`; `YYYY-MM-DD HH:MM` |
| `l:<id>[=<classifier>],…` | Visible layers (replaces defaults) | Layer IDs from the map configuration |
| `v:<type>[<components>]` | View mode | `normal`, `kiosk`, `max`; components `identify`, `menu`, `3d` |
| `i:<w>,<s>,<e>,<n>` or WKT | Area of interest; map fits to it and draws it | bounding box or `POLYGON`/`MULTIPOLYGON` |
| `tool:<name>` | Active tool | `location`, `measure` |
| `@<lon>,<lat>,<zoom>z` | Center (EPSG:4326) and zoom | lon/lat validated; zoom within map limits |

Observed behaviour that constrains link building:

- An explicit `l:` list **replaces** the defaults (`earth`, `fires_all`,
  `country-outline`), so a link must include a basemap and fire layers explicitly.
- Per-satellite fire layers (`fires_viirs_noaa20`, `fires_viirs_snpp`,
  `fires_viirs_noaa21`, `fires_modis_terra`, `fires_modis_aqua`, `fires_landsat_landsat`,
  geostationary layers, and `_nrt`/`_sp` variants) are honoured only with `m:advanced`
  (or the mode that lists them); in basic mode only `fires_all` is valid.
- Historical ranges such as `d:2025-01-07..2025-01-09` work with per-satellite layers.
- A query string before the hash (for example `?utm_source=firms-mcp&utm_medium=mcp`) does
  not affect the map.

## Decision

1. Implement a **pure, deterministic link builder** that serializes this grammar in the
   map's own segment order (`t`, `m`, `d`, `l`, `v`, location) and validates every input
   (coordinate ranges, zoom range, date formats, preset names, layer IDs against the mode).
2. Ship a **layer catalog snapshot** (IDs, titles, tags, modes) extracted from the map's
   configuration on 2026-10-09, with a script that re-extracts it and reports differences.
3. Map API detection sources to map layers (`VIIRS_NOAA20_NRT` → `fires_viirs_noaa20`, …)
   so a data query can be reproduced as a link exactly.
4. Prefer `i:<bbox>` when the caller has a bounding box (the map fits the view), otherwise
   `@lon,lat,zoomz`.
5. Support the global map (`/map/`) and the US/Canada map (`/usfs/map/`), which shares the
   hash format.
6. Append `utm_source=firms-mcp&utm_medium=mcp` by default (mirroring the Earthdata MCP's
   referral tagging so FIRMS can measure MCP-originated traffic); configurable and
   removable.
7. Every link is returned with a plain-language description of what it will show, so the
   agent can tell the user.

## Alternatives considered

| Alternative | Why rejected |
|---|---|
| Link only to the map's front page | Loses the owner's main idea: reproducing the agent's view |
| Screenshot or image endpoints | Not documented; the in-client map ([ADR-0009](0009-interactive-map-via-mcp-apps.md)) covers visualization |
| Let the model write map URLs freely | Models cannot know the undocumented grammar or the mode rules; invalid layers are silently dropped by the map |

## Consequences

- The grammar may change without notice (risk R2). Mitigations: the catalog refresh
  script, grammar tests, and running-list item LU-05 (confirm with FIRMS).
- Links reproduce FIRMS's view; the map, not this server, renders FIRMS data.
