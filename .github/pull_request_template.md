## What changes, and why

<!-- The problem or request, and what this change does about it. Link running-list items
(WK-…, LU-…), ADRs, and requirement IDs. -->

## Areas affected

<!-- Tools, components, documentation, deployment. -->

## How it was tested

<!-- Tests added or changed; manual checks (for example, a link opened in the real Fire Map). -->

## Checklist

- [ ] `npm run check` passes (lint, types, tests, contracts, traceability, build, smoke)
- [ ] Tests carry `[REQ-<ID>]` in their names for the requirements they verify; `npm run traceability` run after changing requirements or tests
- [ ] Tool `version` and `package.json` version bumped per ADR-0010 when interfaces or behaviour changed; `npm run contracts` run
- [ ] Documentation updated: tool catalog, design documents, consumer or developer guides
- [ ] Knowledge-base content added or refreshed only through the documented procedure (verbatim, with provenance)
- [ ] Running list, work summary, changelog, and (if a milestone changed) the ARL log updated
- [ ] No MAP_KEY, token key, or other secret in code, tests, logs, or fixtures
