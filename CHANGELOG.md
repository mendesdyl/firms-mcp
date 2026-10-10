# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/) for the server and for each tool
([ADR-0010](docs/decisions/0010-branching-commits-and-versioning.md)).

## [Unreleased]

### Added

- Knowledge base (`knowledge/`, `firms_mcp.knowledge`): the complete FIRMS FAQ as 142
  verbatim entries with provenance, 8 verbatim supplements (Fire Map disclaimer, LANCE
  disclaimer and acknowledgments, attribute definitions, FIRMS API pages), deterministic
  search, strict validation, and `validate` / `rehash` / `sync` / `import-page` commands.
  Verified line by line against the owner-provided FAQ text (0 missing lines).
- Decision-making characterization, evaluation plan, 61 machine-readable requirements,
  and a requirements-traceability harness.

- Repository initialized with the ARL-structured project plan, NASA ARL metric reference
  and assessment log, Architecture Decision Records 0001–0010, FIRMS data-products
  baseline, research references (including an analysis of NASA's Earthdata MCP), running
  list, and work summary.
