# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/) for the server and for each tool
([ADR-0010](docs/decisions/0010-branching-commits-and-versioning.md)).

## [Unreleased]

### Added

- Operations and governance: roles, organizational issue register, data handled,
  procedures (deployment, FAQ refresh, catalog checks, key rotation, incidents).
- MAP_KEY connect flow for remote use (`firms-mcp http`): OAuth 2.1 authorization server
  with Client ID Metadata Documents and Dynamic Client Registration, PKCE, RFC 9207 `iss`,
  a connect page that checks the key with FIRMS, encrypted (JWE) audience-bound access
  tokens, rotating refresh tokens with replay detection, revocation, and per-tool step-up
  authentication; `firms-mcp keygen` for token keys.
- MCP server (`firms-mcp`, `python -m firms_mcp`) on stdio and Streamable HTTP, serving
  MCP 2026-07-28 and handshake-era clients: nine tools (`search_knowledge`,
  `get_knowledge_entry`, `list_knowledge_topics`, `get_fire_data_sources`,
  `get_data_availability`, `get_fire_detections`, `get_map_key_status`,
  `build_fire_map_link`, `get_fire_footprint_kml_links`) registered from per-tool
  manifests, three resources, two prompts, server instructions, `/health`,
  `/.well-known/ard.json`, and MCP Registry metadata (`server.json`).
- Detection results with per-source summaries, paged records, FIRMS caveats, the Fire Map
  disclaimer and FIRMS citation verbatim, and a reproducing Fire Map link.
- JSON logs on stderr with MAP_KEY redaction; `FIRMS_MCP_HOST`, `FIRMS_MCP_PORT`,
  `FIRMS_MCP_LOG_LEVEL` settings.
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

### Changed

- `FIRMS_MCP_KNOWLEDGE_DIRS` is read through the settings, so a value in `.env` now
  applies (it was previously read only from the process environment).
