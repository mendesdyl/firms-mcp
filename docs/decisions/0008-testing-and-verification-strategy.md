# ADR-0008: Testing and verification strategy

- **Status:** Accepted
- **Date:** 2026-10-09
- **ARL linkage:** ARL3-M1 (components validated independently), ARL4-M1 (verified to work
  together), ARL5-M1 (realistic supporting elements), ARL6-M2 (demonstrated improvement).

## Context

The owner asked for "tests … checking every functionality from the original design". The
ARL metric requires evidence at each level. Tests must not depend on FIRMS availability or
a personal MAP_KEY to run in CI, but the system must also be validated against the real
service.

## Decision

1. **Requirements traceability.** Requirements live in `docs/project/requirements.yaml`.
   Tests declare what they verify with `@pytest.mark.req("FR-…")`. A meta-test fails when
   any requirement whose verification method is `test` has no test, and a generator keeps
   `docs/project/TRACEABILITY.md` in sync.
2. **Test layers**
   - `tests/unit/` — one component at a time; recorded fixtures; network blocked.
   - `tests/contract/` — knowledge-base completeness against the reference FAQ snapshot;
     map-link grammar against the map parser's rules; layer IDs against the catalog.
   - `tests/integration/` — the assembled server through FastMCP's in-memory client and
     over Streamable HTTP (ASGI), in both protocol eras, including the full OAuth flow.
   - `tests/live/` — marked `live`; real FIRMS API with `FIRMS_MAP_KEY`; skipped unless the
     key is present; never run in CI by default.
3. **Network isolation.** An autouse fixture blocks all outbound HTTP in non-live tests
   (as the Earthdata MCP does); unexpected calls fail loudly.
4. **Fixtures** are small, realistic, and documented: synthetic CSVs built from the FIRMS
   attribute definitions, replaced by recorded live responses (key removed) once
   available (LU-03).
5. **Quality gates** in CI: `ruff` (lint + format check), `pytest` with coverage
   reporting, the traceability meta-test, and the knowledge-base validation.
6. **Evaluation** (ARL 5–6) is separate from tests: scenario-based agent tasks with and
   without the server ([Evaluation plan](../design/EVALUATION.md)).

## Alternatives considered

- **Mock-only testing.** Rejected: cannot reach ARL 5.
- **Live tests in CI with a shared key.** Rejected: secret management and FIRMS load for
  little benefit; live runs are recorded as ARL evidence instead.

## Consequences

- Every feature branch adds `req` markers for the requirements it implements.
- Coverage is reported but traceability, not a coverage percentage, is the acceptance
  criterion.
