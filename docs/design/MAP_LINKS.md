# FIRMS Fire Map Links — Design

Implements [ADR-0006](../decisions/0006-firms-fire-map-deep-links.md).
Requirements: FR-MAP-001 … FR-MAP-007. Code: `src/maplinks/` (TypeScript; standard data first
as described in [URL builders](URL_BUILDERS.md)); iteration 1's Python builder is at tag
`v0-iteration-1`.

## Grammar (derived from the map's own parser; verified in the browser)

```
https://firms.modaps.eosdis.nasa.gov/map/[?utm_source=firms-mcp&utm_medium=mcp]#
    [m:<mode>;]d:<dates>[,<day>];l:<layer>[=<options>],…;@<lon>,<lat>,<zoom>z
```

Links are written the way the map writes its own hash (its `update`, `datesToString`,
`getHashLayerInformation`, and `locationToString` functions), so they look like a link copied
from the map.

| Segment | Builder rule |
|---|---|
| `m:` | Omitted for Basic. Set to `advanced` automatically when per-satellite sources are requested or dates are past; `burned_area`, `smoke`, `experimental` allowed explicitly. Agents are told to choose `smoke` themselves for smoke, haze, or air-quality questions |
| `d:` | One of `today`, `24hrs` (default — the map's own default), `48hrs`, `72hrs`, `7days`; or `YYYY-MM-DD`; or `YYYY-MM-DD..YYYY-MM-DD` (UTC days). Future dates rejected. In Smoke / Aerosols mode a period is written as the same days (`7days` → today−6 … today, the map's own `getNumDays`) and a range ends with `,<last day>`: the map's single day, which picks the daily image (the Aerosol Index) shown; without it the map uses the first day |
| `l:` | Fire layers sorted by ID (as the map writes them), then extra layers, the Aerosol Index in smoke mode, overlays, and the basemap. Every ID must exist in the catalog **and** be available in the chosen mode. Default background: Dark Gray with no overlay (it has borders and roads) where the mode offers it; Blue Marble with `country-outline` in Basic (no Dark Gray) and Smoke / Aerosols modes |
| `=<options>` | Layer options. `=pal-<palette>[..squash]` sets an imagery layer's palette; `squash` stretches it to the values on screen. The map writes `noaa20_omps_aerosol=pal-default..squash` for its default, and so do we |
| `@…z` | Always used. Center (EPSG:4326) and zoom within the map's limits (global 1–16; US/Canada 4–16), with the map's precision: 1 decimal, 2 from zoom 9, 3 from zoom 11. An area is turned into its center and the zoom that fits it into a 1280 x 720 map, rounded down to 0.1; smoke links are capped at zoom 7.1 (about 13° across) because smoke travels far from its fires |
| `i:` | **Never used** (II-33, FR-MAP-008). The map fits the view to `i:<w>,<s>,<e>,<n>` but draws a gray area-of-interest box the user cannot turn off, and fits with a coarse whole-number zoom |

**Scale.** The map is plain longitude/latitude with 256-pixel tiles: one CSS pixel spans
360/256/2^zoom degrees. Measured 2026-11-18 on the US/Canada map at zoom 8.6 by reading the
map's cursor coordinates 600 px apart (0.003624° per pixel, the same east-west and
north-south).

**Aerosol Index layers** (dates from the map's layer configuration, 2026-11-18):
`noaa20_omps_aerosol` from 2025-04-28 (preferred); `snpp_omps_aerosol` 2012-01-26 to
2026-11-02. A smoke link uses the newest one with data on its last day, or none (with a note).

**Referral parameters** must stay in the query, before the `#`. Placed after it they become
part of the map state; the map parses past them and rewrites its hash without them, and
`location.search` is empty, so FIRMS would never see the referral (checked 2026-11-18). Agents
show links as named Markdown links instead, so users need not read the URL.

Modes and layer availability come from the catalog snapshot
(`src/maplinks/catalog.json`, 269 layers, 9 modes, 37 modules; captured 2026-10-09 and
refreshed from the map bundle `firms_map.8994472e.js` on 2026-11-18). The refresh found the
Basic-mode fire layer renamed from `fires_all` to `fire_layers_basic`, and new
`fires_viirs_noaa21_sp` and `fires_viirs_noaa21_nrt` layers in Advanced mode (II-29, II-30).
The iteration-1 copy was not changed; it was removed with the Python server (WK-30). A mode's available layers are, for each of its modules, the module's explicit
`layer_refs`, or else every layer with the module's `tag`.

## Verification performed (2026-10-09/10, cold page loads)

| Link | Result |
|---|---|
| `/map/#d:24hrs;@-118.5,34.1,7.0z` | Defaults: `earth`, `fires_all` (renamed `fire_layers_basic` by 2026-11-18), `country-outline` |
| `/map/#d:24hrs;l:fires_viirs_noaa20,fires_viirs_snpp,fires_modis_aqua,earth;@…` | Per-satellite layers **dropped** (Basic mode) |
| `/map/#m:advanced;d:24hrs;l:fires_viirs_noaa20,fires_viirs_snpp,fires_modis_aqua,earth;@…` | All four layers visible |
| `/map/?utm_source=firms-mcp&utm_medium=mcp#m:advanced;d:2025-01-07..2025-01-09;l:fires_viirs_noaa20,fires_viirs_snpp,country-outline,street;i:-119.2,33.8,-117.6,34.6` (builder output) | Exactly those layers; box drawn; view fit at zoom 8; dates applied |
| `/usfs/map/#m:advanced;d:2025-01-07..2025-01-09;l:fires_viirs_noaa20,fires_viirs_snpp,street;i:…` | Same behaviour on the US/Canada map (270 layers; minimum zoom 4) |
| 2026-11-18: `/map/?utm_…#m:advanced;d:2025-01-07..2025-01-09;l:fires_viirs_noaa21_sp,fires_modis_terra_sp,fires_modis_aqua_sp,country-outline,earth;i:-119.2,33.8,-117.6,34.6` (TypeScript builder output) | All three SP layers kept, including the new NOAA-21 SP layer; dates applied; view fit at zoom 8 |
| 2026-11-18: `/map/?utm_…#d:24hrs;l:fire_layers_basic,country-outline,earth;i:…` (builder default) | Kept as given |
| 2026-11-18: `/map/#d:24hrs;l:fires_all,country-outline,earth;@…` (iteration-1 default) | `fires_all` **dropped**: the map rewrote the hash to `l:country-outline,earth` (II-29) |

| 2026-11-18: `/usfs/map/?utm_…#m:advanced;d:2026-07-01..2026-07-31;l:fires_landsat_landsat,fires_modis_aqua_sp,fires_modis_terra_sp,fires_viirs_noaa20_sp,fires_viirs_noaa21_sp,fires_viirs_snpp_sp,dark_gray;@-77.2,38.8,8.6z` (Maryland, builder output) | All six layers kept, Dark Gray basemap, 31 days, no box |
| 2026-11-18: `/map/?utm_…#m:smoke;d:2026-11-12..2026-11-18,2026-11-18;l:fires_landsat_landsat,fires_modis_aqua,fires_modis_terra,fires_viirs_noaa20,fires_viirs_noaa21,noaa20_omps_aerosol=pal-default..squash,country-outline,earth;@142.6,-9.4,7.1z` (Saibai Island, builder output) | Smoke / Aerosols mode, week of 12–18 Nov, NOAA-20 Aerosol Index on, five fire layers on, no box. The map rewrote the single day `2026-11-18` (today) as `24hrs` |
| 2026-11-18: the Maryland link with `?utm_source=…` after the zoom instead of before the `#` | Map loads; the parameters are dropped from the hash and `location.search` is empty |

## Keeping it current

`npm run map-catalog` compares the snapshot with the live map's
configuration and exits non-zero if a layer the builder depends on has disappeared
(risk R2; running-list item LU-05 asks FIRMS to confirm the grammar is stable).
