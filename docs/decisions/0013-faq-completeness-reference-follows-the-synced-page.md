# ADR-0013: FAQ completeness reference follows the synced page

- **Status:** Accepted
- **Date:** 2026-11-18
- **Refines:** [ADR-0005](0005-knowledge-base-verbatim-and-extensible.md) (the completeness
  guarantee) and requirement FR-KB-001.
- **ARL linkage:** ARL3-M1 (knowledge-base component validated), ARL4-M2 (the owner's
  weekly review duty).

## Context

FR-KB-001 required every line of the FAQ text the owner provided on 2026-10-09 to appear in
the knowledge base, and the test passed with 0 missing lines. That proved the converter
keeps FIRMS's wording.

By 2026-11-18 NASA had reworded the FAQ: one question added and eight answers changed,
including the URT/RT/NRT vs Standard answer, which was rewritten into numbered sections. A
sync of that page leaves 17 lines of the October copy nowhere on the page, so the original
test would fail on every sync from now on, although nothing would be wrong.

Iteration 1's guide anticipated this and asked a person to save a new reference copy and
repoint the test after each change. With a weekly automated sync, that manual step would
be forgotten or would block every pull request.

## Decision

1. Each sync that changes entries also saves the page it parsed, compressed, to
   `knowledge/snapshots/firms-faq-page.html.gz`. The committed entries are therefore always
   exactly what that page converts to (a test checks this).
2. **From the first sync on, the completeness reference is that saved page.** Its text is
   read straight from the DOM — every paragraph, list item, table cell, heading, caption,
   and accordion question, one line each — **without the Markdown converter**, and every
   line must appear in the knowledge base after the same normalization as before. The
   reference stays independent of the code it checks.
3. **Until the first sync,** the owner-provided copy remains the reference. The test
   switches over by itself when any FAQ entry carries a retrieval date after 2026-10-09.
   The owner's copy stays in `knowledge/snapshots/` as the historical baseline.
4. List numbers and bullets are dropped from reference lines before comparison, because the
   page sometimes types them as text where the Markdown has list markup.
5. The owner's review of each sync pull request is the human check that the new text is
   FIRMS's own (Operations §4.2).

## Alternatives considered

| Alternative | Why not |
|---|---|
| Keep the October copy as the only reference | Fails on every sync after NASA rewords anything |
| Ask the owner for a fresh copy-paste after each change | A manual step on every sync; easy to forget, and it would block the weekly pull request |
| Compare against the converter's own output | Circular: a converter bug would pass |

## Consequences

- The completeness check keeps working as the FAQ changes, without manual steps.
- The check verifies "everything on the page is in the knowledge base", not "nothing in the
  knowledge base differs from October". Changes are still visible line by line in each sync
  pull request.
- A test also syncs the saved 2026-11-18 page into a copy of the knowledge base and requires
  all 1,015 of its lines, so the DOM-based check runs on every test run, including before
  the first sync.
