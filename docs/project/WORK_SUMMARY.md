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
| T15 | Link to the FIRMS Fire Map with self-building URLs | [ADR-0006](../decisions/0006-firms-fire-map-deep-links.md), WP5 | Designed (grammar verified) |
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
