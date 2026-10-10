# ADR-0007: Data tool design

- **Status:** Accepted
- **Date:** 2026-10-09
- **ARL linkage:** ARL2-M1, ARL3-M1, ARL4-M1, ARL5-M1.

## Context

Detection queries can return thousands of rows; model context is finite; FIRMS limits
each MAP_KEY to 5,000 transactions per 10 minutes; detections are easy to misread
([Data products §1, §8](../science/DATA_PRODUCTS.md)). The Earthdata MCP manages context
with small default page sizes, opaque cursors, and field filtering, and returns structured
error objects rather than raising.

## Decision

1. **Inputs** are Pydantic models with `extra="forbid"`:
   - area as `west, south, east, north` decimal degrees (validated ranges, west < east,
     south < north) or the literal `world`; no place-name geocoding in the server (the
     agent supplies coordinates and is instructed on the axis order);
   - `day_range` 1–5 (FIRMS limit) and optional `date` (`YYYY-MM-DD`, not in the future);
   - `sources`: a list of FIRMS API source IDs (default: the three VIIRS NRT sources and
     MODIS NRT);
   - `limit` (default 50, maximum 500), `cursor`, optional `fields`, optional
     `min_confidence` (explicit opt-in filter; never applied silently), `sort`.
2. **Outputs** always include:
   - `status` (`success` | `no_results` | `error`), `error_code`, `error_message`;
   - a per-source **summary** (count, time range, day/night split, confidence breakdown,
     FRP statistics, bounding box of detections);
   - the requested page of normalized **records** (UTC timestamps; sensor-specific fields
     preserved);
   - **caveats**: IDs and titles of the knowledge entries that apply, and the Fire Map
     disclaimer verbatim;
   - the FIRMS **citation** text verbatim;
   - a **map link** reproducing the query ([ADR-0006](0006-firms-fire-map-deep-links.md));
   - **provenance**: FIRMS endpoint with the MAP_KEY redacted, retrieval time, data
     latency notes;
   - a note that detections from different satellites are independent observations and
     must not be summed as a count of fires.
3. **Upstream discipline:** responses cached by request key (short TTL for NRT, longer for
   standard processing), concurrent identical requests coalesced, a per-key client-side
   budget guard below the FIRMS limit, no automatic retries on 4xx, bounded retries with
   backoff on 5xx and timeouts.
4. **Error mapping:** FIRMS's plain-text errors are mapped to stable codes
   (`invalid_map_key`, `rate_limited`, `invalid_request`, `upstream_unavailable`,
   `auth_required`) with a remediation sentence for the agent.
5. **Annotations:** data tools are `readOnlyHint: true`, `destructiveHint: false`,
   `idempotentHint: true`, `openWorldHint: true`.
6. **No silent interpretation:** the server does not cluster detections into "fires",
   estimate area, or rank threats.

## Alternatives considered

| Alternative | Why rejected |
|---|---|
| Return raw CSV | Wastes context; loses typing; no place to attach caveats |
| Server-side geocoding of place names | Adds a dependency and a hidden source of error; agents can supply coordinates and the Earthdata MCP makes the same choice |
| Clustering detections into fire events | Interpretation beyond FIRMS's published data; FIRMS's own FEDS product exists for modeled perimeters |

## Consequences

- Responses are larger than raw rows for tiny queries but bounded for large ones.
- Caveat coverage becomes measurable in evaluation.
