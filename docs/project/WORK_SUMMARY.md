# Work Summary

A task-by-task account of the work done, what it produced, and which ARL milestones and
requirements it supports. It is updated with every merge to `main`
([ADR-0010](../decisions/0010-branching-commits-and-versioning.md)). For open items see the
[running list](RUNNING_LIST.md); for readiness status see the
[ARL assessment log](../arl/ARL_ASSESSMENT_LOG.md).

## Task index

| # | Task (from the owner's request) | Where it is accomplished | Status |
|---|---|---|---|
| T1 | Build an MCP layer on top of the existing FIRMS API | WP4 ([FIRMS API client](../design/FIRMS_API_CLIENT.md)), WP7 — `src/firms_mcp/` | In progress (client done) |
| T2 | Keep the FIRMS auth model (MAP_KEY) but make connecting easy from a public chatbot | [ADR-0004](../decisions/0004-authentication-bring-your-own-map-key.md), WP8 | Designed |
| T3 | Use the most current MCP standard and enterprise practice | [ADR-0003](../decisions/0003-target-mcp-2026-07-28-with-backward-compatibility.md) | Designed |
| T4 | Plan the orchestration of the project | [Project plan](../plan/PROJECT_PLAN.md) | Done (v1.0) |
| T5 | Follow the NASA ARL metric 100 % and document it | [ARL reference](../arl/ARL_METRIC_REFERENCE.md), [ARL log](../arl/ARL_ASSESSMENT_LOG.md), plan §8 | Ongoing |
| T6 | Traditional README linking to project info and to scientific and design documentation | [README](../../README.md) | Ongoing |
| T7 | Git repository from the start; incremental commits; branches for bigger changes | [ADR-0010](../decisions/0010-branching-commits-and-versioning.md) | Ongoing |
| T8 | Running list of information to look up and work on | [Running list](RUNNING_LIST.md) | Ongoing |
| T9 | Summary of work per task | This document | Ongoing |
| T10 | Tests checking every functionality from the design | [ADR-0008](../decisions/0008-testing-and-verification-strategy.md), [Traceability](TRACEABILITY.md) | Designed |
| T11 | Documentation for the owner, the agent, and others | [Docs index](../README.md) | Ongoing |
| T12 | Follow the Earthdata MCP design | [ADR-0002](../decisions/0002-follow-nasa-earthdata-mcp-conventions.md), [References §2](../research/REFERENCES.md#nasa-earthdata-mcp) | Designed |
| T13 | Include all FIRMS FAQs, not boiled down, with a mechanism to add more | [ADR-0005](../decisions/0005-knowledge-base-verbatim-and-extensible.md), [knowledge/](../../knowledge/README.md), [Adding knowledge](../developers/ADDING_KNOWLEDGE.md) | Done (verified: 0 missing lines) |
| T14 | Provide information to the answering agent rather than answer science questions | Plan §4 guiding principle; ADR-0007 | Designed |
| T15 | Link to the FIRMS Fire Map with self-building URLs | [ADR-0006](../decisions/0006-firms-fire-map-deep-links.md), [Map links design](../design/MAP_LINKS.md), `src/firms_mcp/maplinks/` | Done (links verified in the real map) |
| T16 | Later: map in the client, with animation | [ADR-0009](../decisions/0009-interactive-map-via-mcp-apps.md), WP12 | Proposed |

## Log

### 2026-10-09 — WP0/WP1: research, plan, and decision records (`main`)

**What was done**

- Read the NASA ARL metric in full and transcribed its levels and milestones.
- Studied NASA's Earthdata MCP repository (`b071caf`) and recorded which practices are
  adopted, adapted, or not adopted.
- Established the current MCP revision (2026-07-28) and SDK versions (`mcp` 2.3.0,
  `fastmcp` 4.1.0).
- Surveyed the FIRMS API (v4.1.16): endpoints, sources, `DAY_RANGE` 1–5, the 5,000
  transactions / 10 min limit, error responses for invalid keys, the public map date
  service, and KML footprint downloads.
- Derived the FIRMS Fire Map URL grammar from the map application's own parser and
  verified it with cold page loads, including per-satellite layers (which require
  `m:advanced`), historical date ranges, area-of-interest boxes, and referral parameters.
- Captured the Fire Map disclaimer text and the layer catalog (267 layers).
- Wrote the project plan, ARL reference and assessment log, ten ADRs, the data-products
  baseline, references, and this summary.

**Outputs:** `docs/plan/`, `docs/arl/`, `docs/decisions/`, `docs/science/DATA_PRODUCTS.md`,
`docs/research/REFERENCES.md`, `docs/project/`.

**ARL milestones supported:** ARL1-M1, ARL1-M2.

### 2026-10-09 — WP2: decision-making characterization and traceability (`main`)

**What was done:** characterized the decision-making activity (agent- and person-level),
six personas, four pre-application mechanisms, and eleven baseline failure modes mapped to
FIRMS guidance and to features; wrote the evaluation plan; created 61 machine-readable
requirements, a network guard for tests, and a traceability meta-test and generator.

**Outputs:** [Decision context](../science/DECISION_CONTEXT.md),
[Evaluation plan](../design/EVALUATION.md), [requirements.yaml](requirements.yaml),
[TRACEABILITY.md](TRACEABILITY.md), `tests/conftest.py`, `tests/test_traceability.py`.

**ARL milestones supported:** ARL2-M2, ARL2-M3, ARL3-M2.

### 2026-10-09 — WP3: knowledge base (`feature/knowledge-base`)

**What was done**

- Built `firms_mcp.knowledge`: entry and source models with content hashing, front-matter
  I/O, a strict loader that reports every problem at once, deterministic BM25 search with
  a small synonym table, and maintenance commands (`validate`, `rehash`, `sync`,
  `import-page`).
- Wrote an HTML→Markdown converter that changes form but never wording (links made
  absolute, tables, lists, figures with captions, footnote markers) and used it to
  generate **142 FAQ entries** (137 questions in 15 sections, the preamble, 4 section
  introductions) from the live FAQ page.
- Saved the owner-provided FAQ text verbatim as the reference snapshot and verified the
  knowledge base against it line by line: **0 missing lines**. The one discrepancy found
  along the way was two invisible zero-width spaces in the live HTML; they are now
  removed during conversion and documented.
- Imported 8 supplements verbatim with provenance: the Fire Map disclaimer dialog, the
  LANCE disclaimer and acknowledgments, the MODIS/VIIRS attribute definitions, and the
  FIRMS API pages for `area`, `data_availability`, `map_key`, and `kml_fire_footprints`.
- Found in FIRMS's own page scripts: the MAP_KEY format (32 alphanumerics), the status
  URL, and the transaction-weight formula FIRMS displays (running list LU-02, LU-16).
- Packaged the knowledge base into the wheel.

**Outputs:** `src/firms_mcp/knowledge/`, `knowledge/`, `tests/unit/knowledge/`,
`tests/contract/test_faq_completeness.py`, [Knowledge base design](../design/KNOWLEDGE_BASE.md),
[Adding knowledge](../developers/ADDING_KNOWLEDGE.md).

**Requirements implemented:** FR-KB-001 … FR-KB-009 (FR-KB-010, resources, comes with the
server). **Tests:** 52 passing.

**ARL milestones supported:** ARL2-M1 and ARL3-M1 (knowledge-base component).

### 2026-10-09 — WP4: FIRMS API client (`feature/firms-api-client`)

**What was done**

- `firms_mcp.firms`: the eight-source catalog (with Fire Map layers, map-date keys, KML
  sensors, and the knowledge entries that explain each source); validated bounding boxes;
  an async client for `area`, `data_availability`, MAP_KEY status, and the public map date
  service; a CSV parser for every sensor family with UTC timestamps, documented confidence
  classes, processing level (URT/RT/NRT/SP), and preservation of unknown columns;
  per-source summaries; a TTL/LRU cache with single-flight coalescing; a transaction budget
  using FIRMS's own displayed weight formula; KML footprint links; stable error codes with
  remediation text.
- Verified the MODIS confidence thresholds against the MODIS C6/C6.1 user guide (Table 11)
  and the VIIRS classes against the VIIRS C2 user guide.
- Found and fixed, through tests, that `httpx` logs full request URLs (which contain the
  MAP_KEY) at INFO level: the client now installs log redaction and quiets those loggers.
- Configuration via `pydantic-settings` with `SecretStr`; `.env.example`.

**Outputs:** `src/firms_mcp/firms/`, `src/firms_mcp/config.py`, `src/firms_mcp/redaction.py`,
`tests/unit/firms/`, [FIRMS API client design](../design/FIRMS_API_CLIENT.md),
[Configuration](../developers/CONFIGURATION.md).

**Requirements implemented:** FR-DATA-001 … 004, 007 … 013, SEC-001, FR-AUTH-001.
**Tests:** 125 passing.

**ARL milestones supported:** ARL2-M1 and ARL3-M1 (API client component).

### 2026-10-10 — WP5: FIRMS Fire Map links (`feature/map-links`)

**What was done**

- `firms_mcp.maplinks`: a pure builder for the Fire Map's URL-hash grammar (mode, dates,
  layers, area of interest or center/zoom) on the global and US/Canada maps, with referral
  parameters and a plain-language description of what each link shows.
- A catalog snapshot of the map's configuration (267 layers, 9 modes, 37 modules) drives
  validation: every layer must exist and be available in the chosen mode; per-satellite
  layers switch the link to Advanced mode; a basemap is always included.
- Verified in the browser: builder output loads exactly as described; the US/Canada map
  shares the grammar (minimum zoom 4); global zoom range 1–16.
- `scripts/check_map_catalog.py` detects drift against the live map bundle (no drift on
  2026-10-10).

**Outputs:** `src/firms_mcp/maplinks/`, `scripts/check_map_catalog.py`,
`tests/unit/maplinks/`, [Map links design](../design/MAP_LINKS.md).

**Requirements implemented:** FR-MAP-001 … FR-MAP-006. **Tests:** 149 passing.

**ARL milestones supported:** ARL2-M1 and ARL3-M1 (map-link component).

### 2026-10-10 — Signed replay of WP4 and WP5 (`main`)

**What was done:** with the owner present to approve 1Password signing, the two features
held as tree snapshots were replayed as signed commits and `--no-ff` merges
(`feature/firms-api-client` → `951aa26`, `feature/map-links` → `b4bf2b6`). `main`'s tree
equals the final snapshot tree; 149 tests pass. ARL LifeCycle entry L-2 recorded.

### 2026-10-10 — WP6: viability case (`main`)

**What was done**

- Wrote the [viability case](../plan/VIABILITY_CASE.md) against nine criteria fixed in
  advance (components, integration, FIRMS capacity, credential handling, value,
  alternatives, user effort, organizational constraints, keeping current), each rated
  demonstrated, supported, or open, with the conditions under which the concept would not
  be viable.
- Ran a feasibility spike with the locked FastMCP 4.1.0 / `mcp` 2.3.0: tools with
  structured output, resources, resource templates, prompts, and a custom route work for
  handshake-era (2025-11-25) and 2026-07-28 clients, in memory and over Streamable HTTP;
  2026-07-28 requests carry `Mcp-Method` / `Mcp-Name` headers (used by WP8's step-up).
- Computed query costs with FIRMS's displayed transaction-weight formula and measured
  response sizes (about 400 bytes per detection, 470 bytes per source summary).
- Surveyed comparable MCP servers in the MCP Registry and on the web
  ([References §8](../research/REFERENCES.md#8-comparable-mcp-servers)).

**ARL milestones supported:** ARL3-M3 (recorded in L-3; owner review pending).

### 2026-10-10 — WP7: MCP server (`feature/mcp-server`)

**What was done**

- `firms_mcp.server` assembles a FastMCP 4 server from the three components: nine tools
  registered from per-tool `manifest.json` files (Earthdata MCP layout: manifest,
  Pydantic models, entry function), resources `firms://knowledge/index`,
  `firms://knowledge/{entry_id}`, and `firms://sources`, prompts
  `investigate_fire_activity` and `explain_detection`, server instructions defining
  *Orient → Retrieve → Contextualize → Link*, `/health`, `/.well-known/ard.json`, and
  `server.json` for the MCP Registry. CLI: `firms-mcp` (stdio) and `firms-mcp http`.
- `get_fire_detections` returns per-source summaries, paged records (limit, tool- and
  query-scoped cursor, field selection, sort), an explicit-only confidence filter with
  removed counts, FIRMS caveat references, the Fire Map disclaimer and FIRMS citation
  verbatim from the knowledge base, a map link reproducing the area, UTC days, and
  satellites, and provenance with the key redacted. One failed source does not fail the
  call.
- Tools validate arguments with their own models and return every outcome as structured
  content (`status`, `error_code`, `remediation`), flagged `isError` for errors.
- Credentials: local (stdio) use reads `FIRMS_MAP_KEY`; remote (HTTP) use ignores the
  operator's key unless `FIRMS_MCP_ALLOW_OPERATOR_KEY=true`; malformed keys are rejected
  before any FIRMS call. `FIRMS_MCP_KNOWLEDGE_DIRS` moved into the settings so `.env`
  values apply.
- Tested in both protocol eras, in memory, over Streamable HTTP (in-process ASGI), and
  over stdio with the real process; a raw 2025-06-18 `initialize` is accepted.
- Started the integration issues log (II-01 … II-08).

**Outputs:** `src/firms_mcp/server.py`, `src/firms_mcp/tools/`, `src/firms_mcp/services.py`,
`src/firms_mcp/credentials.py`, `src/firms_mcp/instructions.py`, `src/firms_mcp/prompts.py`,
`src/firms_mcp/resources.py`, `src/firms_mcp/discovery/ard.json`, `server.json`,
[Tool catalog](../design/TOOLS.md), [Architecture](../design/ARCHITECTURE.md),
[Adding a tool](../developers/ADDING_A_TOOL.md),
[Integration issues](INTEGRATION_ISSUES.md).

**Requirements implemented:** FR-KB-010, FR-DATA-005, FR-DATA-006, FR-DATA-014,
FR-MCP-001 … FR-MCP-008, FR-AUTH-002, SEC-002, NFR-001 … NFR-004, DOC-002.
**Tests:** 217 passing (68 new).

**ARL milestones supported:** ARL4-M1 (in progress until authentication is integrated).

### 2026-10-10 — WP8: MAP_KEY connect flow (`feature/oauth-map-key`)

**What was done**

- `firms_mcp.auth.provider.FirmsOAuthProvider` (a FastMCP `OAuthProvider`): clients by
  Client ID Metadata Document (FastMCP's `CIMDClientManager`) or Dynamic Client
  Registration with safe redirect URIs; `/authorize` → a pending authorization and the
  connect page; the key checked with FIRMS's MAP_KEY status service; a single-use code
  returned with `state` and `iss`; PKCE S256 at `/token`; JWE access tokens (`dir` +
  A256GCM, one hour, audience-bound) and rotating refresh tokens with replay detection
  that revokes the family; RFC 7009 revocation for public clients; RFC 8707 resource
  checks.
- The connect page: no scripts, CSP pinned by hash, framing denied, a browser-binding
  cookie and a CSRF token, five attempts, clear messages for malformed, rejected, or
  unverifiable keys, a cancel button, and the "not operated or endorsed by NASA" label.
- `firms_mcp.auth.stepup.StepUpAuth`: 401/403 challenges for tools whose manifest sets
  `require_auth`, from the `Mcp-Name` header on 2026-07-28 requests and the JSON-RPC body
  otherwise; anonymous tools pass through.
- Remote credential resolution reads the connected key from the verified token; the
  operator key applies only to anonymous calls and only when allowed.
- `firms-mcp keygen`; settings for the public URL, token keys, lifetimes, and client
  registration methods.
- Running the command and the tests found eight integration issues (II-09 … II-16), all
  worked out, including two defects in this work package.

**Outputs:** `src/firms_mcp/auth/`, `src/firms_mcp/credentials.py`,
`tests/integration/test_oauth_flow.py`, `tests/unit/test_stepup.py`,
`tests/unit/test_tokens.py`, [Authentication](../design/AUTHENTICATION.md).

**Requirements implemented:** FR-AUTH-003 … FR-AUTH-010, SEC-003, SEC-004.
**Tests:** 251 passing (34 new).

**ARL milestones supported:** ARL2-M1 and ARL3-M1 complete (all four components); phase
gate G1 — computed ARL 3 (L-5), pending the owner's review of the viability case.
