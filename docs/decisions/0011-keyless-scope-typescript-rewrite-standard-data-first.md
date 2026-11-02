# ADR-0011: Keyless scope, TypeScript rewrite, standard data first

- **Status:** Accepted
- **Date:** 2026-11-02
- **Supersedes in part:** [ADR-0004](0004-authentication-bring-your-own-map-key.md) (the
  remote connect flow and token handling are retired) and
  [ADR-0007](0007-data-tool-design.md) (detection fetching is retired; input validation
  and the source catalog carry over).
- **ARL linkage:** ARL2-M1, ARL3-M1, ARL4-M1, ARL4-M2 (re-verification on the TypeScript
  code; see the [ARL guide](../arl/ARL_GUIDE.md) and LifeCycle entry L-8).

## Context

Iteration 1 ([retrospective](../project/ITERATION_1_RETROSPECTIVE.md)) reached a computed
ARL 4 with a Python server that fetched detections with the user's MAP_KEY and held that
key, for remote users, through an OAuth 2.1 authorization server. Most of the code, the
open FIRMS policy questions (LU-06, OD-04), and viability kill condition K1 sat in that
data-and-key path.

The owner's goals for the next iteration, from a design review on 2026-11-02:

- the server should be something **NASA FIRMS would run**, light enough to move into
  FIRMS's PHP backend / TypeScript frontend, while anyone can run their own copy until a
  public one exists;
- it gives people **information to draw their own conclusions**, never the answer to a
  science question;
- **URL building** is a core feature;
- FIRMS's FAQ changes often, and the server must keep its verbatim copy current with a
  human check before agents see new text;
- **standard-processing (SP) data is more authoritative than near-real-time (NRT) data**
  by design of the algorithms, and must be preferred wherever it exists.

## Decision

### 1. Scope: knowledge, URL building, and keyless checks

The server does **(a)** knowledge and URL building and **(b)** keyless checks. It does
**not (c)** fetch FIRMS data with a user's key; how to add (c) later is designed in
[Extending to keyed data](../design/EXTENDING_TO_KEYED_DATA.md).

The server holds no credentials, keeps no per-user state, and needs no authentication.

### 2. MAP_KEY: a placeholder, filled by the agent

- No tool accepts a MAP_KEY. URLs that need one contain the literal placeholder
  `[MAP_KEY]`, and the result says where the user gets a key
  (<https://firms.modaps.eosdis.nasa.gov/api/map_key/>) and where it goes in the URL.
- The server instructions tell the agent: if the user has shared their key in the
  conversation, substitute it into the URL for them, and remind them once that a key
  typed into a chat stays in the transcript.
- Every URL-building result carries a fixed `limitations` statement: the server built the
  URL but cannot fetch, summarize, or chart what it returns.

### 3. Tools

Seven read-only tools, prefixed `firms_` (MCP best practice for discoverability):

| Tool | Purpose |
|---|---|
| `firms_search_knowledge` | Ranked search over the verbatim knowledge base |
| `firms_get_knowledge_entry` | One entry by ID, verbatim, with provenance |
| `firms_list_knowledge_topics` | Sections, entry IDs, and titles |
| `firms_build_fire_map_url` | FIRMS Fire Map deep link (global or US/Canada) |
| `firms_build_api_url` | FIRMS API URLs: area CSV, `data_availability`, MAP_KEY status; the missing-data reference; links to the archive download and MAP_KEY sign-up pages |
| `firms_build_kml_footprint_url` | KML fire footprint download link (see §7) |
| `firms_list_data_sources` | Source catalog, SP sources first |

Knowledge entries are also MCP resources. A single API-URL tool rather than one per
endpoint keeps the tool list short for the agent. The keyless map date service is not a
tool of its own; `firms_build_api_url` and `firms_build_fire_map_url` use it internally
(§4).

### 4. Standard data first

SP data are preferred over NRT wherever SP covers the requested dates. This is the
owner's rule; the server instructions state it and point to the FAQ entry
`faq.getting-started.what-are-the-key-differences-between-urt-rt-nrt-and-standard` for
the reason, **without paraphrasing it**.

- **Coverage** comes from FIRMS's keyless map date service (`/api/map_dates/`), presented
  as "the dates the FIRMS Fire Map currently shows". If it fails or changes shape, the
  server falls back to the static source catalog and says the coverage could not be
  checked.
- **API URLs** (`firms_build_api_url`, area CSV):
  - dates fully covered by SP → the SP source (`MODIS_SP`, `VIIRS_SNPP_SP`,
    `VIIRS_NOAA20_SP`);
  - dates spanning the end of SP coverage → **two labelled URLs**: SP up to the last SP
    date, NRT after it;
  - dates after SP coverage → NRT, with a note that SP is not yet available for those
    dates and NRT is provisional;
  - sensors with no SP product (VIIRS NOAA-21, Landsat) → NRT, saying so.
  - The documented `data_availability` URL is offered alongside, with `[MAP_KEY]`, as
    the publicly advertised way to check coverage.
- **Fire Map links**: past dates covered by SP use the SP layers
  (`fires_modis_aqua_sp`, `fires_modis_terra_sp`, `fires_viirs_snpp_sp`,
  `fires_viirs_noaa20_sp`); NOAA-21 has no SP layer, so its NRT layer is used and the
  description says so.
- **"Today" / "last 24 hours"**: NRT, with a short note that SP cannot exist yet for those
  dates.
- **Source catalog**: SP sources first, marked preferred.

### 5. Content: verbatim, with pointers

FAQ and documentation text is served verbatim ([ADR-0005](0005-knowledge-base-verbatim-and-extensible.md)
unchanged). The server instructions add short guidance written by the project — present
data and caveats, leave the conclusion to the user, prefer SP — and that guidance points
to FAQ entries by ID; it never restates what they say.

### 6. Keeping knowledge current

- The FAQ sync is **ported to TypeScript**. The first sync pull request after the port is
  reviewed closely: it is also the check that the port reproduces the text exactly.
- A **scheduled GitHub Actions workflow** (weekly, and runnable by hand) runs the sync and
  opens a pull request containing the regenerated Markdown and a change report (added,
  changed, retired entries) for the owner to review before anything ships.
- At **deploy/build time** the files are only **checked** against the live page (warn or
  fail); deploy never rewrites them.
- If the page structure breaks the parser, the last good copy stays in place and the
  workflow fails visibly so the owner is alerted.
- How to switch the scheduled syncs off is documented in the operations procedures.

### 7. Missing data and KML

- **Missing data**: FIRMS's missing-data table (`/api/missing_data/`) is keyless but
  undocumented and slow (71 seconds for 169 rows on 2026-11-02). The weekly sync also
  saves it as a dated reference file. Whenever a question touches missing or absent data,
  the server answers from that file, states the date it was saved, and always gives the
  live page URL.
- **KML**: KML footprint files download and need a GIS tool to open. The tool description
  and server instructions say to offer KML only when the user mentions GIS, footprints,
  or tools such as Google Earth or QGIS, and otherwise to ask whether they work with KML
  before suggesting it. Results say the link downloads a file.

### 8. Implementation

- **TypeScript** on a current Node.js LTS, with the **MCP TypeScript SDK v2**
  (`@modelcontextprotocol/server`), Zod schemas, `outputSchema` and structured content on
  every tool, and read-only/idempotent annotations.
- **Transports**: stdio for local use; stateless Streamable HTTP (JSON responses) for a
  hosted deployment.
- Tool contracts, the Fire Map grammar and layer catalog, and the knowledge Markdown are
  kept as language-neutral data files, so a later port (for example to PHP) rewrites only
  a thin layer.
- The TypeScript code **replaces** the Python code on `main`; iteration 1 stays at
  `v0-iteration-1`. The `evaluation/` harness stays in Python and talks to the server over
  MCP.
- Whether to keep the Earthdata-style per-tool `manifest.json` layout
  ([ADR-0002](0002-follow-nasa-earthdata-mcp-conventions.md)) in TypeScript is decided in
  the project-setup step and recorded in its own ADR.

### 9. Distribution

Nothing is published to npm, a container registry, or the MCP Registry until the owner
has spoken with FIRMS. The documentation explains how to run a local copy with Claude
Desktop and Claude Code, what the equivalent steps are for Codex, opencode, and other
agent tools, and that public use from Claude.ai or ChatGPT needs a server reachable from
the internet, which the eventual hosted version provides.

### 10. Process

Everything from iteration 1 carries over: ADRs, the running list, the work summary, the
ARL log, `requirements.yaml` with test traceability (tags such as `[REQ-FR-KB-001]` in
vitest test names), and signed commits merged `--no-ff`. In addition:

- one `feature/*` branch per step, deleted locally and on GitHub once merged; at any time
  only `main`, `archive/iteration-1`, `feature/evaluation`, and at most one active
  branch;
- each step ends with a short note to the owner: the branch, what changed, and what needs
  review or approval.

### 11. Requirements

Requirements that only applied to (c) are marked **`deferred`** (a new status) in the
project-setup step, not deleted, so the trail stays complete:

| Status in iteration 2 | Requirements |
|---|---|
| Carried over | FR-KB-001 … FR-KB-010; FR-MAP-001, 002, 004, 005, 006; FR-DATA-010, 011; FR-MCP-002 … 008; SEC-001, SEC-002; NFR-001 … 004; DOC-001 … 003; PRJ-001 |
| Carried over, reworded | FR-DATA-002 (validates URL-builder inputs); FR-DATA-008 (coverage from the map date service, used to choose SP or NRT); FR-MAP-003 (API source ↔ map layer, now used to choose SP layers); FR-AUTH-002 (no tool needs authentication); FR-MCP-001 (pending the manifest decision in §8); NFR-005 (supported Node.js versions) |
| Deferred | FR-DATA-001, 003, 004, 005, 006, 007, 009, 012, 013, 014; FR-AUTH-001, 003 … 010; SEC-003, SEC-004 |
| New | SP-first selection (§4); `[MAP_KEY]` placeholder and `limitations` statement (§2); scheduled sync pull request and deploy check (§6); missing-data reference (§7); KML gating (§7) |

## Alternatives considered

| Alternative | Why not |
|---|---|
| Keep (a), (b), and (c) | (c) carries the open FIRMS policy questions, key security, and most of the porting weight; it would delay the part of the value that is certain |
| Tool accepts an optional `map_key` and returns a finished URL | The key would pass through the server, its logs, and the host's tool-call records for no gain: the agent can substitute it |
| Keep Python and port later | FIRMS runs PHP and TypeScript; a TypeScript server is closer to their stack and the MCP TypeScript SDK is the reference implementation |
| Write it in PHP now | Fewer MCP examples and tooling; TypeScript keeps the option of a thin PHP port later because contracts live in data files |
| Rewrite FAQ files at deploy time | Unreviewed scraped text would reach agents; a page redesign could silently empty or garble answers |
| A standalone `firms_get_map_dates` tool | "Today" links already show the latest data; the value of the dates is choosing SP or NRT for past dates, which belongs inside the URL builders |
| Fetch the missing-data table live | 71-second responses are too slow for a tool call; a cache would add state |
| Prefer NRT for simplicity | SP is the more authoritative product; NRT is provisional by design |

## Consequences

- No authorization server, tokens, key storage, cache, or rate budget: the server is
  stateless and small, and its security surface is mostly input validation.
- The person gets a working path to the data (the exact URL), but the agent cannot
  summarize detections. Baseline failure mode F1 (fabricated counts) must be answered by
  instruction: the agent says it has not seen the data rather than estimating.
- F9 (MAP_KEY exposure) changes: the server never sees a key, but a user may paste one
  into the chat. The transcript reminder is the mitigation; the extension design for (c)
  restores the connect flow if that is not enough.
- The server depends on two undocumented FIRMS services (`/api/map_dates/`, the
  missing-data table) in addition to the map grammar. Each is added to the questions for
  the FIRMS team, and each has a fallback.
- ARL: the TypeScript components must be re-verified before ARL 4 is claimed again; the
  log records a LifeCycle reassessment to ARL 3 (L-8).
- [ADR-0009](0009-interactive-map-via-mcp-apps.md) (in-client map) stays *Proposed*; it
  depends on (c).

## References

- [Iteration 1 retrospective](../project/ITERATION_1_RETROSPECTIVE.md)
- [Extending to keyed data](../design/EXTENDING_TO_KEYED_DATA.md)
- [ARL guide](../arl/ARL_GUIDE.md)
- FIRMS FAQ entry *What are the key differences between URT/RT/NRT and Standard quality
  fire data?* (`faq.getting-started.what-are-the-key-differences-between-urt-rt-nrt-and-standard`)
