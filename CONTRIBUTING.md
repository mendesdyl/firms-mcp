# Contributing

Thank you for helping. This project follows the conventions below so that its history,
documentation, and NASA ARL evidence stay trustworthy.

## Workflow

1. Check the [running list](docs/project/RUNNING_LIST.md) for the item you are working on,
   or add one.
2. Branch from `main`: `feature/<name>`, `fix/<name>`, or `docs/<name>`
   ([ADR-0010](docs/decisions/0010-branching-commits-and-versioning.md)).
3. Make the change with tests. Mark each test with the requirement(s) it verifies:
   `@pytest.mark.req("FR-001")`.
4. Update documentation in the same branch: the ADR you implement or a new one, consumer
   or developer guides, and the knowledge base if content changed.
5. Run the checks:

   ```bash
   uv run ruff check .
   ```

   ```bash
   uv run ruff format --check .
   ```

   ```bash
   uv run pytest
   ```

6. Merge into `main` with `git merge --no-ff`, then update the
   [work summary](docs/project/WORK_SUMMARY.md), [running list](docs/project/RUNNING_LIST.md),
   [changelog](CHANGELOG.md), and — if a milestone changed — the
   [ARL log](docs/arl/ARL_ASSESSMENT_LOG.md).

## Commit messages

[Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `docs:`,
`test:`, `refactor:`, `chore:`, `ci:`, `build:`. Imperative subject of at most 72
characters; a body that explains *why*; references to running-list IDs (`WK-03`), ADRs, and
requirement IDs.

## Versioning

- Server version in `pyproject.toml`; tool versions in each tool's `manifest.json`.
- Bump rules follow the Earthdata MCP methodology; see
  [ADR-0010](docs/decisions/0010-branching-commits-and-versioning.md).

## Scientific content

- Do not paraphrase FIRMS documentation in the knowledge base. Add or refresh it with the
  procedure in [Adding knowledge](docs/developers/ADDING_KNOWLEDGE.md).
- Every factual statement in `docs/science/` cites its FIRMS source.

## Secrets

Never commit a FIRMS MAP_KEY or token-encryption key. Use `.env` (git-ignored).
