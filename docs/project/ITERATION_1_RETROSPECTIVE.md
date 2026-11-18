# Iteration 1 Retrospective

What the first iteration of the FIRMS MCP server was, what it proved, what it cost, and
how the owner decided what iteration 2 keeps. The iteration-1 code is preserved exactly
as it was on branch `archive/iteration-1` and signed tag `v0-iteration-1` (commit
`d41a57d`, 2026-10-12); this document is the narrative that goes with it. The decisions
it leads to are recorded in
[ADR-0011](../decisions/0011-keyless-scope-typescript-rewrite-standard-data-first.md); how
the dropped capability could come back is in
[Extending to keyed data](../design/EXTENDING_TO_KEYED_DATA.md).

## 1. What iteration 1 was

A Python MCP server (FastMCP 4.1, MCP SDK 2.3, MCP revision 2026-07-28 with
handshake-era compatibility) that gave AI agents three things about NASA FIRMS:

| Capability | What it did | Component |
|---|---|---|
| **Knowledge** | Searched and returned FIRMS's own documentation verbatim: 142 FAQ entries (137 questions in 15 sections, preamble, 4 section introductions) and 8 supplements, each with provenance and a content hash | `firms_mcp.knowledge` ([ADR-0005](../decisions/0005-knowledge-base-verbatim-and-extensible.md)) |
| **Links** | Built FIRMS Fire Map deep links from the map's own URL grammar, validated against a 267-layer catalog snapshot, and KML footprint download links | `firms_mcp.maplinks` ([ADR-0006](../decisions/0006-firms-fire-map-deep-links.md)) |
| **Data** | Fetched fire detections, data availability, and key status from the FIRMS API with the user's MAP_KEY; parsed, summarized, paged, cached, and budgeted them | `firms_mcp.firms` ([ADR-0007](../decisions/0007-data-tool-design.md)) |
| **Auth** | Let a remote user "connect" their MAP_KEY through an OAuth 2.1 authorization server (CIMD, DCR, PKCE, encrypted audience-bound tokens, refresh rotation, per-tool step-up) | `firms_mcp.auth` ([ADR-0004](../decisions/0004-authentication-bring-your-own-map-key.md)) |

Nine tools, three resources, two prompts, stdio and Streamable HTTP, a container image,
CI on Python 3.12–3.14. About 10,000 lines of Python and tests; 252 tests passing.

## 2. How it was built

Work packages WP0–WP10, each on its own `feature/*` branch, merged `--no-ff` with signed
commits ([ADR-0010](../decisions/0010-branching-commits-and-versioning.md)); the
[work summary](WORK_SUMMARY.md) has the task-by-task account.

| WP | Content | Result |
|---|---|---|
| WP0–WP2 | Research, plan, ARL reference, ten ADRs, decision-making characterization, 61 requirements with test traceability | ARL 1–2 documentation |
| WP3 | Verbatim knowledge base and FAQ sync | 0 missing lines against the owner's FAQ text |
| WP4 | FIRMS API client | 125 tests at merge |
| WP5 | Fire Map link builder | Links verified by cold loads in the real map |
| WP6 | Viability case (V1–V9, K1–K4) | ARL3-M3 |
| WP7 | MCP server assembling the components | ARL4-M1 in progress |
| WP8 | MAP_KEY connect flow | ARL 3 (phase gate G1) |
| WP9 | Operations and governance (18 issues) | ARL4-M2 |
| WP10 | Packaging and CI | ARL 4 (phase gate G2) |

Readiness at the end: **computed ARL 4**, with owner review pending on ARL3-M3 (viability
case) and ARL4-M2 (operations and governance) — see the
[ARL assessment log](../arl/ARL_ASSESSMENT_LOG.md).

## 3. What it proved

These results carry into iteration 2 regardless of language:

1. **The FAQ can be served verbatim and kept current.** The HTML→Markdown conversion
   changes form, never wording; a line-by-line check against the owner's copy found 0
   missing lines; the sync reports added, changed, and retired entries.
2. **The Fire Map URL grammar is buildable and stable enough to link to.** Every link
   shape was verified in the real global and US/Canada maps, including historical date
   ranges, per-satellite layers (which need Advanced mode), and areas of interest.
   `check_map_catalog.py` detects drift.
3. **Agents need FIRMS's caveats with the data, not after it.** The decision-context work
   ([DECISION_CONTEXT.md](../science/DECISION_CONTEXT.md)) identified eleven baseline
   failure modes (F1–F11) — among them a detection read as a fire of pixel size at an
   exact spot, detections summed across satellites as a count of fires, UTC read as local
   time, "no detections" when data were not yet processed, and caveats left out — and
   most were answered by attaching the relevant FAQ entries rather than by the server
   interpreting anything.
4. **"Inform, don't conclude" is a design rule, not a disclaimer.** The server's job is to
   put FIRMS's data, documentation, and caveats in front of the person so they can reach
   their own answer.
5. **Several FIRMS facts that are not in the public docs**: the MAP_KEY format, the status
   service's responses, the transaction-weight formula FIRMS displays, and a keyless map
   date service (`/api/map_dates/`) that gives the date coverage per product, including
   how far standard-processing (SP) data reaches.

## 4. What it cost

Most of the weight sat in the data and auth components:

- **The OAuth connect flow** (WP8) was the single largest piece: an authorization server,
  a connect page with CSRF and browser binding, JWE tokens, refresh rotation, step-up,
  and eight integration issues (II-09 … II-16) to work out. It exists only so a remote
  server can hold a user's MAP_KEY.
- **The data path** needed a cache, a transaction budget, a CSV parser per sensor family,
  confidence semantics, paging cursors, and key redaction in every log and error.
- **Open organizational questions** all clustered there too: FIRMS's policy on third-party
  services handling users' keys (LU-06, OG-03), whether an operator-wide key is
  acceptable (OD-04, OG-04), and the security of stored keys and tokens (OG-10, OG-13).
  The viability case named FIRMS objecting to third-party key handling as kill condition
  K1.
- **Portability.** FIRMS's own stack is a PHP backend with a TypeScript frontend. A
  Python server with an embedded authorization server is a poor candidate for FIRMS to
  adopt and run.

## 5. How the owner reached iteration 2's scope

In a structured design review on 2026-11-02 the owner weighed three scopes:

- **(a) Knowledge and URL building** — no FIRMS data fetched, no key held;
- **(b) (a) plus keyless checks** — e.g. the public map date service;
- **(c) Fetching detections with the user's MAP_KEY** — iteration 1's data path.

The owner's first instinct was to keep all three, because (c) is what would eventually
allow drawing fire data on a map inside the chat (a wish-list item,
[ADR-0009](../decisions/0009-interactive-map-via-mcp-apps.md)). Two things moved the
decision:

1. **(c) is where the murky water is.** Holding users' keys raises the policy, security,
   and operations questions in §4, none of which FIRMS has answered yet.
2. **The choice of language.** Once the owner chose to rewrite in TypeScript so that the
   server can move into FIRMS's PHP/TypeScript stack, carrying the OAuth and data
   machinery across would have made the port heavy for the part of the value that is
   least certain.

The owner's final answer: **build (a) and (b), and document exactly how to extend to
(c)**. The person still gets a working path to the data: the server builds the exact
FIRMS API URL for their area and dates, with a `[MAP_KEY]` placeholder the agent fills in
if the user shares their key, and says plainly what it cannot do with the results.

The same review settled the rest of iteration 2 (all recorded in ADR-0011): the server is
designed for FIRMS to run, with documentation for anyone to run their own copy; content
stays verbatim and the server instructions point to FAQ entries rather than paraphrasing
them; **standard-processing data is preferred over NRT wherever it exists**, because the
owner considers it more authoritative by design of the algorithms; the FAQ refresh
becomes a weekly reviewed pull request; nothing is published to any registry yet.

## 6. What carries over, what changes, what is retired

| Item | Iteration 2 |
|---|---|
| Verbatim knowledge base, provenance, content hashes, sync with change reports | **Kept**; sync ported to TypeScript and scheduled as a reviewed pull request |
| Fire Map link builder and layer catalog | **Kept**; SP layers chosen for dates SP covers |
| Source catalog | **Kept**; SP sources listed first and marked preferred |
| KML footprint links | **Kept**, offered only to users who work with KML |
| API access | **Changed**: URLs are built, not fetched |
| Data availability | **Changed**: the map date service is used internally to pick SP or NRT; the documented `data_availability` URL is offered to the user |
| Missing-data table | **New**: snapshotted by the weekly sync, always linked to the live page |
| Detection fetching, parsing, summaries, paging, cache, budget | **Retired** to the extension design for (c) |
| OAuth connect flow, tokens, step-up, operator key | **Retired** to the extension design for (c) |
| ARL process, ADRs, running list, requirements traceability, signed `--no-ff` merges | **Kept** |
| Python 3.12–3.14, `uv`, FastMCP | **Replaced** by Node.js LTS, TypeScript, MCP TypeScript SDK v2 |
| `evaluation/` harness | **Kept in Python**; it talks to the server over MCP |

## 7. Lessons

1. **Ask what has to be held before building how to hold it.** Iteration 1 started from
   "keep FIRMS's auth model" and built a full authorization server before asking whether
   the server needed to hold a key at all. Iteration 2 asks first.
2. **The verbatim discipline paid off.** Because nothing in the knowledge base was ever
   paraphrased, the whole of it carries forward unchanged and its correctness does not
   depend on the code that serves it.
3. **Most of the risk sits at the boundary with FIRMS**, not in our code: undocumented
   grammars and services, policy questions, rate limits. Iteration 2 keeps that boundary
   small and lists every undocumented dependency as a question for the FIRMS team.
4. **Branches are only useful if the owner can follow them.** Iteration 1 left nine
   branches behind. Iteration 2 keeps one branch per step, deletes it after merging, and
   ends each step with a short note of what to review and approve.
