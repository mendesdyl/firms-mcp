# FIRMS MCP

A [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server that gives AI
assistants well-documented access to NASA's
[Fire Information for Resource Management System (FIRMS)](https://firms.modaps.eosdis.nasa.gov/):
the complete FIRMS FAQ and product documentation, verbatim, and ready-made links into the
FIRMS Fire Map and the FIRMS API, standard-processing data first. It is keyless: it never
needs or sees a FIRMS MAP_KEY.

> **Status:** iteration 2 — a keyless TypeScript server
> ([ADR-0011](docs/decisions/0011-keyless-scope-typescript-rewrite-standard-data-first.md));
> computed ARL 3 (see the [ARL guide](docs/arl/ARL_GUIDE.md)). Iteration 1 (Python, with
> detection fetching and a MAP_KEY connect flow) is preserved at tag `v0-iteration-1`.
> Developers: [Development](docs/developers/DEVELOPMENT.md).

> **Owner to-do:** the weekly FIRMS FAQ sync runs from a Mac and is **not installed yet**. See
> [Setting up the weekly sync on a Mac](docs/project/OPERATIONS_AND_GOVERNANCE.md#setting-up-the-weekly-sync-on-a-mac).

> **Not an official NASA product.** This project uses public NASA FIRMS services and
> reproduces NASA documentation with attribution. It is not affiliated with or endorsed by
> NASA. As FIRMS states: *"Do not use for the preservation of life or property.
> Satellite-derived active fire / thermal anomalies have limited accuracy."*

## What it does

The server does not answer science questions and does not fetch fire detections. It gives
the agent FIRMS's own explanations and caveats, and builds the exact URLs the user opens to
see the data.

| Capability | Tool | Description |
|---|---|---|
| **Knowledge base** | `firms_search_knowledge`, `firms_get_knowledge_entry`, `firms_list_knowledge_topics` | The full FIRMS FAQ, verbatim and searchable, plus the Fire Map and LANCE disclaimers, attribute definitions, and API pages, each with its source and retrieval date; kept current by a reviewed weekly sync |
| **Fire Map links** | `firms_build_fire_map_url` | Links that open the FIRMS Fire Map at the right place, dates, satellites, and basemap; standard-processing layers for past dates |
| **FIRMS API URLs** | `firms_build_api_url` | Area CSV URLs (standard processing where it covers the dates, near real-time after it), `data_availability`, MAP_KEY status, and FIRMS's missing-data table; URLs carry a `[MAP_KEY]` placeholder |
| **KML footprints** | `firms_build_kml_footprint_url` | Download links for FIRMS fire-footprint KML files, for GIS users |
| **Source catalog** | `firms_list_data_sources` | VIIRS (NOAA-20, NOAA-21, Suomi NPP), MODIS, and Landsat sources, standard processing first, with the dates FIRMS currently has |

Details: [tool catalog](docs/design/TOOLS.md). How fetching data with a user's key could be
added later: [Extending to keyed data](docs/design/EXTENDING_TO_KEYED_DATA.md).

## Connecting

No public endpoint is running yet: nothing is published until the owner has spoken with
FIRMS (ADR-0011 §9). To use the server now, run your own copy over stdio in a local client
such as Claude Desktop or Claude Code (see Development below); a step-by-step self-hosting
guide is running-list item WK-24. To open the API URLs, request a free MAP_KEY at
<https://firms.modaps.eosdis.nasa.gov/api/map_key/> and put it in place of `[MAP_KEY]`.

## Documentation

| Topic | Document |
|---|---|
| Project plan (ARL-structured) | [docs/plan/PROJECT_PLAN.md](docs/plan/PROJECT_PLAN.md) |
| NASA ARL metric and this project's assessments | [Reference](docs/arl/ARL_METRIC_REFERENCE.md) · [Assessment log](docs/arl/ARL_ASSESSMENT_LOG.md) |
| Design decisions | [Architecture Decision Records](docs/decisions/README.md) |
| Scientific background and caveats | [FIRMS data products](docs/science/DATA_PRODUCTS.md) |
| Sources and research notes | [References](docs/research/REFERENCES.md) |
| Running list and work summary | [Running list](docs/project/RUNNING_LIST.md) · [Work summary](docs/project/WORK_SUMMARY.md) |
| All documentation | [docs/README.md](docs/README.md) |

## Design at a glance

- **TypeScript on the MCP TypeScript SDK v2**, stateless, stdio and Streamable HTTP; tool
  contracts generated from Zod schemas into [`contracts/tools.json`](contracts/tools.json)
  so a port to another stack (for example FIRMS's PHP backend) has a fixed target. See
  [ADR-0012](docs/decisions/0012-typescript-project-layout-and-tool-contracts.md).
- **Follows NASA's Earthdata MCP** conventions where they fit
  ([ADR-0002](docs/decisions/0002-follow-nasa-earthdata-mcp-conventions.md)):
  workflow-defining server instructions, one place per tool, versioned contracts.
- **Current MCP specification** (2026-07-28, stateless) with support for clients on earlier
  revisions ([ADR-0003](docs/decisions/0003-target-mcp-2026-07-28-with-backward-compatibility.md)).
- **Readiness tracked with NASA's Application Readiness Levels**: Start-of-Project ARL 1,
  Goal ARL 7.

## Development

Requirements: Node.js 24 or 26 (`.node-version` is 26).

```bash
npm ci
```

```bash
npm run check
```

Build, then run the server on stdio, or over Streamable HTTP at `http://127.0.0.1:8000/mcp`:

```bash
npm run build
```

```bash
node dist/index.js
```

```bash
node dist/index.js http
```

The structure of the server is in [Architecture](docs/design/ARCHITECTURE.md); everyday
commands in [Development](docs/developers/DEVELOPMENT.md).

Contributor guidelines: [CONTRIBUTING.md](CONTRIBUTING.md). Security reports:
[SECURITY.md](SECURITY.md).

## Acknowledgments

Data and documentation: NASA FIRMS. FIRMS asks that scientific publications use: *"We
acknowledge the use of imagery from the NASA LANCE FIRMS (https://earthdata.nasa.gov/firms),
part of the NASA Earth Science Data and Information System (ESDIS)."*

Design precedent: NASA's Earthdata MCP server.

## License

[Apache License 2.0](LICENSE).
