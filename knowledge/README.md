# FIRMS Knowledge Base

Verbatim FIRMS documentation that the MCP server gives to AI agents, with the provenance
of every entry. Design: [ADR-0005](../docs/decisions/0005-knowledge-base-verbatim-and-extensible.md)
and [Knowledge base design](../docs/design/KNOWLEDGE_BASE.md). How to add or refresh content:
[Adding knowledge](../docs/developers/ADDING_KNOWLEDGE.md).

> Content here is NASA's, reproduced word for word with attribution. Do not edit FAQ
> entries by hand: regenerate them with the sync command so they stay identical to the
> source. Nothing in this directory is a summary.

## Layout

| Path | Contents |
|---|---|
| `sources.yaml` | Registry of where content comes from (publisher, URL, retrieval date, licensing note) |
| `faq/<section>/<question>.md` | One entry per question of the [FIRMS FAQ](https://www.earthdata.nasa.gov/data/tools/firms/faq), plus the page preamble and section introductions — generated |
| `supplements/<section>/<name>.md` | Other FIRMS / NASA pages: Fire Map disclaimer, LANCE disclaimer and acknowledgment, attribute definitions, FIRMS API pages — imported verbatim |
| `snapshots/` | Reference copies used by tests. `firms-faq_2026-10-09_owner-provided.txt` is the FAQ text supplied by the project owner; the test suite checks that every line of it is in `faq/` |
| `reports/` | Change reports written by each FAQ sync |

## Entry format

Each entry is Markdown with YAML front matter:

```yaml
---
id: faq.getting-started.what-is-utc        # stable ID used by tools and resources
title: What is UTC?                        # the question or heading, verbatim
kind: faq                                  # faq | faq-section-intro | faq-preamble | supplement
section: getting-started
section_title: Getting Started
source: firms-faq                          # an ID from sources.yaml
source_url: https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-124369-16
retrieved: '2026-10-09'
content_sha256: …                          # hash of the body; checked at load time
order: 16                                  # position within the source
tags: []
related: []                                # IDs of entries this one links to
status: current                            # current | retired
---

<verbatim content>
```

## Contents (2026-10-09)

- **FAQ:** 142 entries — 137 questions in 15 sections, the page preamble, and 4 section
  introductions (VIIRS, MODIS, Experimental Mode, Acronyms).
- **Supplements:** 8 entries — Fire Map disclaimer; LANCE disclaimer and acknowledgments;
  attribute definitions for NRT MODIS and VIIRS; FIRMS API pages for `area`,
  `data_availability`, `map_key`, and `kml_fire_footprints`.

Validate at any time:

```bash
uv run python -m firms_mcp.knowledge validate
```
