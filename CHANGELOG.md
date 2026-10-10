# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/) for the server and for each tool
([ADR-0010](docs/decisions/0010-branching-commits-and-versioning.md)).

## [Unreleased]

### Added

- Viability case for the application concept (ARL3-M3), including a survey of comparable
  MCP servers and FIRMS transaction costs for typical queries.
- FIRMS Fire Map link builder (`firms_mcp.maplinks`) for the global and US/Canada maps,
  validated against a snapshot of the map's own layer and mode configuration, with a live
  drift check (`scripts/check_map_catalog.py`).
- FIRMS API client (`firms_mcp.firms`): source catalog, validated areas, async client for
  `area`, `data_availability`, MAP_KEY status, and the public map date service; CSV parsing
  and per-source summaries; response cache with request coalescing; transaction budget
  using FIRMS's displayed weight formula; KML footprint links; stable error codes; MAP_KEY
  redaction in logs and errors.
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
