# Viability Case

| | |
|---|---|
| **ARL milestone** | ARL3-M3 — *Convincing case for the viability of the application concept made* |
| **Work package** | WP6 ([project plan §9](PROJECT_PLAN.md#9-work-breakdown-and-phasing)) |
| **Date** | 2026-10-10 |
| **Prepared by** | Implementing agent, for owner review |
| **Status** | Submitted for owner review |

ARL 3 is the level at which "feasibility studies to assess the potential viability of and
provide a proof-of-concept for the application are conducted" while the components are
**not yet integrated** ([ARL reference](../arl/ARL_METRIC_REFERENCE.md)). This document
makes the case for the concept's viability from the evidence gathered in WP0–WP5 and
states, before any integration work, what would make the concept *not* viable.

## 1. The claim

An MCP server that gives AI agents (a) FIRMS active-fire detections retrieved with the
user's own FIRMS `MAP_KEY`, (b) FIRMS's own documentation verbatim with provenance, and
(c) deterministic links into the FIRMS Fire Map is **viable**:

1. it can be built entirely on public, documented FIRMS services and on the current MCP
   standard and SDKs, and three of its four components already exist and are tested;
2. the FIRMS transaction limit comfortably accommodates the queries the decision-making
   activity needs;
3. it addresses specific, documented failure modes of how agents answer fire questions
   today, in ways the comparable servers found on 2026-10-10 do not;
4. it costs users nothing beyond a free FIRMS key and asks them for one connect step;
5. its organizational questions and residual risks are known, each has an owner and a
   fallback, and none of them blocks integration.

**Recommendation:** proceed to ARL 4 (integration: WP7 MCP server, WP8 authentication,
WP9 operations and governance), subject to the open items in §5.

## 2. Criteria

The criteria were fixed before the evidence was assembled. Each is rated:
**Demonstrated** (built and tested in this repository), **Supported** (analysis with cited
sources, not yet exercised end to end), or **Open** (evidence still needed; the closing
action is named).

| ID | Criterion | Rating |
|---|---|---|
| V1 | The application components can be built and validated independently | Demonstrated for 3 of 4; Supported for authentication |
| V2 | The components can be integrated on the current MCP standard and reached by real hosts | Supported (feasibility spike); host matrix Open |
| V3 | FIRMS's limits accommodate realistic use, and results fit an agent's context | Supported (FIRMS's own weight formula); live confirmation Open |
| V4 | The user's credential can be handled without exposing it to the model | Supported (design and building blocks verified) |
| V5 | The application addresses the baseline failure modes of the decision-making activity | Supported (mechanism per failure mode); measurement Open (WP11) |
| V6 | The application offers something the available alternatives do not | Supported (survey of 2026-10-10) |
| V7 | User effort and cost are low | Supported |
| V8 | Organizational and policy constraints permit the application | Supported; FIRMS policy questions Open |
| V9 | The application can be kept current as FIRMS evolves | Demonstrated (drift tooling) |

## 3. Evidence

### 3.1 V1 — Components built and validated independently

| Component | Evidence | Tests | Rating |
|---|---|---|---|
| Knowledge base ([ADR-0005](../decisions/0005-knowledge-base-verbatim-and-extensible.md)) | 150 entries: the complete FIRMS FAQ as 142 verbatim entries plus 8 verbatim supplements, each with source URL, retrieval date, and content hash. Verified line by line against the owner-provided FAQ text: **0 missing lines**. Merged `e9c1bfe`. | 52 | Demonstrated |
| FIRMS API client ([ADR-0007](../decisions/0007-data-tool-design.md), [design](../design/FIRMS_API_CLIENT.md)) | Eight-source catalog; validated areas; async client for `area`, `data_availability`, MAP_KEY status, and the public map date service; one CSV parser for every sensor family; per-source summaries; cache with request coalescing; transaction budget; KML links; stable error codes; MAP_KEY redaction. MODIS confidence classes checked against the MODIS C6/C6.1 user guide (Table 11). Merged `951aa26`. | 73 | Demonstrated |
| Fire Map link builder ([ADR-0006](../decisions/0006-firms-fire-map-deep-links.md), [design](../design/MAP_LINKS.md)) | Links built from the map's own hash grammar and validated against a snapshot of its layer and mode configuration (267 layers); generated links verified by cold loads in the real global and US/Canada maps; drift check against the live map bundle. Merged `b4bf2b6`. | 24 | Demonstrated |
| Authentication ([ADR-0004](../decisions/0004-authentication-bring-your-own-map-key.md)) | Design complete. The building blocks it needs are present in the locked dependencies (checked 2026-10-10): FastMCP 4.1.0's `OAuthProvider` base class and `InMemoryOAuthProvider` reference implementation, `CIMDClientManager` for Client ID Metadata Documents, and `joserfc` 1.7.5 for JWE tokens. To be built in WP8. | — | Supported |

All tests run offline: a test fixture blocks every non-loopback connection (NFR-001).

### 3.2 V2 — Integration on the current standard

**Feasibility spike (2026-10-10).** A throwaway server built with the locked FastMCP 4.1.0
/ `mcp` 2.3.0, with a tool returning a Pydantic model, a resource template, a static
resource, a prompt, and a custom HTTP route, was exercised with the FastMCP client:

| Path | Handshake-era client (`2025-11-25`) | 2026-07-28 client |
|---|---|---|
| In-memory | Tools, structured output, resources, templates, prompts, instructions all worked | Same; negotiated via `server/discover` |
| Streamable HTTP (in-process ASGI) | Worked, with `Mcp-Session-Id` | Worked statelessly; requests carried `Mcp-Method` and `Mcp-Name` headers |

Two findings shape the design: the standard `Mcp-Name` header makes the per-tool step-up
challenge of ADR-0004 possible without parsing request bodies on 2026-07-28 requests, and
the server's instructions reach modern clients only through `server/discover` (a client
that pins the version without discovery does not see them). The spike's checks become
permanent integration tests in WP7.

**Hosts.** Public chatbots connect to remote MCP servers by URL and run the MCP
authorization flow ([ADR-0004](../decisions/0004-authentication-bring-your-own-map-key.md),
context). Which hosts support Client ID Metadata Documents, mid-session step-up after
anonymous use, and MCP Apps is not yet verified — running-list item **LU-09** (Open).

### 3.3 V3 — Capacity within FIRMS's limits

FIRMS allows 5,000 transactions per MAP_KEY per 10 minutes and counts larger requests as
several transactions. The weights below use the formula FIRMS's own area-API page uses to
display a request's transaction amount (running-list item LU-02), computed with
`firms_mcp.firms.budget.transaction_weight` for the default sources (VIIRS S-NPP,
NOAA-20, NOAA-21, and MODIS, all near real time):

| Query | 1 day | 5 days (FIRMS maximum) |
|---|---|---|
| A city or county (1° × 1°) | 7 transactions → 714 queries / 10 min | 33 → 151 |
| A large state (California, ~10° × 10°) | 7 → 714 | 33 → 151 |
| A continent (South America) | 13 → 384 | 65 → 76 |
| The whole world | 117 → 42 | 585 → 8 |

A single user's conversation issues a handful of such queries, so the per-key limit is
not a practical constraint for the decision-making activity
([Decision context §5](../science/DECISION_CONTEXT.md), categories C1–C2). Identical
queries within the cache lifetime cost nothing (FR-DATA-012), and the client refuses a
request that would exceed a configurable budget below the limit (FR-DATA-013). The
formula is FIRMS's *displayed estimate*; it is confirmed against the MAP_KEY status
service once a live key is available (OD-05).

**Context economy.** A detection serializes to about 380–420 bytes of JSON and a
per-source summary to about 470 bytes (measured on the test fixtures). A default page of
50 records is therefore about 20 KB; a summary of four sources is under 2 KB. The planned
tool design (ADR-0007) returns summaries first and pages records with a cursor and field
selection, so even a world query that matches tens of thousands of detections produces a
bounded response.

### 3.4 V4 — Credential handling

The key decision is that the MAP_KEY never passes through the model: locally it comes
from the environment; remotely it is entered once on the server's own connect page,
validated with FIRMS, and carried inside encrypted, audience-bound tokens
([ADR-0004](../decisions/0004-authentication-bring-your-own-map-key.md)). Redaction is
already implemented and tested: tests found that `httpx` logs full request URLs (which
contain the key) at INFO level, and the client now filters and quiets those loggers
(SEC-001). This matters for viability because the most direct alternative mechanism,
passing the key as a tool argument, puts it in the conversation (failure mode F9, §3.6).

### 3.5 V5 — Value: the failure modes it addresses

Baseline failure modes F1–F11 are those characterized in
[Decision context §4](../science/DECISION_CONTEXT.md); they are hypotheses until the
evaluation measures them (WP11, ARL 5–6).

| Failure mode | Mechanism in this application | Component state |
|---|---|---|
| F1 fabricated or stale counts | Live detections with retrieval time and the FIRMS request (key redacted) | Client and parser built and tested |
| F2 a detection read as a fire of pixel size at an exact location | FIRMS's own explanation attached to every result; pixel footprint (`scan`/`track`) in records | Knowledge entry present verbatim; attachment in WP7 |
| F3 detections summed across satellites | Per-source summaries with overpass counts; explicit note in every result | Summaries built and tested |
| F4 time-zone errors | UTC timestamps with explicit offset; FIRMS's "What is UTC?" entry | Built and tested |
| F5 "no detections" when data are not yet processed | Processing level per record (URT/RT/NRT/SP); availability tool; latency notes | Parser and availability client built |
| F6 omitted caveats | Caveat entries per source; knowledge search; server instructions | Knowledge base built; instructions in WP7 |
| F7 broken or misleading map links | Links from the map's own grammar, verified in the real map | Built, tested, verified |
| F8 missing or wrong citation | FIRMS's citation text verbatim in every data result | Text present in the knowledge base; attachment in WP7 |
| F9 MAP_KEY exposure | Key never a tool argument; encrypted tokens; redaction | Redaction built; OAuth in WP8 |
| F10 life-safety overreach | Fire Map disclaimer verbatim in every data result; instructions to redirect | Text present; attachment in WP7 |
| F11 burned area estimated from detections | FIRMS's answer to "Can I estimate burned area from active fire data?" found by search | Built and tested |

Against the pre-application mechanisms M1–M4 (Decision context §3), the application
combines what M1 (the FIRMS map and downloads) does well — authoritative, current data —
with what M2–M3 (assistants) do well — answering in language — while removing M4's key
exposure. The projected impact on accuracy, effort, and risk is in the
[evaluation plan §5](../design/EVALUATION.md); demonstrating it is ARL6-M2, not part of
this case.

### 3.6 V6 — Alternatives (survey of 2026-10-10)

The official MCP Registry was searched for "firms" and "fire", and the web for FIRMS MCP
servers. The survey was not exhaustive; it records what the public descriptions say.

| Alternative | What it offers (per its public description) | Relation to this project |
|---|---|---|
| `io.github.pipeworx-io/nasa-firms` (MCP Registry, v0.1.1; MIT) | Tools for detections in a box or near a point and for data availability; remote endpoint and `npx` package. Its README states the MAP_KEY is supplied as an `_apiKey` tool argument, with a platform environment-variable fallback. No FIRMS documentation content or Fire Map links are described. | Same data access. A key passed as a tool argument enters the model's context (F9), which ADR-0004 rejects. No caveat, citation, or map-link layer |
| Wildfire MCP Server (community, aliafsahnoudeh) | Combines FIRMS hotspots with weather, air-quality, and Earth Engine data; directory listings say each data source needs its own key | Broader scope, different purpose (analysis across sources); no FIRMS documentation layer described |
| `com.olyport/wildfire`, `com.daedalmap/wildfires` (MCP Registry) | Wildfire incident data from the National Interagency Fire Center; aggregated wildfire events (paid per call) | Adjacent: incidents and events, not satellite detections |
| NASA Earthdata MCP (`nasa/earthdata-mcp`) | Discovery of CMR collections and granules, Harmony transformations | Complementary; the design precedent ([ADR-0002](../decisions/0002-follow-nasa-earthdata-mcp-conventions.md)); a candidate for federation |

What no alternative found offers: FIRMS's own documentation served verbatim with
provenance; caveats, the Fire Map disclaimer, and the FIRMS citation attached to every
data result; Fire Map links that reproduce the query; and a connect flow that keeps the
key out of the conversation. These are the features aimed at failure modes F2, F6–F10.
Sources are listed in [References §8](../research/REFERENCES.md#8-comparable-mcp-servers).

If FIRMS or NASA publishes an official FIRMS MCP server, this project's components (the
verbatim knowledge base with its refresh tooling, the map-link builder and its catalog
check) remain contributable to it; that is the project's exit path, not a failure of the
concept.

### 3.7 V7 — User effort and cost

- A FIRMS MAP_KEY is free and requested with an email address
  (`supplement.api.map-key`; [References §4](../research/REFERENCES.md#4-firms-services)).
- Remote users add one URL to their chatbot and complete one connect page; knowledge,
  source-catalog, map-link, and KML tools work before connecting (FR-AUTH-002).
- Local users set one environment variable.
- The server has no paid dependencies. Hosting is one small container; its load on
  FIRMS is bounded by each user's own key limit and reduced by caching.

### 3.8 V8 — Organizational and policy constraints

| Constraint | Position | Rating |
|---|---|---|
| Reuse of FIRMS content | FIRMS documentation is a U.S. Government work; NASA content is generally not subject to copyright in the United States. Entries are reproduced verbatim with attribution and a link to the source (`knowledge/sources.yaml`) | Supported |
| Citation and disclaimer | FIRMS asks for "NASA FIRMS" credit and gives an acknowledgment text; the Fire Map shows a disclaimer. Both are served verbatim with every data result (FR-DATA-006) | Supported |
| Endorsement | The project is independent and must not appear to be an official NASA service (plan risk R7) | Supported; wording reviewed in WP9 |
| Third-party services handling users' MAP_KEYs; an operator-wide key | Not addressed in FIRMS's public documentation; asked of Earthdata Support (running-list item LU-06); operator key disabled by default (OD-04) | **Open** |
| Linking to the map's URL hash and adding referral parameters | Grammar derived from the map's own parser; referral parameters mirror the Earthdata MCP; FIRMS confirmation requested (LU-05, LU-14) | **Open** |

These are ARL4-M2 items and are managed in WP9 (operations and governance).

### 3.9 V9 — Keeping current

FIRMS changes (plan risk R1: the `country` endpoints are marked "not currently available"
on the API page, and the area API's `DAY_RANGE` limit is now 5 days), so viability
depends on detecting change:
`python -m firms_mcp.knowledge sync` regenerates FAQ entries from the live page and
reports added, changed, and retired entries; `scripts/check_map_catalog.py` compares the
link builder's catalog with the live map bundle (no drift on 2026-10-10); every knowledge
entry carries a content hash; live tests against the real API run on demand (WP11). Each
tool has its own version (ADR-0010), so changes are visible to clients.

## 4. What would make the concept not viable

| ID | Condition | How it would show | Response |
|---|---|---|---|
| K1 | FIRMS objects to third-party services collecting users' MAP_KEYs | Reply to LU-06 | Distribute for local (stdio) use only, and private deployments where users configure their own key; the anonymous tools (knowledge, catalog, links) remain useful remotely |
| K2 | Major hosts cannot complete the connect flow or the per-tool step-up | Client walkthroughs (LU-09, WP11) | Require authorization at connect time for the whole server (widely supported), or document local use for those hosts |
| K3 | FIRMS's API or map grammar changes incompatibly | Live tests, `check_map_catalog.py`, sync reports | Update the client or catalog; version the affected tools |
| K4 | The evaluation shows no improvement over the baseline | WP11 results (ARL5-M2, ARL6-M2) | Reassess the concept with the owner; the ARL log records the result |

None of K1–K4 has occurred. K1 and K2 change *how* the server is offered, not whether the
components are useful; K4 is the decisive test and belongs to ARL 5–6.

## 5. Conclusion

The case rests on built and tested components (V1, V9), on FIRMS's own published
mechanics for capacity (V3), on a spike against the locked framework versions (V2), and
on a mapping from documented failure modes to concrete mechanisms (V5). The open items do
not block integration:

| Open item | Closed by |
|---|---|
| Authentication component built and tested | WP8 (also completes ARL2-M1 and ARL3-M1) |
| Host compatibility matrix (LU-09) | WP8 and WP11 walkthroughs |
| Live confirmation of transaction weights and CSV headers (LU-02, LU-03) | OD-05 (owner's key in `.env`), WP11 |
| FIRMS policy questions (LU-05, LU-06, LU-14) | WP9, contact with Earthdata Support |
| Measured improvement over the baseline | WP11 (ARL5-M2), beta (ARL6-M2) |

**The application concept is viable. Proceed to ARL 4.**

## 6. Review

| Date | Reviewer | Decision | Notes |
|---|---|---|---|
| 2026-10-10 | Implementing agent | Submitted | Recorded in the [ARL log](../arl/ARL_ASSESSMENT_LOG.md) as LifeCycle entry L-3 |
| | Owner | Pending | If the owner does not accept the case, ARL3-M3 reverts to 🟡 in a new log entry |
