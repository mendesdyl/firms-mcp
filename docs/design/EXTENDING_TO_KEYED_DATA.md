# Extending to Keyed Data (option C)

Iteration 2 builds a keyless server: knowledge, URL building, and keyless checks
([ADR-0011](../decisions/0011-keyless-scope-typescript-rewrite-standard-data-first.md)).
This document is the design for adding **option C** — fetching FIRMS data with a MAP_KEY
so that the agent can see detections — without disturbing the keyless core. It is a plan,
not a commitment: nothing here is built until the owner decides to, and that decision is
recorded in a new ADR.

## 1. What C would add

| Capability | Why someone would want it |
|---|---|
| Detections for an area and dates, summarized per source | The agent can say how many detections each satellite made, when, day or night, with what confidence — with FIRMS's caveats attached — instead of handing over a URL |
| Data availability and MAP_KEY status, fetched | The agent can check coverage and remaining transactions itself |
| Records the client can draw | The basis for an in-chat map with time animation ([ADR-0009](../decisions/0009-interactive-map-via-mcp-apps.md)), which is on the owner's wish list |

What C does **not** change: content stays verbatim, the server still informs rather than
concludes, and standard-processing (SP) data are still preferred over NRT.

## 2. Preconditions

C should not start until these are answered, because the answers decide which path in §3
applies:

1. **Who runs the server.** If NASA FIRMS hosts it, FIRMS may serve its own data without a
   user key at all (path C3). If a third party hosts it, a user key is needed.
2. **FIRMS policy on third-party services using users' MAP_KEYs** (running list LU-06,
   operations issue OG-03). Iteration 1's viability case named FIRMS objecting as kill
   condition K1.
3. **Whether an operator-wide key is acceptable** for anonymous use (OD-04, OG-04).
   Default: no.
4. **Which hosts the target users use**, and whether those hosts complete an OAuth connect
   flow and per-tool step-up (LU-09).

## 3. Three paths

| Path | How the key gets to FIRMS | When it fits | Weight |
|---|---|---|---|
| **C1 — Local only** | The user sets `FIRMS_MAP_KEY` in their own environment; the server reads it at start-up | Someone running their own copy with Claude Desktop, Claude Code, or another local agent | Small: a client module and one or two tools, no auth |
| **C2 — Remote, user connects a key** | An OAuth 2.1 connect flow: the user enters the key once on a connect page; the server keeps it inside an encrypted, audience-bound token | A public server run by someone other than FIRMS | Large: iteration 1's whole WP8 |
| **C3 — FIRMS-hosted** | No user key: FIRMS's own backend serves the data, under FIRMS's own limits | FIRMS adopts the server | Depends on FIRMS's internals; likely the lightest for users |

Recommended order: **C1 first** (it proves the data path with no new security surface),
then **C3 if FIRMS adopts the server**, and **C2 only if a third party must host a public
server** and FIRMS agrees to key handling.

## 4. Design

### 4.1 Shape

The keyed capability is an **optional module** that the server registers only when it is
enabled. The keyless core does not import it.

```
src/
  knowledge/        keyless (iteration 2)
  maplinks/         keyless
  apiurls/          keyless — builds URLs, chooses SP or NRT
  sources/          keyless — catalog, SP first
  keyed/            option C — only loaded when FIRMS_MCP_ENABLE_KEYED_DATA=true
    client.ts       FIRMS area / data_availability / mapkey_status calls
    parse.ts        CSV → typed records, per sensor family
    summarize.ts    per-source summaries
    budget.ts       transaction budget
    tools/          firms_get_fire_detections, firms_get_data_availability, firms_get_map_key_status
  auth/             option C2 only
```

The URL builder already decides the source, dates, and windows for a request. The keyed
client takes that same decision and fetches it, so SP-first behaviour and input
validation are written once.

### 4.2 Tools added

| Tool | Returns |
|---|---|
| `firms_get_fire_detections` | Per-source summaries (count, time range, day/night split, confidence breakdown, FRP statistics, extent), paged records with a cursor, the caveat entry IDs, the Fire Map disclaimer and FIRMS citation verbatim, a Fire Map link reproducing the query, and the request URL with the key redacted |
| `firms_get_data_availability` | Coverage per source from the documented `data_availability` service |
| `firms_get_map_key_status` | Transactions used and the limit |

Rules carried from iteration 1 ([ADR-0007](../decisions/0007-data-tool-design.md)):

- results are summaries first and records on request, with a maximum page size;
- confidence filtering only on explicit request, with the removed count reported;
- every time in UTC with an explicit `Z`;
- one failed source does not fail the call;
- a FIRMS error becomes a stable error code with remediation text.

### 4.3 Key handling

- No tool accepts a key as a parameter (SEC-002 stays).
- The key never appears in a result, log line, error message, or link (SEC-001):
  requests are logged with the key replaced by `[MAP_KEY]`, and HTTP client logging is
  silenced or redacted. (Iteration 1 found that `httpx` logs full URLs at INFO level; the
  TypeScript HTTP client must be checked for the same thing.)
- **C1**: the key comes from the environment; remote (HTTP) mode ignores it unless the
  operator explicitly allows an operator key (OD-04).
- **C2**: port iteration 1's design ([ADR-0004](../decisions/0004-authentication-bring-your-own-map-key.md),
  [Authentication](../design/AUTHENTICATION.md)): Client ID Metadata Documents with
  Dynamic Client Registration as a fallback, PKCE S256, single-use codes, `iss` on
  responses, encrypted audience-bound access tokens, rotating refresh tokens with replay
  detection, and per-tool step-up so the keyless tools keep working anonymously.

### 4.4 FIRMS limits

FIRMS allows 5,000 transactions per key per 10 minutes. The keyed module keeps a
per-key budget using the weight formula FIRMS's own area page displays (running list
LU-02), caches identical requests (short TTL for NRT, long for SP), and coalesces
concurrent identical requests. A request that would exceed the budget is refused with an
explanation rather than sent.

### 4.5 The in-chat map

Once detections can be fetched, an MCP Apps view
([ADR-0009](../decisions/0009-interactive-map-via-mcp-apps.md)) can draw them with a time
slider. That needs a host that supports MCP Apps (LU-09) and is a separate step after C.

## 5. Reusing iteration 1

Iteration 1 implemented all of C in Python. Tag `v0-iteration-1` holds the reference
implementation and its tests:

| Concern | Iteration-1 location |
|---|---|
| API client, CSV parser, summaries, cache, budget, errors | `src/firms_mcp/firms/` |
| Detection tool and paging cursors | `src/firms_mcp/tools/get_fire_detections/`, `src/firms_mcp/tools/common.py` |
| Key redaction | `src/firms_mcp/redaction.py` |
| OAuth connect flow, tokens, step-up | `src/firms_mcp/auth/` |
| Tests | `tests/unit/firms/`, `tests/integration/test_oauth_flow.py`, `tests/unit/test_stepup.py`, `tests/unit/test_tokens.py` |
| Design | [FIRMS API client](FIRMS_API_CLIENT.md), [Authentication](AUTHENTICATION.md) |

The tests are the most valuable part to port: they encode the CSV columns per sensor
family, the MODIS and VIIRS confidence semantics checked against the user guides, and
the attacks the connect flow must refuse.

## 6. Requirements

These requirements were marked `deferred` by ADR-0011 and become active again:

- **C1:** FR-DATA-001, 003, 004, 005, 006, 007, 009, 012, 013, 014; FR-AUTH-001.
- **C2 adds:** FR-AUTH-003 … FR-AUTH-010; SEC-003, SEC-004.
- **C3:** to be written with FIRMS; most of the C1 list applies with FIRMS's internal data
  access in place of the HTTP client.

## 7. Effect on readiness (ARL)

Adding C adds a component, so ARL2-M1 and ARL3-M1 need the new component created and
tested independently, and ARL4-M1 needs it integrated, before the computed ARL can move
past where the keyless server stands. Operations and governance (ARL4-M2) gains back the
key-related issues OG-01 … OG-04, OG-10, and OG-13. The [ARL guide](../arl/ARL_GUIDE.md)
explains the rule.

## 8. Steps, when the owner decides to go ahead

1. Record the decision and the chosen path in a new ADR that supersedes ADR-0011 §1.
2. Reactivate the requirements in §6 and write the tests first, porting iteration 1's.
3. Build the keyed module behind `FIRMS_MCP_ENABLE_KEYED_DATA`.
4. Validate live with a real MAP_KEY (running list OD-05, LU-01 … LU-03).
5. For C2 only: port the connect flow and walk it through each target host.
6. Record a LifeCycle ARL entry.
