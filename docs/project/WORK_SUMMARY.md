# Work Summary

A task-by-task account of the work done, what it produced, and which ARL milestones and
requirements it supports. It is updated with every merge to `main`
([ADR-0010](../decisions/0010-branching-commits-and-versioning.md)). For open items see the
[running list](RUNNING_LIST.md); for readiness status see the
[ARL assessment log](../arl/ARL_ASSESSMENT_LOG.md).

## Task index

| # | Task (from the owner's request) | Where it is accomplished | Status |
|---|---|---|---|
| T1 | Build an MCP layer on top of the existing FIRMS API | WP4, WP7 — `src/firms_mcp/` | In progress |
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
| T13 | Include all FIRMS FAQs, not boiled down, with a mechanism to add more | [ADR-0005](../decisions/0005-knowledge-base-verbatim-and-extensible.md), WP3 | Designed |
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
