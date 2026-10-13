# FIRMS MCP — Project Plan

| | |
|---|---|
| **Project** | FIRMS MCP: a Model Context Protocol layer for NASA's Fire Information for Resource Management System |
| **Plan version** | 1.1 |
| **Date** | 2026-10-09 |
| **Project owner / PI** | Dylan Mendes |
| **Implementing agent** | Claude (Anthropic), working under the owner's direction |
| **Readiness framework** | NASA Applied Sciences *Application Readiness Level (ARL)* metric — see [ARL reference](../arl/ARL_METRIC_REFERENCE.md) |
| **Status** | Active — Phase II (Development, Testing, & Validation); computed ARL 4 ([ARL log](../arl/ARL_ASSESSMENT_LOG.md)) |

This plan is the controlling document for the project. Every work package below is tied
to one or more ARL milestones, every design choice is recorded as an
[Architecture Decision Record](../decisions/README.md), and every requirement is traced to
tests in the [traceability matrix](../project/TRACEABILITY.md). Progress is recorded in
the [ARL assessment log](../arl/ARL_ASSESSMENT_LOG.md), the
[running list](../project/RUNNING_LIST.md), and the [work summary](../project/WORK_SUMMARY.md).

---

## 1. Executive summary

AI assistants are increasingly asked about wildfires and other thermal anomalies. Without
direct access to authoritative data they either decline, rely on news articles, or
fabricate specifics; and when they do find FIRMS data they routinely misread it — for
example, treating a 375 m VIIRS pixel centroid as the location and size of a fire, or
summing detections from several satellites as if each were a separate fire.

This project builds an MCP server that sits on top of the existing, public FIRMS services
and gives any MCP-capable agent four things:

1. **Data** — active fire detections and data availability from the official FIRMS API,
   using the user's own FIRMS `MAP_KEY`.
2. **Knowledge** — the complete FIRMS FAQ and related product documentation, served
   verbatim with provenance, through a knowledge base built to be extended as FIRMS
   evolves.
3. **Links** — deterministic deep links into the FIRMS Fire Map (`/map/`) that reproduce
   exactly what the agent queried (area, dates, satellites, basemap).
4. **Visualization (planned)** — an interactive map rendered inside the chat client
   (MCP Apps), including animation of detections over time.

The server does **not** answer science questions. It supplies data, verbatim reference
material, and caveats so that the agent answering the user can do so accurately and with
appropriate qualification.

The design follows NASA's own Earthdata MCP server
([`nasa/earthdata-mcp`](https://github.com/nasa/earthdata-mcp)) wherever it applies
([ADR-0002](../decisions/0002-follow-nasa-earthdata-mcp-conventions.md)) and targets the
current MCP specification, revision **2026-07-28**, while remaining usable by clients on
earlier revisions ([ADR-0003](../decisions/0003-target-mcp-2026-07-28-with-backward-compatibility.md)).

## 2. Background

### 2.1 FIRMS

FIRMS distributes near real-time (NRT) active fire / thermal anomaly detections from
MODIS (Terra, Aqua; 1 km), VIIRS (Suomi NPP, NOAA-20, NOAA-21; 375 m), Landsat 8/9 OLI
(30 m; US/Canada), and geostationary sensors (GOES, Meteosat, Himawari), plus imagery and
derived products. FIRMS is part of NASA LANCE within ESDIS. Programmatic access is through
the FIRMS API (version 4.1.16 at the time of writing), which requires a free `MAP_KEY`
requested by email and limited to 5,000 transactions per 10-minute interval. Details and
citations: [FIRMS data products](../science/DATA_PRODUCTS.md) and
[References](../research/REFERENCES.md).

### 2.2 Model Context Protocol

MCP is an open protocol by which AI applications ("hosts") connect to external servers
offering **tools**, **resources**, and **prompts**. Revision 2026-07-28 made the protocol
stateless (no `initialize` handshake, no `Mcp-Session-Id`), added `server/discover`,
replaced server-initiated requests with the Multi Round-Trip Request pattern, moved Tasks
into an extension, preferred Client ID Metadata Documents over Dynamic Client
Registration, and formalized extensions such as **MCP Apps** (interactive UI in the
conversation). See [ADR-0003](../decisions/0003-target-mcp-2026-07-28-with-backward-compatibility.md).

### 2.3 Precedent: NASA Earthdata MCP

NASA ESDIS/CMR released the Earthdata MCP server (`https://cmr.earthdata.nasa.gov/mcp/v1`)
for discovering Earthdata collections and granules. Its design — Python/FastMCP, one
directory per tool with a versioned `manifest.json`, Pydantic input/output models, server
instructions that enforce a *Discover → Verify → Access* workflow, anonymous discovery with
per-tool step-up authentication, documentation split into consumer and developer guides,
`server.json` for the MCP Registry, and an `ard.json` discovery document — is the template
this project follows. The analysis of that repository (commit `b071caf`, 2026-10-08) is in
[References § Earthdata MCP](../research/REFERENCES.md#nasa-earthdata-mcp).

## 3. Problem statement and objectives

**Problem.** Agents lack (a) authenticated, rate-limit-aware access to FIRMS data, (b) the
scientific caveats FIRMS publishes for interpreting that data, and (c) a reliable way to
send users to the right view in the FIRMS Fire Map.

**Objectives.**

| ID | Objective | Measure of success |
|---|---|---|
| O1 | Give agents correct, current FIRMS detections for a place and time | Tool results match direct FIRMS API output for the same query (live validation) |
| O2 | Give agents the FIRMS FAQ and product documentation verbatim, with provenance | 100 % of the reference FAQ snapshot present in the knowledge base (automated check) |
| O3 | Make caveats unavoidable | Every data response carries caveat references, the FIRMS disclaimer, and the citation text |
| O4 | Produce working FIRMS Fire Map deep links | Generated links load the intended mode, dates, layers, and extent (automated grammar tests + live verification) |
| O5 | Make connecting easy for a public-chatbot user while keeping the FIRMS `MAP_KEY` model | A user adds one URL, completes a one-page connect step, and never pastes the key into a chat |
| O6 | Conform to the current MCP specification and enterprise practice | Works with 2026-07-28 and handshake-era clients; OAuth 2.1 + PRM + CIMD; structured outputs; tool annotations |
| O7 | Be maintainable by others | Complete consumer, developer, design, and science documentation; tests trace to requirements |

## 4. Scope

**In scope**

- Tools, resources, prompts, and server instructions over the FIRMS API (area, data
  availability, MAP_KEY status), FIRMS KML footprint downloads, and the public FIRMS map
  date service.
- A knowledge base containing the full FIRMS FAQ (verbatim), the FIRMS map disclaimer,
  attribute-field definitions, and API notes — with a documented mechanism for adding and
  refreshing content.
- Deep links to the FIRMS Fire Map (global `/map/` and US/Canada `/usfs/map/`).
- Authentication: environment variable for local (stdio) use; OAuth 2.1 "connect your
  MAP_KEY" flow for remote use from public chatbots.
- Local (stdio) and remote (Streamable HTTP) operation; container image.
- Interactive in-client map with time animation via MCP Apps (Phase II, separate branch).

**Out of scope**

- Answering science questions, forecasting fire behavior, or estimating burned area
  (FIRMS itself advises against estimating burned area from active fire detections).
- Life-safety use. FIRMS states: *"Do not use for the preservation of life or property."*
  The server repeats this in every data response.
- Mirroring or redistributing FIRMS data beyond pass-through of what the user requested.
- Email alert subscription management (it is a web workflow on FIRMS; the server links to
  it rather than automating it).
- Presenting the server as an official NASA product. It is an independent project that
  uses public NASA services; see [ADR-0004](../decisions/0004-authentication-bring-your-own-map-key.md)
  and the README disclaimer.

**Guiding principle.** *Inform the agent; do not answer for it.* Tools return data,
verbatim documentation, and provenance. Interpretation is left to the agent, which is
instructed to surface FIRMS's caveats when it interprets.

## 5. Stakeholders

| Stakeholder | Interest | Role in ARL progression |
|---|---|---|
| Public chatbot users (residents, journalists, students, NGO and research staff) | Fast, trustworthy answers about recent fire activity, with a map | End users; beta testers at ARL 6 |
| AI assistants / MCP hosts (Claude, ChatGPT, Copilot, Cursor, …) | Well-described tools, structured results, standard auth | Integration environment at ARL 4–7 |
| NASA FIRMS / LANCE / ESDIS | Correct use of data, citation, rate-limit protection, referral visibility | Candidate **partner** for ARL 7–9; source of truth for content |
| NASA Earthdata MCP team | Consistency across NASA-adjacent MCP servers | Design precedent; possible federation |
| Project owner | A credible, documented, maintainable system | Approves plan and ARL assessments |

## 6. The decision-making activity

ARL is defined relative to an end user's *decision-making activity*. For this project that
activity is: **an AI assistant, acting for a human, deciding what FIRMS data to retrieve,
how to interpret it, which caveats apply, and how to present it** — and the human's
downstream decisions that rely on that answer (situational awareness, reporting, research
data selection). The full characterization — personas, question taxonomy, current
(pre-application) mechanisms, baseline failure modes, and the measurement protocol — is in
[Decision-making characterization](../science/DECISION_CONTEXT.md).

## 7. Application concept

| Component | Purpose | Design record |
|---|---|---|
| FIRMS API client | Typed, async access to `/api/area`, `/api/data_availability`, MAP_KEY status, `/api/map_dates`, KML footprints; error mapping; caching; rate-limit protection | [ADR-0007](../decisions/0007-data-tool-design.md) |
| Detection normalizer | Parse CSV per sensor, normalize attributes, compute summaries | ADR-0007 |
| Knowledge base | Verbatim FAQ + supplements with provenance; search; extension and refresh workflow | [ADR-0005](../decisions/0005-knowledge-base-verbatim-and-extensible.md) |
| Map link builder | Deterministic FIRMS Fire Map URLs from the map's own hash grammar and verified layer catalog | [ADR-0006](../decisions/0006-firms-fire-map-deep-links.md) |
| Auth subsystem | Env-var key (stdio); OAuth 2.1 authorization server whose consent step collects and validates the user's MAP_KEY (remote); per-tool step-up | [ADR-0004](../decisions/0004-authentication-bring-your-own-map-key.md) |
| MCP server | Tools, resources, prompts, server instructions, health, discovery documents | ADR-0002, ADR-0003 |
| In-client map (planned) | MCP App: interactive map of returned detections with time animation | [ADR-0009](../decisions/0009-interactive-map-via-mcp-apps.md) |

### 7.1 Planned MCP surface (initial)

| Kind | Name | Auth | Summary |
|---|---|---|---|
| Tool | `search_knowledge` | none | Search the FIRMS knowledge base; return matching entries verbatim with source |
| Tool | `get_knowledge_entry` | none | Return one or more knowledge entries verbatim by ID |
| Tool | `list_knowledge_topics` | none | Table of contents of the knowledge base |
| Tool | `get_fire_data_sources` | none | Catalog of FIRMS detection sources (sensor, satellite, resolution, latency, coverage, API ID, map layer) |
| Tool | `get_data_availability` | optional | Date coverage per source (documented API with a key; public map date service without) |
| Tool | `get_fire_detections` | MAP_KEY | Detections for a bounding box and date window; summary + records + caveats + citation + map link |
| Tool | `get_map_key_status` | MAP_KEY | Remaining transactions for the user's key |
| Tool | `build_fire_map_link` | none | FIRMS Fire Map URL for an area, dates, sources, and basemap |
| Tool | `get_fire_footprint_kml_links` | none | KMZ footprint download links by region, period, and sensor |
| Resource | `firms://knowledge/{entry_id}` | none | Knowledge entry (Markdown, verbatim) |
| Resource | `firms://knowledge/index` | none | Knowledge index |
| Resource | `firms://sources` | none | Source catalog (JSON) |
| Prompt | `investigate_fire_activity` | none | Guided workflow for "what fire activity is near X?" |
| Prompt | `explain_detection` | none | Guided interpretation of one detection with caveats |
| Tool (planned) | `show_fire_map` | MAP_KEY | MCP App: interactive, animatable map in the client |

Final names, schemas, and annotations are defined in the
[tool catalog](../design/TOOLS.md) as each tool is implemented.

## 8. ARL plan — level by level

**Start-of-Project ARL: 1.** The science and the FIRMS services are mature and published,
and the application idea exists, but at project start none of it had been documented for
this application and no component existed. **Goal ARL (End-of-Project): 7**, defined as
the server deployed as a public remote MCP endpoint, integrated into the operational
environment of at least one partner (for example a NASA FIRMS / Earthdata channel or an
organization running a public assistant), and demonstrated in their decision-making
activity. ARL 8–9 require partner qualification and sustained use and are planned as
post-project sustainment. Justification: [ARL assessment log](../arl/ARL_ASSESSMENT_LOG.md#goal-arl).

The table for each level gives the NASA milestone, what it means for this project, the
deliverable that evidences it, and how it is verified. Status is tracked only in the
assessment log, so that this plan stays stable.

### Phase I — Discovery & Feasibility

#### ARL 1 — Basic Research (Baseline Ideas)

| Milestone | Project interpretation | Evidence (deliverable) | Verification |
|---|---|---|---|
| ARL1-M1 Ideas for how specific research results could enhance decision making developed | How FIRMS detections, FAQ guidance, and map views can improve agent answers about fire activity | §1, §3, §7 of this plan; [Decision context §2](../science/DECISION_CONTEXT.md) | Owner review |
| ARL1-M2 Baseline support research identified and documented | FIRMS products, algorithms, validation literature, API behavior, MCP specification, Earthdata MCP precedent | [Data products](../science/DATA_PRODUCTS.md), [References](../research/REFERENCES.md), [ARL reference](../arl/ARL_METRIC_REFERENCE.md) | Owner review; every claim cites a source |

#### ARL 2 — Application Concept (Invention)

| Milestone | Project interpretation | Evidence | Verification |
|---|---|---|---|
| ARL2-M1 Independent application components formulated and created | API client, normalizer, knowledge base, map link builder, auth module exist as separate modules with their own ADRs | Source under `src/firms_mcp/` per component; ADR-0004…0007 | Code review; module-level tests exist |
| ARL2-M2 Decision making activity to be enhanced identified | Agent-mediated retrieval and interpretation of FIRMS data | [Decision context §1–3](../science/DECISION_CONTEXT.md) | Owner review |
| ARL2-M3 Plans to better characterize the decision making activity developed | Question taxonomy, personas, measurement protocol and metrics | [Decision context §5](../science/DECISION_CONTEXT.md); [Evaluation plan](../design/EVALUATION.md) | Owner review |

#### ARL 3 — Proof of Application Concept (Viability Established)

| Milestone | Project interpretation | Evidence | Verification |
|---|---|---|---|
| ARL3-M1 Components tested and validated independently | Unit tests per component against recorded FIRMS responses, the FAQ snapshot, and the map grammar | `tests/unit/**`; CI results | `pytest` green; coverage report |
| ARL3-M2 Detailed characterization of user decision making process completed (baseline performance, mechanisms, limitations) | Documented pre-application mechanisms (manual FIRMS use, web search, model recall), failure modes, and baseline measurement protocol | [Decision context §3–4](../science/DECISION_CONTEXT.md) | Owner review |
| ARL3-M3 Convincing case for viability made | Technical feasibility (API, auth, limits, spec support, client support) and value case | [Viability case](VIABILITY_CASE.md) | Owner review |

### Phase II — Development, Testing, & Validation

#### ARL 4 — Initial Integration & Verification (Prototype/Plan)

| Milestone | Project interpretation | Evidence | Verification |
|---|---|---|---|
| ARL4-M1 Components brought together; technical integration issues worked out | Components exposed as MCP tools/resources/prompts in one server; stdio and Streamable HTTP; auth integrated; integration issues logged and resolved | `src/firms_mcp/server.py`; `tests/integration/**`; [Integration issues log](../project/INTEGRATION_ISSUES.md) | In-memory and HTTP integration tests green |
| ARL4-M2 Organizational challenges and human process issues identified and managed | MAP_KEY acquisition and limits, FIRMS terms/disclaimer/citation, endorsement and branding, content governance for the knowledge base, support channels, operations ownership, security of user keys | [Operations & governance](../project/OPERATIONS_AND_GOVERNANCE.md) | Owner review; each issue has an owner and a mitigation |

#### ARL 5 — Validation in Relevant Environment (Potential Determined)

| Milestone | Project interpretation | Evidence | Verification |
|---|---|---|---|
| ARL5-M1 Integrated into a functioning prototype with realistic supporting elements | Server running over Streamable HTTP against the live FIRMS API with a real MAP_KEY, used from real MCP clients (MCP Inspector, Claude Code, a public chatbot connector) | Live test run log; client walkthrough transcripts | `pytest -m live` green; recorded walkthroughs |
| ARL5-M2 Potential to improve decision making determined and articulated | Projected impact on answer accuracy, caveat coverage, link correctness, time-to-answer, user effort | [Evaluation plan](../design/EVALUATION.md) §Projected impact | Owner review |

#### ARL 6 — Demonstration in Relevant Environment (Potential Demonstrated)

| Milestone | Project interpretation | Evidence | Verification |
|---|---|---|---|
| ARL6-M1 Beta-tested in a simulated operational environment | Public beta endpoint used by recruited testers through real chatbot clients on scripted and free-form scenarios | Beta report | Report reviewed by owner |
| ARL6-M2 Projected improvements demonstrated | With/without-MCP comparison on the evaluation question set | Evaluation results | Metrics meet thresholds in the evaluation plan |

### Phase III — Integration into Partner's System

#### ARL 7 — Application Prototype in Partner's Decision Making (Functionality Demonstrated)

| Milestone | Project interpretation | Evidence | Verification |
|---|---|---|---|
| ARL7-M1 Integrated into end-user's operational environment | Deployed where a partner's users work (partner-hosted or partner-endorsed endpoint; listed in the MCP Registry) | Deployment record; partner agreement | Partner confirmation |
| ARL7-M2 Functionality tested & demonstrated in decision making activity | Partner-run sessions on real questions | Partner demonstration report | Partner sign-off |

#### ARL 8 — Application Completed & Qualified (Functionality Proven)

| Milestone | Project interpretation | Evidence | Verification |
|---|---|---|---|
| ARL8-M1 Finalized system tested, proven operational within user's environment | Release candidate passing all tests in partner environment; SLOs met | Qualification test report | Partner |
| ARL8-M2 Qualified and approved by user | Partner approval for use | Approval record | Partner |
| ARL8-M3 User documentation and training completed | Consumer guide, operator runbook, training material | `docs/consumers/**`, `docs/operations/**` | Partner review |

#### ARL 9 — Approved, Operational Deployment & Use in Decision Making (Sustained Use)

| Milestone | Project interpretation | Evidence | Verification |
|---|---|---|---|
| ARL9-M1 Sustained use in decision making context | Repeated use over time with monitoring, maintenance, and knowledge-base refresh | Usage and maintenance reports | Partner |

## 9. Work breakdown and phasing

Work packages map to milestones and to git branches. Larger changes are developed on
feature branches and merged into `main` with a merge commit (`--no-ff`) so each feature
remains visible in history ([ADR-0010](../decisions/0010-branching-commits-and-versioning.md)).

| WP | Work package | ARL milestones | Branch |
|---|---|---|---|
| WP0 | Repository, plan, ARL framework, ADR process | ARL1-M1, ARL1-M2 (partial) | `main` |
| WP1 | Baseline research: data products, references, Earthdata MCP analysis | ARL1-M2 | `main` |
| WP2 | Decision-making characterization and evaluation plan | ARL2-M2, ARL2-M3, ARL3-M2 | `main` |
| WP3 | Knowledge base: verbatim FAQ, supplements, loader, search, refresh tooling | ARL2-M1, ARL3-M1 | `feature/knowledge-base` |
| WP4 | FIRMS API client, source catalog, normalizer, caching and limits | ARL2-M1, ARL3-M1 | `feature/firms-api-client` |
| WP5 | FIRMS Fire Map link builder and layer catalog | ARL2-M1, ARL3-M1 | `feature/map-links` |
| WP6 | Viability case | ARL3-M3 | `main` |
| WP7 | MCP server integration: tools, resources, prompts, instructions, discovery docs | ARL4-M1 | `feature/mcp-server` |
| WP8 | Authentication: env var + OAuth 2.1 MAP_KEY connect + step-up | ARL2-M1, ARL4-M1 | `feature/oauth-map-key` |
| WP9 | Operations & governance; integration issues log | ARL4-M2 | `main` |
| WP10 | Packaging: container image, CI, MCP Registry `server.json` | ARL4-M1, ARL5-M1 | `feature/packaging-ci` |
| WP11 | Live validation with real clients; evaluation harness; projected impact | ARL5-M1, ARL5-M2 | `feature/evaluation` |
| WP12 | In-client map and animation (MCP Apps) | ARL5-M1 (enhancement) | `feature/mcp-apps-map` |
| WP13 | Beta program | ARL6-M1, ARL6-M2 | — |
| WP14 | Partner integration, qualification, sustainment | ARL7–9 | — |

### Phase gates

A phase gate is passed when every milestone in the phase is complete in full and recorded
in the assessment log with evidence. Gate reviews produce a LifeCycle ARL entry.

| Gate | Condition | Produces |
|---|---|---|
| G1 | ARL 1–3 milestones complete | LifeCycle ARL 3 |
| G2 | ARL 4 milestones complete | LifeCycle ARL 4 |
| G3 | ARL 5 milestones complete (requires live MAP_KEY validation) | LifeCycle ARL 5 |
| G4 | ARL 6 milestones complete (requires external beta testers) | LifeCycle ARL 6 |
| G5 | ARL 7 milestones complete (requires a partner) | LifeCycle ARL 7 = Goal |

## 10. Requirements

Requirements are maintained in machine-readable form in
[`requirements.yaml`](../project/requirements.yaml), each with an ID, source, rationale,
priority, and verification method. Tests declare the requirements they verify with
`@pytest.mark.req("…")`; a meta-test fails if any requirement whose verification method is
`test` has no test. The human-readable matrix is [TRACEABILITY.md](../project/TRACEABILITY.md).

## 11. Architecture

See [Architecture](../design/ARCHITECTURE.md) and the decision records:

| ADR | Decision |
|---|---|
| [0001](../decisions/0001-record-architecture-decisions.md) | Record architecture decisions |
| [0002](../decisions/0002-follow-nasa-earthdata-mcp-conventions.md) | Follow NASA Earthdata MCP conventions |
| [0003](../decisions/0003-target-mcp-2026-07-28-with-backward-compatibility.md) | Target MCP 2026-07-28 with backward compatibility |
| [0004](../decisions/0004-authentication-bring-your-own-map-key.md) | Authentication: bring your own MAP_KEY |
| [0005](../decisions/0005-knowledge-base-verbatim-and-extensible.md) | Knowledge base: verbatim, provenance-tracked, extensible |
| [0006](../decisions/0006-firms-fire-map-deep-links.md) | FIRMS Fire Map deep links |
| [0007](../decisions/0007-data-tool-design.md) | Data tool design |
| [0008](../decisions/0008-testing-and-verification-strategy.md) | Testing and verification strategy |
| [0009](../decisions/0009-interactive-map-via-mcp-apps.md) | Interactive map via MCP Apps |
| [0010](../decisions/0010-branching-commits-and-versioning.md) | Branching, commits, and versioning |

ADRs not yet written are listed as *planned* in the [ADR index](../decisions/README.md)
and are written on the branch that implements them.

## 12. Verification and validation

| Level | What | How | ARL |
|---|---|---|---|
| Unit | Each component in isolation | `pytest`, recorded fixtures, no network | ARL 3 |
| Contract | Knowledge base completeness against the reference FAQ snapshot; map URL grammar against the map's parser rules | Automated tests | ARL 3 |
| Integration | Server end to end through the MCP client (in-memory and HTTP), including auth flows | `pytest tests/integration` | ARL 4 |
| Live | Against the real FIRMS API with a real MAP_KEY | `pytest -m live` (opt-in; never in CI by default) | ARL 5 |
| Evaluation | Agent task success with vs. without the server | [Evaluation plan](../design/EVALUATION.md) | ARL 5–6 |
| Beta | Real users, real clients | Beta protocol | ARL 6 |

Details: [ADR-0008](../decisions/0008-testing-and-verification-strategy.md) and
[Testing guide](../developers/TESTING.md).

## 13. Risk register

| ID | Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| R1 | FIRMS API changes (e.g., country endpoints are currently marked "not currently available"; `DAY_RANGE` limit changed from 10 to 5) | Medium | High | Strict parsing with clear errors; documented assumptions with retrieval dates; live tests; running-list item to re-verify each release | Owner |
| R2 | Map hash grammar is not a published API and may change | Medium | Medium | Grammar derived from the map's own parser and verified in a browser; layer catalog snapshot with refresh script; link tests; ask FIRMS to confirm | Owner |
| R3 | MAP_KEY rate limit (5,000 transactions / 10 min) exhausted | Medium | Medium | Caching, request coalescing, per-call source limits, clear errors; operator-wide key disabled by default | Owner |
| R4 | User MAP_KEY exposure | Low | High | Key never enters model context or logs; encrypted inside tokens; redaction tests; security review | Owner |
| R5 | Agents misinterpret detections despite caveats | Medium | High | Caveats and disclaimer embedded in every data result; server instructions; evaluation measures caveat coverage | Owner |
| R6 | MCP 2026-07-28 is new; client support uneven | High | Medium | FastMCP 4 dual-era support; test both eras; document client matrix | Owner |
| R7 | Perceived as an official NASA service | Medium | Medium | Clear disclaimer; no NASA logos; attribution per FIRMS guidance | Owner |
| R8 | Knowledge base drifts from the live FAQ | High (over time) | Medium | Refresh script with diff report; content-hash provenance; scheduled review in sustainment | Owner |
| R9 | No partner available for ARL 7+ | Medium | High (for Goal ARL) | Engage FIRMS / Earthdata support early (contact listed in FAQ); public beta builds evidence | Owner |
| R10 | Dependency churn (FastMCP 4.x, MCP SDK 2.x released mid-2026) | Medium | Medium | Version pins with upper bounds; lockfile; CI on supported Python versions | Owner |

## 14. Configuration management

- **Repository**: git, default branch `main`. Feature work on `feature/<name>` branches,
  merged with `--no-ff`. Conventional Commits. See [CONTRIBUTING](../../CONTRIBUTING.md).
- **Versioning**: semantic versioning for the server (`pyproject.toml`) and for every tool
  (`manifest.json`), following the Earthdata MCP methodology
  ([ADR-0010](../decisions/0010-branching-commits-and-versioning.md)).
- **Changelog**: [CHANGELOG.md](../../CHANGELOG.md) (Keep a Changelog format).
- **Secrets**: never committed; `.env` is git-ignored; `.env.example` documents variables.

## 15. Documentation plan

| Audience | Documents |
|---|---|
| Everyone | [README](../../README.md), [docs index](../README.md) |
| Users of chat clients | [User guide](../consumers/USER_GUIDE.md) |
| Developers | [Developer guides](../developers/) — adding a tool, adding knowledge, testing, versioning |
| Reviewers / scientists | [Science notes](../science/), [ADRs](../decisions/), this plan, the [ARL log](../arl/ARL_ASSESSMENT_LOG.md) |
| Project tracking | [Running list](../project/RUNNING_LIST.md), [Work summary](../project/WORK_SUMMARY.md), [Traceability](../project/TRACEABILITY.md) |

## 16. Governance and change control

- This plan changes only through commits that update its version number and add a row to
  the revision history below.
- Design changes require a new or superseding ADR.
- ARL assessments are recorded at each phase gate, at each merge of a feature branch, and
  every August (Fiscal Year ARL), and are never edited after the fact. Corrections are
  added as new entries.

## Revision history

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-10-09 | Initial baseline |
| 1.1 | 2026-10-10 | Status updated: phase gates G1 (ARL 3) and G2 (ARL 4) reached (ARL log L-5, L-7); no change to milestones, work packages, or requirements |
