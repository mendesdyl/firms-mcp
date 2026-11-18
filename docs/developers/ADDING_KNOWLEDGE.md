# Adding and Refreshing Knowledge

The knowledge base is how the server keeps up with FIRMS as its documentation changes.
Three procedures cover every case. All of them keep content verbatim and record where it
came from ([ADR-0005](../decisions/0005-knowledge-base-verbatim-and-extensible.md)).

## 1. Refresh the FIRMS FAQ

**Normally this happens on its own.** A weekly job on the owner's Mac
(`scripts/mac/knowledge-sync.sh`, Mondays 09:00) regenerates `knowledge/faq/`, saves the
missing-data table, runs `npm run check`, and opens (or updates) one pull request, from the
`knowledge-sync` branch, with the change report. The *Knowledge sync* workflow does the same
when started by hand from the Actions tab, although the FAQ page often refuses GitHub's
runners (II-28). Review it as described in
[Operations §4.2](../project/OPERATIONS_AND_GOVERNANCE.md#42-refreshing-the-firms-faq).

To run the same steps yourself on a branch:

```bash
npm run knowledge -- sync
```

```bash
npm run knowledge -- missing-data
```

```bash
npm run check
```

`sync` fetches <https://www.earthdata.nasa.gov/data/tools/firms/faq> and, if any entry was
added, changed, or retired, writes:

- the regenerated `knowledge/faq/**.md` (changed entries keep their IDs; reworded questions
  appear as one retired and one added entry);
- `knowledge/reports/faq-sync-<date>.md`, the change report;
- `knowledge/snapshots/firms-faq-page.html.gz`, the page it parsed. The completeness test
  reads this page's text straight from the DOM and requires every line in the knowledge base
  ([ADR-0013](../decisions/0013-faq-completeness-reference-follows-the-synced-page.md)).

`sync` refuses, and writes nothing, if the result looks like a broken parse: no questions
found, an empty question or answer, or more than 20 % of current entries about to be retired.
If FIRMS really did reorganize the FAQ, rerun with `--allow-large-change` after checking the
page.

`missing-data` saves FIRMS's missing-data table to `knowledge/reference/missing-data.json`;
an unchanged table keeps the earlier copy and its date.

To work from a saved copy instead of the live page:

```bash
npm run knowledge -- sync --html saved-faq.html --date 2026-11-18
```

To see whether the committed FAQ matches the live page without writing anything (the deploy
check; add `--strict` to fail on a difference):

```bash
npm run knowledge -- check
```

## 2. Add part of another web page

Use `import-page` for any NASA/FIRMS page — select the content with a CSS selector or by
heading text:

```bash
npm run knowledge -- import-page --url https://www.earthdata.nasa.gov/data/projects/lance --heading "Disclaimer" --id supplement.disclaimers.lance-disclaimer --title "LANCE Disclaimer" --section disclaimers --section-title "Disclaimers and acknowledgments" --source lance --order 1 --tags disclaimer,citation
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
   npm run knowledge -- rehash knowledge/supplements/<section>/<name>.md
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
