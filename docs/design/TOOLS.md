# Tool Catalog

The MCP surface of the TypeScript server (iteration 2): seven tools and three resources, all
keyless. Each tool is one `defineTool` value in `src/tools/<name>/tool.ts`
([ADR-0012](../decisions/0012-typescript-project-layout-and-tool-contracts.md)); its Zod
schemas are authoritative and are exported to [`contracts/tools.json`](../../contracts/tools.json)
by `npm run contracts`. This catalog explains them. A test checks that every registered tool,
its version, and each of its parameters appear here (DOC-002). The retired iteration-1 Python tools
are in [TOOLS_ITERATION_1.md](TOOLS_ITERATION_1.md).

Design records: [ADR-0011](../decisions/0011-keyless-scope-typescript-rewrite-standard-data-first.md)
(scope, standard data first, MAP_KEY placeholder), [URL builders](URL_BUILDERS.md),
[map links](MAP_LINKS.md), [knowledge base](KNOWLEDGE_BASE.md).

## Overview

| Tool | Version | Calls FIRMS | Purpose |
|---|---|---|---|
| `firms_search_knowledge` | 1.0.0 | No | Search FIRMS's documentation; entries returned whole and verbatim |
| `firms_get_knowledge_entry` | 1.0.0 | No | Entries by ID |
| `firms_list_knowledge_topics` | 1.0.0 | No | Table of contents of the knowledge base |
| `firms_build_fire_map_url` | 1.0.1 | Map date service | FIRMS Fire Map links, standard layers first |
| `firms_build_api_url` | 1.0.0 | Map date service | FIRMS API URLs with `[MAP_KEY]`; missing-data answers |
| `firms_build_kml_footprint_url` | 1.0.0 | No | KML fire footprint download links |
| `firms_list_data_sources` | 1.0.0 | Map date service | Source catalog, standard processing first, with current dates |

All tools are read-only, non-destructive, and idempotent. `openWorldHint` is true for the
three that ask FIRMS's keyless map date service for coverage; nothing else leaves the server.
No tool accepts or needs a MAP_KEY (SEC-002, FR-AUTH-002).

## Conventions

- **Results** are structured content validated against the output schema, with the same JSON
  as text. An invalid input becomes an `isError` result whose message says what to change.
- **URL results** carry `limitations` (the server built the URL but cannot fetch, summarize,
  count, or chart what it returns), `notes` to pass on, and `coverage` (whether FIRMS's dates
  were checked live or the saved snapshot was used). API results also carry `map_key`
  (placeholder, where to get a key, where it goes) and `related` FIRMS pages.
- **Areas** are `{west, south, east, north}` in decimal degrees, longitude first; dates are
  UTC `YYYY-MM-DD`.
- **Sensors** are `viirs_noaa20`, `viirs_noaa21`, `viirs_snpp`, `modis`, `landsat`. Without
  `sensors`, the first four are used, each only for the dates FIRMS has its data (FR-URL-005).

## Knowledge

### `firms_search_knowledge` (v1.0.0)

Deterministic BM25 search over the verbatim knowledge base (FR-KB-005, FR-KB-009).

| Parameter | Default | Meaning |
|---|---|---|
| `query` | — | Plain words or FIRMS terms (1-500 characters) |
| `limit` | 3 | Entries to return, 1-10; each in full |
| `section` | all | One section ID from `firms_list_knowledge_topics` |
| `include_retired` | false | Also search entries FIRMS no longer publishes |

Returns `results` (each entry's verbatim `body`, `source_url`, `retrieved`, `content_sha256`,
`related`, plus `score` and `snippet`) and a `suggestion` when nothing matched.

### `firms_get_knowledge_entry` (v1.0.0)

| Parameter | Default | Meaning |
|---|---|---|
| `entry_ids` | — | 1-10 entry IDs |

Returns `entries` and `not_found` with the closest IDs (FR-KB-006). Retired entries carry a
`notice`.

### `firms_list_knowledge_topics` (v1.0.0)

| Parameter | Default | Meaning |
|---|---|---|
| `section` | — | List one section's entries |
| `include_entries` | false | List every entry instead of counts |
| `include_retired` | false | Include retired entries |

Returns `sections` (ID, title, count, and entries when asked) and the knowledge `sources`
(FR-KB-007). An unknown section is an error listing the valid IDs.

## URL building

### `firms_build_fire_map_url` (v1.0.1)

Links into the FIRMS Fire Map ([grammar](MAP_LINKS.md)), each with a plain-language
`description` (FR-MAP-001 … FR-MAP-010). Links match the map's own hash: no area-of-interest
box, fire layers sorted, Dark Gray basemap for fire views. Mode `smoke` adds the OMPS Aerosol
Index at a regional zoom; agents are told to choose it for smoke, haze, or air-quality questions.

| Parameter | Default | Meaning |
|---|---|---|
| `map` | global | `global` or `us-canada` |
| `area` | — | Box the map is centered and zoomed on (no box is drawn); or use `center` |
| `center` | 0, 0 (global) | `{longitude, latitude}` |
| `zoom` | fitted to `area`; 3 (8 with `center`, 7.1 in smoke mode) | Global 1-16, US/Canada 4-16 |
| `period` | 24hrs | `today`, `24hrs`, `48hrs`, `72hrs`, `7days` (NRT) |
| `start_date` | — | First UTC day, for past dates (instead of `period`) |
| `end_date` | `start_date` | Last UTC day |
| `sensors` | defaults | Sensors shown one by one (Advanced mode) |
| `mode` | automatic | `basic`, `advanced`, `burned_area`, `smoke` (fires with the Aerosol Index), `experimental` |
| `basemap` | dark_gray (earth in basic and smoke) | Basemap layer ID |
| `overlays` | none on dark_gray, else country-outline | Overlay layer IDs |
| `extra_layers` | — | More layer IDs; checked against the chosen mode |

Past dates use each sensor's standard-processing layer where SP covers them and its NRT layer
after; where that choice changes, one link per stretch is returned.

### `firms_build_api_url` (v1.0.0)

FIRMS API URLs for the user to open (FR-URL-001 … FR-URL-005, FR-KB-013).

| Parameter | Default | Meaning |
|---|---|---|
| `request` | — | `area`, `data_availability`, `map_key_status`, or `missing_data` |
| `area` | — | For `area`: a box, or `world` |
| `sensors` | defaults | For `area` and `missing_data` |
| `recent_days` | — | For `area`: the most recent 1-5 UTC days (NRT) |
| `start_date` | — | First UTC day (`area`, `missing_data`) |
| `end_date` | `start_date` | Last UTC day |
| `processing` | standard_first | For `area`: `nrt` only when the user asks for NRT |
| `source` | ALL | For `data_availability`: one source ID or `ALL` |

`area` URLs follow `/api/area/csv/[MAP_KEY]/<SOURCE>/<area>/<1-5>[/<date>]`: standard
processing where it covers the dates, NRT after it, labelled; at most 5 days per URL and 31
days per call. Days FIRMS lists as missing are noted. `missing_data` answers from the table
the weekly sync saved, with its date and the live page.

### `firms_build_kml_footprint_url` (v1.0.0)

| Parameter | Default | Meaning |
|---|---|---|
| `region` | — | One of FIRMS's 12 KML regions |
| `period` | — | `24h`, `48h`, `72h`, `7d` |
| `sensor` | — | Sensor; `landsat` only for `canada` and `usa_contiguous_and_hawaii` |

Keyless; the link downloads a KML file (NRT only) for GIS tools (FR-DATA-011). The description
and the server instructions limit it to users who mention GIS, footprints, Google Earth, or
QGIS.

## Catalog

### `firms_list_data_sources` (v1.0.0)

No parameters. Returns the nine sources, standard processing first and marked `preferred`
(FR-DATA-015), each with sensor, satellites, pixel size, coverage, API ID, map layers,
knowledge entries, and the `dates` FIRMS currently has; the five sensors with their SP and NRT
sources; and the coverage summary.

## Resources

| URI | Content |
|---|---|
| `firms://knowledge/index` | Table of contents (JSON) |
| `firms://knowledge/{entry_id}` | One entry: title, FIRMS's text verbatim, provenance line (Markdown) |
| `firms://sources` | Source catalog, standard processing first (JSON) |
