# Tool Catalog

The MCP surface of the FIRMS MCP server: nine tools, three resources, and two prompts.
Each tool is defined by its directory under `src/firms_mcp/tools/<name>/`
([ADR-0002](../decisions/0002-follow-nasa-earthdata-mcp-conventions.md)): `manifest.json`
holds the name, version, title, the description the model reads, tags, annotations,
`require_auth`, and examples; `models.py` holds the Pydantic input and output models;
`tool.py` holds the entry function. The JSON schemas clients receive are generated from
those models, so this catalog explains the tools but the schemas are authoritative.
A test checks that every registered tool, its version, and each of its parameters appear
here (DOC-002).

Design records: [ADR-0003](../decisions/0003-target-mcp-2026-07-28-with-backward-compatibility.md)
(protocol), [ADR-0004](../decisions/0004-authentication-bring-your-own-map-key.md) (keys),
[ADR-0006](../decisions/0006-firms-fire-map-deep-links.md) (links),
[ADR-0007](../decisions/0007-data-tool-design.md) (data tools). Architecture:
[ARCHITECTURE.md](ARCHITECTURE.md).

## Overview

| Tool | Version | Needs a MAP_KEY | Open world | Purpose |
|---|---|---|---|---|
| `search_knowledge` | 1.0.0 | No | No | Search FIRMS's documentation; entries returned whole and verbatim |
| `get_knowledge_entry` | 1.0.0 | No | No | Entries by ID |
| `list_knowledge_topics` | 1.0.0 | No | No | Table of contents of the knowledge base |
| `get_fire_data_sources` | 1.0.0 | No | No | Catalog of FIRMS detection sources |
| `get_data_availability` | 1.0.0 | Optional | Yes | Date coverage per source |
| `get_fire_detections` | 1.0.0 | Yes | Yes | Detections with summaries, caveats, disclaimer, citation, map link |
| `get_map_key_status` | 1.0.0 | Yes | Yes | Transactions used by the connected key |
| `build_fire_map_link` | 1.0.0 | No | No | FIRMS Fire Map links |
| `get_fire_footprint_kml_links` | 1.0.0 | No | No | KMZ footprint download links |

All tools are read-only, non-destructive, and idempotent (`readOnlyHint: true`,
`destructiveHint: false`, `idempotentHint: true`); `openWorldHint` is true only for tools
that call FIRMS. Every tool declares a title and an output schema (NFR-002, NFR-003).

## Conventions

### Results

Every result is returned twice, as the specification recommends: as `structuredContent`
matching the tool's output schema, and as the same JSON in a text block for clients that
ignore structured content. Fields that do not apply to a result are omitted.

| Field | Meaning |
|---|---|
| `status` | `success`, `no_results` (a valid answer: nothing matched), or `error` |
| `error_code` | Stable code when `status` is `error` (below) |
| `error_message` | What went wrong, in plain words; never contains a MAP_KEY |
| `remediation` | What the agent should do next |
| `retryable`, `retry_after_seconds` | Whether and when retrying can help |

A result with `status: error` is also flagged `isError: true`, so hosts treat it as a tool
execution error while the model still receives the explanation. Arguments are validated
by the tool's own input model, so invalid arguments produce the same structured error
(`invalid_request`) instead of a protocol error. Unknown arguments are rejected.

| `error_code` | Cause | Typical remediation |
|---|---|---|
| `invalid_request` | Arguments invalid (box order, date in the future, unknown source, page size) | Correct the named parameter |
| `invalid_cursor` | Cursor not issued by this tool, or altered | Start a new query without a cursor |
| `cursor_expired` | "Most recent days" moved to a new UTC day between pages | Start a new query or give a date |
| `auth_required` | The tool needs a MAP_KEY and none is connected | Connect a key through the client; never paste it into the chat |
| `invalid_map_key` | FIRMS (or the format check) rejected the key | Check or request a key |
| `map_key_rejected` | FIRMS refused the key: invalid or over its limit | Wait and retry |
| `rate_limited` | The request would exceed the key's transaction budget | Wait `retry_after_seconds`, or narrow the request |
| `upstream_unavailable` | FIRMS did not respond successfully (after retries) | Retry later; FIRMS outage page |
| `upstream_format` | FIRMS returned an unexpected format | Report to the maintainers |
| `internal_error` | Unexpected server failure (details are logged, not returned) | Retry; report if persistent |

### Pagination

`get_fire_detections` pages its records (Earthdata MCP convention): `limit` (default 50,
maximum 500, 0 for summaries only), an opaque `cursor`, and `fields` to trim records.
Cursors are tool-scoped and query-scoped: they carry the original query, so other query
arguments are ignored when a cursor is given; `limit` and `fields` may change between
pages. Later pages are normally served from the response cache, so paging does not spend
FIRMS transactions again. If FIRMS data change between pages the result says so; if the
UTC day changes during a "most recent days" query the cursor expires.

### Knowledge entries in results

Knowledge entries are returned with their full `body` (FIRMS's text, verbatim, Markdown),
`source_url`, `retrieved` date, and `content_sha256`. Results that point to documentation
without including it (caveats, catalog entries) carry `{id, title, source_url}` references
to read with `get_knowledge_entry`.

### Versioning

Each tool has its own SemVer version in its manifest, exposed to clients in the tool's
`_meta` (ADR-0010): major for removed or renamed parameters or output fields, minor for
additions, patch for internal fixes.

## Knowledge tools

### `search_knowledge` (v1.0.0)

Deterministic BM25 search over the knowledge base (FR-KB-005).

| Parameter | Type | Default | Notes |
|---|---|---|---|
| `query` | string, 1–500 characters | required | Plain words or FIRMS terms |
| `limit` | integer 1–10 | 3 | Entries are returned whole |
| `section` | section ID | — | e.g. `caveats`, `viirs`, `modis`, `landsat`, `fire-map` |
| `include_retired` | boolean | false | Also search entries FIRMS no longer publishes |

Output: `query`, `total`, `results` (each a knowledge entry plus `score` and `snippet`),
and a `suggestion` when nothing matched (`status: no_results`).

### `get_knowledge_entry` (v1.0.0)

| Parameter | Type | Default | Notes |
|---|---|---|---|
| `entry_ids` | list of 1–10 IDs | required | From search results, `related`, caveats, or the table of contents |

Output: `entries` (verbatim, with provenance; retired entries carry `status: retired` and a
`notice`, FR-KB-009) and `not_found` with the closest existing IDs (FR-KB-006).

### `list_knowledge_topics` (v1.0.0)

| Parameter | Type | Default | Notes |
|---|---|---|---|
| `section` | section ID | — | List that section's entries |
| `include_entries` | boolean | false | List every entry (about 150 titles) |
| `include_retired` | boolean | false | |

Output: `total_entries`, `sections` (ID, title, `entry_count`, and `entries` when asked),
and the registered `sources` with retrieval dates (FR-KB-007).

## Data tools

### `get_fire_data_sources` (v1.0.0)

| Parameter | Type | Default | Notes |
|---|---|---|---|
| `source_ids` | list of FIRMS source IDs | all | |

Output: `sources` — for each: FIRMS source ID and display name, instrument, platforms,
processing tier and note, nominal pixel size, coverage, whether it is queried by default,
Fire Map layers, KML sensor, record start per the FAQ, and the knowledge entries that
explain it — plus `default_sources` and `notes` (FR-DATA-010).

### `get_data_availability` (v1.0.0)

| Parameter | Type | Default | Notes |
|---|---|---|---|
| `source` | FIRMS source ID or `ALL` | `ALL` | |

With a MAP_KEY it calls FIRMS's documented `data_availability` API (`method: firms_api`);
without one, the public date service the Fire Map uses (`method: fire_map_date_service`),
re-keyed to source IDs (FR-DATA-008). Output: `availability` rows (`source`, `min_date`,
`max_date`, `extra`), the request URL with the key redacted, `retrieved_utc`, `notes`, and
knowledge references about dates and latency.

### `get_fire_detections` (v1.0.0)

Detections from the FIRMS area API for an area and 1–5 UTC days (FR-DATA-001).

| Parameter | Type | Default | Notes |
|---|---|---|---|
| `area` | `{west, south, east, north}` or `"world"` | required | Decimal degrees, longitudes first; west < east, south < north; boxes crossing the antimeridian must be split |
| `day_range` | integer 1–5 | 1 | FIRMS limit |
| `date` | `YYYY-MM-DD` | — | First UTC day; without it, the most recent days (today back to today − (day_range − 1)) |
| `sources` | list of 1–8 source IDs | VIIRS NOAA-20, NOAA-21, S-NPP NRT and MODIS NRT | |
| `min_confidence` | `nominal` or `high` | — | Applied only when given; Landsat `medium` ranks with nominal (FR-DATA-014) |
| `sort` | `newest`, `oldest`, `frp` | `newest` | Ties broken by source and position |
| `limit` | integer 0–500 | 50 | 0 returns summaries only (NFR-004) |
| `cursor` | string | — | `next_cursor` from the previous page, unchanged |
| `fields` | list of record fields | all | `source`, `latitude`, `longitude`, `acquired_utc` always included |

Output (FR-DATA-005, FR-DATA-006):

| Field | Content |
|---|---|
| `query` | The query as interpreted, including `window_utc` (the UTC days covered) |
| `by_source` | Per source: `status`, a `summary` of everything FIRMS returned (detections, first and last time, overpasses, by satellite, day/night, confidence class, processing level, FRP statistics, extent), the `confidence_filter` counts when a filter was applied, the FIRMS `request_url` with `[MAP_KEY]`, `retrieved_utc`, `from_cache`, `estimated_transactions`, the processing note, and an error for a failed source |
| `total_records`, `returned`, `next_cursor`, `records` | The page of detections (pixel centers with typed attributes, UTC times, processing level, and any columns FIRMS adds) |
| `notes` | Independence of observations (never add counts across sources or overpasses), UTC, no interpretation by the server, FIRMS's RT/URT replacement rule when RT/URT records are present, and notes about Landsat coverage, SP lag, filters, failed sources, or changed data |
| `caveats` | References to the FIRMS entries that apply (what a detection means, non-vegetation sources, false detections, missed fires, confidence, UTC, latency, burned area, plus each source's entries; missed-detection guidance when nothing was found) |
| `disclaimer` | The FIRMS Fire Map disclaimer, verbatim, with its source |
| `citation` | FIRMS's answer on crediting and citing FIRMS, verbatim |
| `map_link` | A Fire Map link reproducing the area, UTC dates, and per-satellite layers, with a description |

One failed source does not fail the call: its error is reported in `by_source` and the
rest are returned. Key problems (`auth_required`, `invalid_map_key`, `map_key_rejected`,
`rate_limited`) fail the whole call. Requests are cached and coalesced, and budgeted
against the key's FIRMS limit (FR-DATA-012, FR-DATA-013).

### `get_map_key_status` (v1.0.0)

No parameters: the status is for the MAP_KEY connected to the session. Output: FIRMS's
`transaction_limit`, `current_transactions`, `remaining`, and `transaction_interval`; the
server's own `server_budget` (ceiling and estimated use in the current window); FIRMS's
full response as `firms_response` with any key redacted (FR-DATA-009).

## Link tools

### `build_fire_map_link` (v1.0.0)

| Parameter | Type | Default | Notes |
|---|---|---|---|
| `area` | `{west, south, east, north}` | — | The map fits and outlines it |
| `center` | `{longitude, latitude}` | — | Instead of `area` |
| `zoom` | number | 8 with a center | Global map 1–16; US/Canada map 4–16 |
| `period` | `today`, `24hrs`, `48hrs`, `72hrs`, `7days` | `24hrs` | Or dates |
| `start_date`, `end_date` | `YYYY-MM-DD` | — | UTC days; not in the future |
| `sources` | FIRMS source IDs | — | Per-satellite layers (Advanced mode) |
| `extra_layers` | Fire Map layer IDs | — | e.g. geostationary layers; validated against the catalog |
| `basemap` | `earth`, `firefly`, `street`, `light_gray`, `dark_gray`, `topo_shade`, `topo` | `earth` | |
| `overlays` | layer IDs | `["country-outline"]` | `[]` for none |
| `mode` | `basic`, `advanced`, `burned_area`, `smoke`, `experimental` | automatic | |
| `map` | `global` or `us-canada` | `global` | `/map/` or `/usfs/map/` |

Output: `link` (`url`, `map`, `mode`, `dates`, `layers`, `area` or `center` and `zoom`, and a
plain-language `description`) and `notes` (FR-MAP-001 … FR-MAP-006; grammar in
[Map links](MAP_LINKS.md)).

### `get_fire_footprint_kml_links` (v1.0.0)

| Parameter | Type | Default | Notes |
|---|---|---|---|
| `region` | one of the 12 FIRMS KML regions | required | e.g. `canada`, `europe`, `south_america` |
| `period` | `24h`, `48h`, `72h`, `7d` | `24h` | |
| `sensors` | KML sensors | all offered for the region | `c6.1`, `suomi-npp-viirs-c2`, `noaa-20-viirs-c2`, `noaa-21-viirs-c2`, `landsat` (Canada and USA only) |

Output: `links` (one per sensor, with labels), `notes`, and the knowledge entry holding the
footprint legend (FR-DATA-011).

## Resources

| URI | Type | Content |
|---|---|---|
| `firms://knowledge/index` | `application/json` | Sections, entry IDs and titles, sources |
| `firms://knowledge/{entry_id}` | `text/markdown` | The entry's title as a heading, FIRMS's text verbatim, then a provenance line (source URL, retrieval date, entry ID, hash) |
| `firms://sources` | `application/json` | The source catalog, as `get_fire_data_sources` returns it |

Lists and reads carry a public one-hour cache hint (`ttlMs`, `cacheScope`) for clients on
2026-07-28 that cache; the content changes only with a server release (FR-KB-010).

## Prompts

| Prompt | Arguments | Workflow |
|---|---|---|
| `investigate_fire_activity` | `place`, `days` (1–5), optional `date` | Box for the place, detections, per-source report in UTC, FIRMS caveats, disclaimer, map link, safety redirect |
| `explain_detection` | `detection` | Sensor, time, processing level; FIRMS's explanations of the detection and its attributes; pixel size; caveats; map link |

## Server instructions

The instructions (`src/firms_mcp/instructions.py`) define the workflow
**Orient → Retrieve → Contextualize → Link** and the rules for safety (FIRMS's
disclaimer, official emergency information first), coordinates (longitude first), time
(UTC), reading detections (no summing across sources, absence of detections is not
absence of fire), credentials (never in the conversation), context management, and
errors (FR-MCP-002). Clients receive them in the `initialize` result (handshake era) or
the `server/discover` result (2026-07-28).
