# ADR-0005: Knowledge base — verbatim, provenance-tracked, extensible

- **Status:** Accepted
- **Date:** 2026-10-09
- **ARL linkage:** ARL1-M2 (baseline research made available), ARL2-M1 and ARL3-M1
  (component and its independent validation), ARL4-M2 (content governance).

## Context

The owner supplied the full FIRMS FAQ and asked that "the documentation of these FAQs
should not be boiled down" and that "there should be a mechanism to add more information
in the future as the content of the site is ever evolving". The server's purpose is to
inform the answering agent, not to answer for it; FIRMS's own wording carries caveats that
paraphrase can lose.

The live FAQ (<https://www.earthdata.nasa.gov/data/tools/firms/faq>) is a single HTML page
whose sections are `<h2 id="…">` headings followed by accordion items, each a question
(button text) and an answer (HTML with links, lists, tables, and figures with captions).

## Decision

1. **Unit of content:** one Markdown file per FAQ question, with YAML front matter:
   `id`, `title` (the question, verbatim), `kind` (`faq` | `supplement`), `section`,
   `section_title`, `source` (ID in `knowledge/sources.yaml`), `source_url` (with anchor
   where available), `retrieved`, `content_sha256`, `tags`, `related`, `status`
   (`current` | `retired`).
2. **Verbatim body:** the answer converted from HTML to Markdown preserving every
   sentence, link target, list, table, figure alt text, and caption. No summarization or
   editing. Section introductions and the page preamble are stored as their own entries.
3. **Provenance:** `knowledge/sources.yaml` registers each source (publisher, URL,
   retrieval date, licensing note). The owner-provided FAQ text is kept unmodified in
   `knowledge/snapshots/` as the reference snapshot.
4. **Completeness check (the "not boiled down" guarantee):** an automated test normalizes
   whitespace and markup and asserts that every non-empty line of the reference snapshot
   appears in the knowledge base. Any loss fails the build.
5. **Refresh mechanism:** `scripts/sync_faq.py` fetches the live FAQ, regenerates entry
   files, and writes a change report (added, changed, retired entries). A human reviews the
   diff and commits. Entries that disappear from the live page are marked `retired`, kept
   for provenance, excluded from search by default, and flagged when retrieved by ID.
6. **Extension mechanism:** curated content that is not on the FAQ page (the Fire Map
   disclaimer, attribute definitions, API notes) lives in `knowledge/supplements/` with
   the same front matter and its own source entry. Operators can add directories through
   `FIRMS_MCP_KNOWLEDGE_DIRS`. Every file is schema-validated at startup (unique IDs,
   required fields, hash matches body); invalid content stops the server rather than being
   served silently.
7. **Retrieval:** deterministic lexical ranking (BM25 with field boosts for title, tags,
   and body). Search results return the **full verbatim body** of each hit, never a
   generated summary, with a short snippet only as an aid.
8. **Serving:** tools (`search_knowledge`, `get_knowledge_entry`, `list_knowledge_topics`)
   because many hosts only surface tools to the model, plus resources
   (`firms://knowledge/index`, `firms://knowledge/{entry_id}`) for hosts that let users
   attach context.

## Alternatives considered

| Alternative | Why rejected |
|---|---|
| Hand-written summaries of the FAQ | Violates the owner's requirement; loses FIRMS's caveat wording |
| One large document | Poor retrieval granularity; floods context |
| Embedding/vector search | Adds a model dependency and non-determinism for ~150 curated entries; the Earthdata MCP is itself moving away from its embedding pipeline. Can be added behind the same interface later |
| Live scraping on every request | Slow, fragile, and loads NASA's site; the committed snapshot is reviewable and testable |

## Consequences

- The knowledge base is reviewable in pull requests like code.
- FAQ updates are a scripted, reviewed procedure documented in
  [Adding knowledge](../developers/ADDING_KNOWLEDGE.md).
- NASA-authored text is reproduced with attribution. Content on NASA sites is generally
  not subject to copyright in the United States; attribution and the source link are
  retained on every entry.
