# Running List — information to look up and work to do

This is the project's living to-do list. It is updated in the same commit as the work it
describes. Items move from **Open** to **Done** (with the commit or evidence that closed
them); nothing is deleted. Each item has a stable ID so that commits, ADRs, and the
[work summary](WORK_SUMMARY.md) can reference it.

Legend: 🔎 needs research · 🛠 implementation · 📝 documentation · ❓ needs owner decision ·
🔑 needs a real FIRMS MAP_KEY · 🤝 needs an external party

## Open — information to look up

| ID | Item | Why it matters | Blocked by | Status |
|---|---|---|---|---|
| LU-01 | 🔑 Response format of the MAP_KEY status service (`/mapserver/mapkey_status/?MAP_KEY=…`) for a valid key | `get_map_key_status` output schema; consent-page validation | Valid MAP_KEY | Open. Invalid key → HTTP 403, plain text "MAP_KEY is invalid or your have exceeded your transaction/time limit. Please try again later." (observed 2026-10-09) |
| LU-02 | 🔑 How many transactions a multi-day or `world` area request consumes | Rate-limit budgeting, caching policy | Valid MAP_KEY | Partly answered 2026-10-09: the FIRMS area-API page computes the "Mapkey transaction amount" it displays as `ceil(ceil((east−west)/60) × ceil((north−south)/60) × (2 if VIIRS else 0.5) × DAY_RANGE)`. Confirm against the status service with a live key |
| LU-03 | 🔑 Exact CSV headers for every area-API source (VIIRS ×3, MODIS, Landsat, SP variants) | Parser and output schema | Valid MAP_KEY | Open. Expected columns taken from the FIRMS attribute page; confirm live |
| LU-04 | 🔎 When will the `country` / `countries` API endpoints return? | Country queries currently require bounding boxes | FIRMS outage page | Open. Marked "not currently available" on the API page (2026-10-09) |
| LU-05 | 🤝 Confirm the FIRMS Fire Map hash grammar is stable / acceptable to link to | Deep links depend on it | FIRMS team | Open. Grammar derived from the map's own parser and verified in a browser |
| LU-06 | 🤝 FIRMS policy on third-party services using users' MAP_KEYs, and on an operator-wide key | Auth design, terms compliance | Earthdata Support (earthdata-support@nasa.gov, subject "FIRMS") | Open |
| LU-07 | 🔎 Are geostationary (GOES / Meteosat / Himawari) detections available through the area API? | Source catalog completeness | — | Open. Not listed among area-API sources on 2026-10-09; present as map layers |
| LU-09 | 🔎 Which MCP hosts support MCP Apps, CIMD, and mid-session step-up (401 after anonymous use) | Client compatibility matrix | — | Open. Protocol side verified 2026-10-10 with the FastMCP 4.1 client: 2026-07-28 and handshake-era (2025-11-25, 2025-06-18) clients over stdio and Streamable HTTP. Real hosts still to check (WP8, WP11) |
| LU-10 | 🔎 Standard-processing (SP) lag per sensor | Explaining availability to users | — | Open. Map date service (2026-10-09): MODIS SP to 2026-07-31; VIIRS S-NPP SP and NOAA-20 SP to 2026-06-30 |
| LU-11 | 🔎 Review FIRMS API code examples at `/academy/` | Usage patterns, undocumented parameters | — | Open. Note: the area page's own script also generates `/api/area/html/…` URLs (an HTML output type besides `csv`) |
| LU-13 | 🔎 Cross-check knowledge base against the VIIRS C2 375 m user guide (June 2025) and MODIS C6/6.1 user guide | Supplement content; caveat accuracy | — | In progress: both guides downloaded; confidence semantics verified (MODIS Table 11 thresholds; VIIRS classes 7/8/9) and used by the parser |
| LU-14 | 🤝 Whether FIRMS wants a specific referral parameter on links (currently `utm_source=firms-mcp&utm_medium=mcp`, mirroring Earthdata MCP) | Referral analytics for FIRMS | FIRMS team | Open. Verified that the map loads correctly with these parameters |
| LU-15 | 🔎 FIRMS WMS/WFS services (MAP_KEY-based) for possible image or vector outputs | Future visualization options | — | Open |

## Open — work to do

| ID | Item | Work package | Status |
|---|---|---|---|
| WK-01 | 📝 Baseline research documents: data products, references | WP1 | In progress |
| WK-02 | 📝 Decision-making characterization and evaluation plan | WP2 | Open |
| WK-03 | 🛠 Knowledge base: verbatim FAQ ingestion, supplements, loader, search, refresh script, completeness test | WP3 | Done on `feature/knowledge-base` (see Done) |
| WK-04 | 🛠 FIRMS API client, source catalog, CSV normalizer, caching, rate-limit guard | WP4 | Done on `feature/firms-api-client` (see Done) |
| WK-05 | 🛠 Map link builder and layer catalog snapshot with refresh/verification script | WP5 | Done on `feature/map-links` (see Done) |
| WK-06 | 📝 Viability case | WP6 | Done (see Done) |
| WK-07 | 🛠 MCP server: tools, resources, prompts, instructions, health, `server.json`, `ard.json` | WP7 | Done on `feature/mcp-server` (snapshot queued for signing; see Done) |
| WK-08 | 🛠 Auth: env var, OAuth 2.1 MAP_KEY connect flow (CIMD + DCR), encrypted tokens, step-up | WP8 | Done on `feature/oauth-map-key` (snapshot queued for signing; see Done) |
| WK-09 | 📝 Operations & governance; integration issues log | WP9 | Done (snapshot queued for signing; see Done) |
| WK-10 | 🛠 Container image, GitHub Actions CI, MCP Registry metadata | WP10 | Done on `feature/packaging-ci` (snapshot queued for signing; see Done) |
| WK-11 | 🛠 Evaluation harness and live validation | WP11 | Open |
| WK-12 | 🛠 MCP Apps in-client map with time animation | WP12 | Open |
| WK-13 | 📝 Consumer user guide for Claude.ai, ChatGPT, Claude Code, Cursor, VS Code | WP7/WP8 | Open |
| WK-14 | 🛠 Bring WP3–WP5 modules in line with `ruff` 0.17 (4 files to reformat, 9 lint findings) and anchor the `knowledge` lint exclusion, which also hides `src/firms_mcp/knowledge` (integration issue II-08) | WP10 | Done (II-08 resolved) |
| WK-15 | 🛠 Per-tool step-up must parse the JSON-RPC body for handshake-era requests, which carry no `Mcp-Name` header (integration issue II-06) | WP8 | Done (II-06 resolved) |

## Decisions needed from the owner

| ID | Decision | Current default | Status |
|---|---|---|---|
| OD-01 | ❓ License | Apache-2.0 (provisional) | Open |
| OD-02 | ❓ Hosting target for the public remote endpoint | Container image, host-agnostic; options documented | Open |
| OD-03 | ❓ Create a public GitHub repository, and its name | Public repository `github.com/mendesdyl/firms-mcp`. `server.json` uses the registry name `io.github.mendesdyl/firms-mcp`; the registry requires the name's namespace to match the publishing account | Decided 2026-10-12: the owner created the public repository `mendesdyl/firms-mcp`, and `main` was pushed to it |
| OD-04 | ❓ Allow an operator-wide MAP_KEY for anonymous users on a public deployment | Disabled by default | Open |
| OD-05 | 🔑 Provide a FIRMS MAP_KEY locally (in `.env`, never in chat) to run live validation | Live tests skip without it | Open |

## Pending signed commits

Commits are signed through the owner's 1Password SSH key. While the owner is away, each
finished feature is snapshotted as a git tree (`git write-tree`, pinned at
`refs/snapshots/<NN>-<wp>`) with its commit and merge messages, and replayed as signed
commits and `--no-ff` merges when the owner is back to approve (owner decision,
2026-10-10).

| Order | Branch | Snapshot ref | Status |
|---|---|---|---|
| 01 | `feature/firms-api-client` (WP4) | `refs/snapshots/01-wp4` | Done 2026-10-10: signed `c227ee3`, merged `951aa26` |
| 02 | `feature/map-links` (WP5) | `refs/snapshots/02-wp5` | Done 2026-10-10: signed `bf810b1`, merged `b4bf2b6`; `main` tree equals the snapshot tree |
| 03 | `feature/mcp-server` (WP7) | `refs/snapshots/03-wp7` | Done 2026-10-12: signed `569ca42`, merged `5a502fb` |
| 04 | `feature/oauth-map-key` (WP8) | `refs/snapshots/04-wp8` | Done 2026-10-12: signed `e5f3223`, merged `109c1ae` |
| 05 | `main` (WP9, documentation) | `refs/snapshots/05-wp9` | Done 2026-10-12: signed `0f42412` |
| 06 | `feature/packaging-ci` (WP10) | `refs/snapshots/06-wp10` | Done 2026-10-12: signed `f1f5c9f`, merged `d126779`; `main` tree equals the snapshot tree |

The owner stepped away on 2026-10-10 and asked for later work to be batched; entries from
03 on follow the snapshot procedure above. The queue is empty as of 2026-10-12.

## Done

| ID | Item | Closed by |
|---|---|---|
| LU-00a | Read the ARL metric document in full | Transcribed in [ARL reference](../arl/ARL_METRIC_REFERENCE.md) |
| LU-00b | Study NASA Earthdata MCP (`nasa/earthdata-mcp` @ `b071caf`) | [References § Earthdata MCP](../research/REFERENCES.md#nasa-earthdata-mcp) |
| LU-00c | Identify the current MCP specification and SDK versions | MCP 2026-07-28; `mcp` 2.3.0; `fastmcp` 4.1.0 — [ADR-0003](../decisions/0003-target-mcp-2026-07-28-with-backward-compatibility.md) |
| LU-00d | Determine the FIRMS Fire Map URL grammar | Derived from the map's parser (bundle `firms_map.927094f8.js`) and verified in a browser — [ADR-0006](../decisions/0006-firms-fire-map-deep-links.md) |
| LU-00e | Current FIRMS API endpoints, sources, and limits | API v4.1.16; `DAY_RANGE` 1–5; 5,000 transactions / 10 min — [Data products](../science/DATA_PRODUCTS.md) |
| LU-12 | Full text of the LANCE disclaimer | Imported verbatim as `supplement.disclaimers.lance-disclaimer` (and acknowledgments) |
| LU-16 | MAP_KEY format | FIRMS pages validate a MAP_KEY as 32 alphanumeric characters (`/api/map_key/` checks `^[0-9a-z]+$`, the area page checks case-insensitively) and check status at `/mapserver/mapkey_status/?MAP_KEY=…` |
| WK-03 | Knowledge base (WP3) | 150 entries (142 FAQ + 8 supplements); completeness 0 missing lines; 52 tests — merge of `feature/knowledge-base` |
| LU-08 | US/Canada map hash compatibility | Verified 2026-10-10: `/usfs/map/` honours the same grammar and layer IDs (270 layers; minimum zoom 4) |
| WK-05 | Fire Map link builder (WP5) | `firms_mcp.maplinks` + catalog snapshot + `scripts/check_map_catalog.py`; generated links verified in the real map; 149 tests |
| WK-04 | FIRMS API client (WP4) | `firms_mcp.firms`: catalog, client, parser, summaries, cache, budget, KML links, redaction; 125 tests — merge of `feature/firms-api-client` |
| WK-06 | Viability case (WP6) | [Viability case](../plan/VIABILITY_CASE.md); ARL3-M3 recorded in L-3, owner review pending |
| WK-07 | MCP server (WP7) | `firms_mcp.server` + nine manifest-defined tools, resources, prompts, instructions, `/health`, `/.well-known/ard.json`, `server.json`; [tool catalog](../design/TOOLS.md), [architecture](../design/ARCHITECTURE.md), [integration issues](INTEGRATION_ISSUES.md); 217 tests — `feature/mcp-server` |
| WK-08 | Authentication (WP8) | `firms_mcp.auth`: MAP_KEY connect flow (CIMD + DCR, PKCE, `iss`, JWE tokens, refresh rotation with replay detection, revocation), step-up middleware, `firms-mcp keygen`; [Authentication](../design/AUTHENTICATION.md); 251 tests — `feature/oauth-map-key` |
| WK-09 | Operations and governance (WP9) | [Operations and governance](OPERATIONS_AND_GOVERNANCE.md) (ARL4-M2, owner review pending); [integration issues log](INTEGRATION_ISSUES.md) started in WP7 |
| WK-10 | Packaging and CI (WP10) | `Dockerfile`, `.github/workflows/` (CI on Python 3.12–3.14, release to PyPI, MCP Registry publication), PR template, Dependabot, `mcp-name` marker; [Testing](../developers/TESTING.md), [Versioning and releasing](../developers/RELEASING.md); 252 tests pass on CPython 3.12.15, 3.13.16, 3.14.6 — `feature/packaging-ci` |
| WK-14 | Lint and format clean across the repository (II-08) | `feature/packaging-ci` |
| WK-16 | Build and run the container image | 2026-10-12, Docker 29.8.2, built from `refs/snapshots/06-wp10`: image builds; runs as user `firms`; `/health` reports 9 tools and 150 knowledge entries; `/.well-known/ard.json` and the protected-resource metadata are served; an MCP client over Streamable HTTP lists the nine tools and calls `search_knowledge` and `build_fire_map_link` successfully |
