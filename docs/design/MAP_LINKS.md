# FIRMS Fire Map Links — Design

Implements [ADR-0006](../decisions/0006-firms-fire-map-deep-links.md).
Requirements: FR-MAP-001 … FR-MAP-006. Code: `src/firms_mcp/maplinks/`.

## Grammar (derived from the map's own parser; verified in the browser)

```
https://firms.modaps.eosdis.nasa.gov/map/[?utm_source=firms-mcp&utm_medium=mcp]#
    [m:<mode>;]d:<dates>;l:<layer>,…;(i:<w>,<s>,<e>,<n> | @<lon>,<lat>,<zoom>z)
```

| Segment | Builder rule |
|---|---|
| `m:` | Omitted for Basic. Set to `advanced` automatically when per-satellite sources are requested; `burned_area`, `smoke`, `experimental` allowed explicitly |
| `d:` | One of `today`, `24hrs` (default — the map's own default), `48hrs`, `72hrs`, `7days`; or `YYYY-MM-DD`; or `YYYY-MM-DD..YYYY-MM-DD` (UTC days). Future dates rejected |
| `l:` | Fire layers first (from API sources via the source catalog), then extra layers, overlays (default `country-outline`, the map's default overlay), then the basemap (default `earth`, Blue Marble). Every ID must exist in the catalog **and** be available in the chosen mode |
| `i:` | Used when an area is given: the map fits the view and draws the box |
| `@…z` | Used otherwise: center (EPSG:4326) and zoom within the map's limits (global 1–16; US/Canada 4–16) |

Modes and layer availability come from the catalog snapshot
(`src/firms_mcp/maplinks/catalog.json`, 267 layers, 9 modes, 37 modules, captured
2026-10-09). A mode's available layers are, for each of its modules, the module's explicit
`layer_refs`, or else every layer with the module's `tag`.

## Verification performed (2026-10-09/10, cold page loads)

| Link | Result |
|---|---|
| `/map/#d:24hrs;@-118.5,34.1,7.0z` | Defaults: `earth`, `fires_all`, `country-outline` |
| `/map/#d:24hrs;l:fires_viirs_noaa20,fires_viirs_snpp,fires_modis_aqua,earth;@…` | Per-satellite layers **dropped** (Basic mode) |
| `/map/#m:advanced;d:24hrs;l:fires_viirs_noaa20,fires_viirs_snpp,fires_modis_aqua,earth;@…` | All four layers visible |
| `/map/?utm_source=firms-mcp&utm_medium=mcp#m:advanced;d:2025-01-07..2025-01-09;l:fires_viirs_noaa20,fires_viirs_snpp,country-outline,street;i:-119.2,33.8,-117.6,34.6` (builder output) | Exactly those layers; box drawn; view fit at zoom 8; dates applied |
| `/usfs/map/#m:advanced;d:2025-01-07..2025-01-09;l:fires_viirs_noaa20,fires_viirs_snpp,street;i:…` | Same behaviour on the US/Canada map (270 layers; minimum zoom 4) |

## Keeping it current

`uv run python scripts/check_map_catalog.py` compares the snapshot with the live map's
configuration and exits non-zero if a layer the builder depends on has disappeared
(risk R2; running-list item LU-05 asks FIRMS to confirm the grammar is stable).
