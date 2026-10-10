# Adding and Refreshing Knowledge

The knowledge base is how the server keeps up with FIRMS as its documentation changes.
Three procedures cover every case. All of them keep content verbatim and record where it
came from ([ADR-0005](../decisions/0005-knowledge-base-verbatim-and-extensible.md)).

Install the optional sync dependencies once:

```bash
uv sync --extra dev --extra sync
```

## 1. Refresh the FIRMS FAQ

Run on a branch (`docs/knowledge-refresh-YYYY-MM-DD`):

```bash
uv run python -m firms_mcp.knowledge sync
```

This fetches <https://www.earthdata.nasa.gov/data/tools/firms/faq>, regenerates
`knowledge/faq/`, and writes `knowledge/reports/faq-sync-<date>.md` listing added, changed,
unchanged, and retired entries. Then:

1. Read the report and `git diff knowledge/faq`. Changed entries keep their IDs; reworded
   questions appear as one retired and one added entry.
2. Run the checks:

   ```bash
   uv run python -m firms_mcp.knowledge validate
   ```

   ```bash
   uv run pytest tests/contract tests/unit/knowledge
   ```

   If FIRMS removed or reworded text, the completeness test against the 2026-10-09
   owner-provided snapshot will fail. That is expected: add a new snapshot of the current
   page (owner-provided or saved) under `knowledge/snapshots/`, point the test at it, and
   keep the old snapshot for history.
3. Note the refresh in `CHANGELOG.md` and the [running list](../project/RUNNING_LIST.md).
4. Merge with `--no-ff`.

To work offline from a saved copy of the page:

```bash
uv run python -m firms_mcp.knowledge sync --html saved-faq.html --date 2026-10-09
```

## 2. Add part of another web page

Use `import-page` for any NASA/FIRMS page — select the content with a CSS selector or by
heading text:

```bash
uv run python -m firms_mcp.knowledge import-page --url https://www.earthdata.nasa.gov/data/projects/lance --heading "Disclaimer" --id supplement.disclaimers.lance-disclaimer --title "LANCE Disclaimer" --section disclaimers --section-title "Disclaimers and acknowledgments" --source lance --order 1 --tags disclaimer,citation
```

If the page comes from a new origin, first add it to `knowledge/sources.yaml` (ID,
title, publisher, URL, retrieval date, licensing note). The command writes
`knowledge/supplements/<section>/<name>.md` with the content hash already set.

## 3. Add hand-curated content

For content that cannot be extracted automatically (for example the Fire Map dialog,
which is rendered by JavaScript):

1. Create `knowledge/supplements/<section>/<name>.md` with the front matter shown in
   [knowledge/README.md](../../knowledge/README.md) and the text **copied exactly**.
2. Register its source in `sources.yaml` and explain how it was captured in `notes`.
3. Set the hash:

   ```bash
   uv run python -m firms_mcp.knowledge rehash knowledge/supplements/<section>/<name>.md
   ```

4. Validate and run the tests as above.

## Operator-specific knowledge

Deployments can add their own entries without changing this repository: put Markdown
files (and a `sources.yaml`) in a directory and list it in `FIRMS_MCP_KNOWLEDGE_DIRS`
(separate several directories with `:`). They are validated exactly like built-in content.

## Rules

- Never paraphrase or summarize FIRMS content in the knowledge base.
- Never edit generated FAQ files by hand; re-run the sync.
- Every entry must have a registered source and a correct hash; the server will not start
  otherwise.
