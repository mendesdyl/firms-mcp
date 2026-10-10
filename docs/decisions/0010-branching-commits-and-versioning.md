# ADR-0010: Branching, commits, and versioning

- **Status:** Accepted
- **Date:** 2026-10-09
- **ARL linkage:** ARL4-M2 (process), ARL8-M3 (maintenance documentation).

## Context

The owner asked for a git repository from the start, incremental commits "when there is
enough to document", and branches for bigger changes. The Earthdata MCP uses decoupled
server and tool versioning.

## Decision

1. **Branches.** `main` is always releasable: tests pass, docs build. Work that adds a
   component or spans several commits is done on `feature/<name>` (or `fix/<name>`,
   `docs/<name>`) and merged with `git merge --no-ff` so the feature remains visible as a
   unit in history. Small documentation updates may go directly to `main`.
2. **Commits.** [Conventional Commits](https://www.conventionalcommits.org/) (`feat`, `fix`,
   `docs`, `test`, `refactor`, `chore`, `ci`, `build`), imperative subject ≤ 72
   characters, a body explaining *why*, and references to running-list item IDs, ADRs, and
   requirement IDs where relevant.
3. **Every merge** to `main` updates the [work summary](../project/WORK_SUMMARY.md), the
   [running list](../project/RUNNING_LIST.md), the [changelog](../../CHANGELOG.md), and,
   when milestones change, the [ARL log](../arl/ARL_ASSESSMENT_LOG.md).
4. **Versioning** (as the Earthdata MCP):
   - Server version in `pyproject.toml` (SemVer): major for breaking protocol or framework
     changes, minor for new tools or features, patch for internal changes.
   - Tool version in each `manifest.json` (SemVer): major for breaking interface changes
     (removed or renamed parameters or output fields), minor for additive changes, patch
     for internal fixes.
   - Knowledge base: each entry carries `retrieved` and `content_sha256`; refreshes are
     noted in the changelog.
5. **Tags.** Releases are tagged `vX.Y.Z` on `main`.

## Consequences

- History reads as a sequence of reviewed features.
- Version numbers tell clients what changed.
