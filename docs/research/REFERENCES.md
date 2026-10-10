# References and Research Notes

Every external fact the project relies on is listed here with where it came from and when
it was retrieved. When a fact is re-verified, add the new date; when it changes, record
the change in the [running list](../project/RUNNING_LIST.md) and the affected ADR.

## 1. Readiness framework

| Source | Location | Retrieved | Notes |
|---|---|---|---|
| NASA Applied Sciences Program, *The Application Readiness Level Metric* (11 slides) | <https://carbon.nasa.gov/docs/The%20ARL%20Metric.pdf> | 2026-10-09 | Transcribed in [ARL reference](../arl/ARL_METRIC_REFERENCE.md) |

## 2. NASA Earthdata MCP

**Repository:** <https://github.com/nasa/earthdata-mcp> — studied at commit `b071caf`
(2026-10-08, "CMRNLP-153: Add control transformation job tool and update docs"), 152
commits of history. Public endpoint `https://cmr.earthdata.nasa.gov/mcp/v1`
(Streamable HTTP). Registry name `io.github.nasa/earthdata-mcp`, version 1.1.0.

### 2.1 What the Earthdata MCP does, and what this project adopts

| Earthdata MCP practice | Observed in | Adopted here? | How |
|---|---|---|---|
| Python, FastMCP (`fastmcp>=4`), `uv`, Pydantic | `pyproject.toml` | **Yes** | Same stack ([ADR-0002](../decisions/0002-follow-nasa-earthdata-mcp-conventions.md)) |
| One directory per tool: `manifest.json` (name, version, description, tags, annotations, `require_auth`, `enabled`, examples) + `tool.py` + `output_model.py` | `tools/*/`, `loader.py` | **Yes** | Same structure inside the `firms_mcp` package; loader validates manifests |
| Tools named `get_*`; descriptions written for the LLM in the manifest | `tools/*/manifest.json` | **Yes** | Plus verb-led names where `get_` would mislead (`search_knowledge`, `build_fire_map_link`) |
| Pydantic input models with `extra="forbid"`; structured error outputs with a `status` field | `models/tools/*.py` | **Yes** | Same pattern |
| Server instructions enforcing a workflow (*Discover → Verify → Access*), honesty about limitations, context-window management, error handling, an example trace | `prompts/instructions.py` | **Yes** | FIRMS workflow: *Orient → Retrieve → Contextualize → Link* |
| Anonymous discovery; authentication only for tools that need it (per-tool step-up, HTTP 401 challenge before the MCP layer) | `util/stepup.py`, `server.py` | **Yes** | Knowledge and link tools anonymous; data tools require a MAP_KEY |
| OAuth via `OAuthProxy` to Earthdata Login | `server.py` | **Adapted** | FIRMS keys are not issued by Earthdata Login, so the server acts as its own authorization server whose consent step collects the user's MAP_KEY ([ADR-0004](../decisions/0004-authentication-bring-your-own-map-key.md)) |
| Pagination: `limit` (default 10, max 50), opaque query-scoped `cursor`, `fields` filtering | `models/pagination.py`, `util/pagination.py` | **Yes** | For detection records |
| Referral parameters on outbound links (`utm_source=earthdata-mcp&utm_medium=mcp`) | commit `16064f2`, instructions | **Yes** | `utm_source=firms-mcp&utm_medium=mcp` on FIRMS links (configurable) |
| Health endpoint; `/.well-known/ard.json` discovery document with representative queries | `server.py`, `ard.json` | **Yes** | Same |
| `server.json` for the MCP Registry, published via GitHub OIDC workflow | `server.json`, `.github/workflows/publish-mcp.yml` | **Yes** (when a public repository exists) | |
| Decoupled versioning: server SemVer in `pyproject.toml`; per-tool SemVer in `manifest.json` | `docs/developers/versioning.md` | **Yes** | Same rules |
| Docs split into `consumers/` and `developers/`; user guide with per-client connection steps | `docs/` | **Yes** | Extended with science, design, ARL, and project docs |
| Tests: pytest, all real HTTP blocked by an autouse fixture, mocked upstream responses; separate manual live integration script not run in CI | `tests/conftest.py`, `scripts/integration_test.py` | **Yes** | `respx` blocks network; live tests opt-in via a marker |
| PR template with checklist (tests, docs, version bumps) | `.github/pull_request_template.md` | **Yes** | |
| Langfuse tracing, CloudWatch logging, AWS ECS/Terraform, Bamboo | `util/langfuse.py`, `terraform/` | **No** | Infrastructure-specific; this project logs structured JSON and supports OpenTelemetry context per the MCP spec |
| Embedding/ingestion pipeline (being deprecated upstream) | README note | **No** | Lexical search is sufficient for a curated knowledge base of this size |

## 3. Model Context Protocol

| Source | Location | Retrieved |
|---|---|---|
| Specification, revision 2026-07-28 | <https://modelcontextprotocol.io/specification/2026-07-28> | 2026-10-09 |
| Changelog 2025-11-25 → 2026-07-28 | <https://modelcontextprotocol.io/specification/2026-07-28/changelog> | 2026-10-09 |
| Authorization | <https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization> | 2026-10-09 |
| MCP Apps extension overview (`io.modelcontextprotocol/ui`; apps spec 2026-01-26) | <https://modelcontextprotocol.io/extensions/apps/overview> | 2026-10-09 |
| MCP Python SDK `mcp` 2.3.0 (2026-10-02; 2.0.0 released 2026-07-28) | <https://pypi.org/project/mcp/> | 2026-10-09 |
| FastMCP 4.1.0 (2026-10-08) | <https://gofastmcp.com>, <https://pypi.org/project/fastmcp/> | 2026-10-09 |

Key changes relevant to this project (from the changelog): stateless requests (no
`initialize`, no `Mcp-Session-Id`); `server/discover`; Multi Round-Trip Requests
(`InputRequiredResult`) replace server-initiated elicitation/sampling; `resultType` on all
results; `ttlMs`/`cacheScope` on list and read results; `Mcp-Method`/`Mcp-Name` request
headers; Tasks moved to an extension; Roots, Sampling, Logging deprecated; Dynamic Client
Registration deprecated in favour of Client ID Metadata Documents; RFC 9207 `iss` in
authorization responses.

### OAuth and related standards

OAuth 2.1 (draft-ietf-oauth-v2-1-13); RFC 6750 (Bearer tokens); RFC 7591 (Dynamic Client
Registration); RFC 8414 (Authorization Server Metadata); RFC 8707 (Resource Indicators);
RFC 9207 (Issuer Identification); RFC 9728 (Protected Resource Metadata);
draft-ietf-oauth-client-id-metadata-document-00 (CIMD).

## 4. FIRMS services

| Service | Location | Auth | Retrieved | Observations |
|---|---|---|---|---|
| API index (v4.1.16) | <https://firms.modaps.eosdis.nasa.gov/api/> | — | 2026-10-09 | `area`, `data_availability`, `kml_fire_footprints`, `map_key`, `missing_data` available; `countries` and `country` "not currently available" |
| Area API | `/api/area/csv/[MAP_KEY]/[SOURCE]/[AREA_COORDINATES]/[DAY_RANGE]` and `…/[DATE]` | MAP_KEY | 2026-10-09 | Bounding box `west,south,east,north` or `world`; `DAY_RANGE` 1–5; `DATE` `YYYY-MM-DD`; sources `LANDSAT_NRT` (US/Canada only), `MODIS_NRT`, `MODIS_SP`, `VIIRS_NOAA20_NRT`, `VIIRS_NOAA20_SP`, `VIIRS_NOAA21_NRT`, `VIIRS_SNPP_NRT`, `VIIRS_SNPP_SP`. "RT and URT data are removed when corresponding NRT detections are processed or RT/URT is older than 6 hours." |
| Data availability | `/api/data_availability/csv/[MAP_KEY]/[SENSOR]` | MAP_KEY | 2026-10-09 | Sensors: `ALL` plus the eight sources above |
| MAP_KEY | <https://firms.modaps.eosdis.nasa.gov/api/map_key/> | — | 2026-10-09 | Free, requested with an email address; 5,000 transactions per 10-minute interval; larger requests may count as several transactions |
| MAP_KEY status | `/mapserver/mapkey_status/?MAP_KEY=…` | MAP_KEY | 2026-10-09 | Invalid key → HTTP 403 with a plain-text message |
| KML fire footprints | `/api/kml_fire_footprints/?region=…&date_span=…&sensor=…` | none | 2026-10-09 | 12 regions; `24h`/`48h`/`72h`/`7d`; sensors `c6.1`, `suomi-npp-viirs-c2`, `noaa-20-viirs-c2`, `noaa-21-viirs-c2`, `landsat` (Canada and contiguous US + Hawaii only) |
| Missing data | <https://firms.modaps.eosdis.nasa.gov/api/missing_data/> | — | 2026-10-09 | Web table of days with missing data (standard and NRT) |
| Map date service (undocumented, used by the Fire Map) | <https://firms.modaps.eosdis.nasa.gov/api/map_dates/> | none | 2026-10-09 | JSON of `[min, max]` dates per product, e.g. `modis_nrt`, `modis_v6`, `jpss1_viirs_c2_nrt`, `jpss2_viirs_c2_nrt`, `suomi_viirs_c2_nrt`, `suomi_viirs_c2_sp`, `landsat_nrt`, `goesr_abi_c1_nrt`, `ba_monthly`, `ba_monthly_viirs` |
| Area API error responses | — | — | 2026-10-09 | Invalid key: `/api/area/` → HTTP 400 "Invalid MAP_KEY."; `/api/data_availability/` → HTTP 401 "Invalid MAP_KEY." |
| Area API page script (`computeWeight`, `checkTransaction`) | <https://firms.modaps.eosdis.nasa.gov/api/area/> | — | 2026-10-09 | Displayed transaction weight `ceil(ceil(Δlon/60)·ceil(Δlat/60)·(2 VIIRS / 0.5 other)·DAY_RANGE)`; MAP_KEY validated as 32 alphanumerics; status at `/mapserver/mapkey_status/?MAP_KEY=…` |

## 5. FIRMS Fire Map

| Item | Location | Retrieved | Notes |
|---|---|---|---|
| Fire Map | <https://firms.modaps.eosdis.nasa.gov/map/> | 2026-10-09 | Map configuration version 2.0.0; EPSG:4326 |
| Map application bundle | `/dist/firms_map.927094f8.js` | 2026-10-09 | Source of the hash grammar (class handling `t:`, `m:`, `d:`, `l:`, `v:`, `i:`, `tool:`, `@lon,lat,zoomz`) |
| Layer catalog | Runtime configuration of the map (267 layers) | 2026-10-09 | Snapshot stored with the link builder |
| Map disclaimer dialog ("ACTIVE FIRES / THERMAL ANOMALIES") | Shown on first load of the map | 2026-10-09 | Stored verbatim as a knowledge supplement |
| US/Canada Fire Map | <https://firms.modaps.eosdis.nasa.gov/usfs/map/> | 2026-10-09 | Reached from the global map's US/CANADA mode, which copies the hash |

Browser verification performed 2026-10-09 (cold page loads):

- `#d:24hrs;@-118.5,34.1,7.0z` → defaults: `earth` basemap, `fires_all`, `country-outline`.
- `#m:advanced;d:24hrs;l:fires_viirs_noaa20,fires_viirs_snpp,fires_modis_aqua,earth;@-118.5,34.1,7.0z`
  → exactly those layers visible.
- Same layers **without** `m:advanced` → per-sensor layers dropped (basic mode only knows
  `fires_all`).
- `#m:advanced;d:2025-01-07..2025-01-09;l:fires_viirs_noaa20,fires_viirs_snpp,street;i:-119.2,33.8,-117.6,34.6`
  → date range applied; view fit to the box; box drawn.
- `?utm_source=firms-mcp&utm_medium=mcp` before the hash does not affect loading.

## 6. FIRMS documentation

| Source | Location | Retrieved |
|---|---|---|
| FIRMS FAQ | <https://www.earthdata.nasa.gov/data/tools/firms/faq> | 2026-10-09 (also provided verbatim by the owner) |
| Attribute fields for NRT MODIS and VIIRS active fire data | <https://www.earthdata.nasa.gov/data/tools/firms/active-fire-data-attributes-modis-viirs> | 2026-10-09 |
| VIIRS Collection 2 375 m Active Fire Product User's Guide v1.2 (Schroeder, Giglio, Hall; June 2025) | <https://www.earthdata.nasa.gov/s3fs-public/2025-06/VIIRS_C2_AF-375m_User_Guide_1.2.pdf> | 2026-10-09 — consulted for confidence classes (7/8/9 = low/nominal/high) and HHMM UTC acquisition times |
| MODIS Collection 6 and 6.1 Active Fire Product User's Guide v1.0 (Giglio, Schroeder, Hall, Justice; May 2021) | <https://www.earthdata.nasa.gov/s3fs-public/2023-09/MODIS_C6_C6.1_Fire_User_Guide_1.0.pdf> | 2026-10-09 — consulted for confidence-class thresholds (§8.4.3, Table 11) |
| LANCE (disclaimer and FIRMS citation) | <https://www.earthdata.nasa.gov/data/projects/lance#ed-firms-citation> | link recorded 2026-10-09 |

## 7. Scientific literature cited by the FIRMS FAQ

These are the primary sources behind the caveats the server surfaces. They are cited, not
reproduced.

- Giglio, L., Descloitres, J., Justice, C. O., & Kaufman, Y. (2003). An enhanced contextual fire detection algorithm for MODIS. *Remote Sensing of Environment*, 87, 273–282. doi:10.1016/S0034-4257(03)00184-6
- Schroeder, W., Oliva, P., Giglio, L., & Csiszar, I. A. (2014). The New VIIRS 375m active fire detection data product: algorithm description and initial assessment. *Remote Sensing of Environment*, 143, 85–96. doi:10.1016/j.rse.2013.12.008
- Schroeder, W., Oliva, P., Giglio, L., Quayle, B., Lorenz, E., & Morelli, F. (2016). Active fire detection using Landsat-8/OLI data. *Remote Sensing of Environment*, 185, 210–220. doi:10.1016/j.rse.2015.08.032
- Giglio, L., Csiszar, I., Restás, Á., Morisette, J. T., Schroeder, W., Morton, D., & Justice, C. O. (2008). Active fire detection and characterization with ASTER. *Remote Sensing of Environment*, 112(6), 3055–3063. doi:10.1016/j.rse.2008.03.003
- Hall, J. V., Zhang, R., Schroeder, W., Huang, C., & Giglio, L. (2019). Validation of GOES-16 ABI and MSG SEVIRI active fire products. *International Journal of Applied Earth Observation and Geoinformation*, 83, 101928. doi:10.1016/j.jag.2019.101928
- Wooster, M. J., et al. (2015). LSA SAF Meteosat FRP products – Part 1. *Atmospheric Chemistry and Physics*, 15(22), 13217–13239. doi:10.5194/acp-15-13217-2015
- Roberts, G., et al. (2015). LSA SAF Meteosat FRP products – Part 2. *Atmospheric Chemistry and Physics*, 15(22), 13241–13267. doi:10.5194/acp-15-13241-2015
- Xu, W., Wooster, M. J., Kaneko, T., He, J., Zhang, T., & Fisher, D. (2017). Himawari-8 AHI FRP retrieval. *Remote Sensing of Environment*, 193, 138–149. doi:10.1016/j.rse.2017.02.024
- Xu, W., Wooster, M. J., He, J., & Zhang, T. (2021). GOES-16 ABI with the geostationary FTA algorithm. *Science of Remote Sensing*, 3, 100016. doi:10.1016/j.srs.2021.100016
- Xu, W., et al. (2026). Meteosat Third Generation FCI early fire detection and small-fire FRP retrieval. *Science of Remote Sensing*, 13, 100366. doi:10.1016/j.srs.2026.100366
- Schmidt, C., Hoffman, J., Prins, E., & Lindstrom, S. (2013). GOES-R ABI ATBD for Fire/Hot Spot Characterization v2.6. NOAA NESDIS STAR.
- Chen, Y., et al. (2022). California wildfire spread derived using VIIRS satellite observations and an object-based tracking system. *Scientific Data*, 9, 249. doi:10.1038/s41597-022-01343-0
- Csiszar, I., et al. (2006; 2014), Morisette, J. T., et al. (2005), Justice, C. O., et al. (2002), Giglio, L., et al. (2006) — MODIS/VIIRS validation and burned-area relationships, as listed in the FIRMS publications page.
