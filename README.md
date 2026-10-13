# FIRMS MCP

A [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server that gives AI
assistants direct, well-documented access to NASA's
[Fire Information for Resource Management System (FIRMS)](https://firms.modaps.eosdis.nasa.gov/):
active fire detections, the complete FIRMS FAQ and product documentation, and links into
the FIRMS Fire Map.

> **Status:** under active development — Phase I (Discovery & Feasibility) of the
> [project plan](docs/plan/PROJECT_PLAN.md). See the [ARL assessment log](docs/arl/ARL_ASSESSMENT_LOG.md)
> for the current readiness level and the [running list](docs/project/RUNNING_LIST.md) for
> what is in progress.

> **Not an official NASA product.** This project uses public NASA FIRMS services and
> reproduces NASA documentation with attribution. It is not affiliated with or endorsed by
> NASA. As FIRMS states: *"Do not use for the preservation of life or property.
> Satellite-derived active fire / thermal anomalies have limited accuracy."*

## What it does

The server does not answer science questions. It gives the agent that is answering the
data, FIRMS's own explanations, and the caveats it needs to answer accurately.

| Capability | Description | Needs a FIRMS MAP_KEY? |
|---|---|---|
| **Fire detections** | Active fire / thermal anomaly detections for an area and date window from VIIRS (Suomi NPP, NOAA-20, NOAA-21), MODIS (Terra, Aqua), and Landsat (US/Canada), with summaries, caveats, citation, and a map link | Yes (the user's own key) |
| **Knowledge base** | The full FIRMS FAQ, verbatim and searchable, plus the Fire Map disclaimer, attribute definitions, and API notes, each with its source and retrieval date | No |
| **Fire Map links** | Links that open the FIRMS Fire Map at the right place, dates, satellites, and basemap | No |
| **Data availability** | Date coverage for each FIRMS source | Optional |
| **KML footprints** | Download links for FIRMS fire-footprint KMZ files by region and period | No |
| **In-chat map** *(planned)* | Interactive, animated map of detections rendered in MCP Apps–capable clients | Yes |

The planned tool, resource, and prompt surface is in the
[project plan §7.1](docs/plan/PROJECT_PLAN.md#71-planned-mcp-surface-initial).

## Connecting

There are two ways to use the server:

- **Remote (public chatbots such as Claude.ai or ChatGPT):** add the server's URL (ending
  in `/mcp`) as a custom connector. Knowledge and map tools work right away. When the
  assistant first needs FIRMS data, you are sent to a one-page "Connect your FIRMS
  MAP_KEY" step; the key goes to the server and FIRMS, never into the chat. Request a free
  key at <https://firms.modaps.eosdis.nasa.gov/api/map_key/>. Details:
  [Authentication](docs/design/AUTHENTICATION.md). No public endpoint is running yet
  (hosting is owner decision OD-02).
- **Local (Claude Desktop, Claude Code, Cursor, VS Code):** run the server over stdio
  with your key in the `FIRMS_MAP_KEY` environment variable.

Step-by-step instructions per client will be in the [user guide](docs/consumers/USER_GUIDE.md).

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

- **Follows NASA's Earthdata MCP** ([`nasa/earthdata-mcp`](https://github.com/nasa/earthdata-mcp)):
  Python + FastMCP, one directory per tool with a versioned `manifest.json`, Pydantic
  models, workflow-defining server instructions, anonymous use with per-tool step-up
  authentication. See [ADR-0002](docs/decisions/0002-follow-nasa-earthdata-mcp-conventions.md).
- **Current MCP specification** (2026-07-28, stateless) with support for clients on earlier
  revisions; Streamable HTTP and stdio transports. See
  [ADR-0003](docs/decisions/0003-target-mcp-2026-07-28-with-backward-compatibility.md).
- **Readiness tracked with NASA's Application Readiness Levels**: Start-of-Project ARL 1,
  Goal ARL 7.

## Development

Requirements: Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --extra dev
```

```bash
uv run pytest
```

Run the server locally on stdio (put your key in `.env` as `FIRMS_MAP_KEY`), or over
Streamable HTTP at `http://127.0.0.1:8000/mcp`:

```bash
uv run firms-mcp
```

```bash
uv run firms-mcp http
```

The tools, resources, and prompts are described in the [tool catalog](docs/design/TOOLS.md);
the structure of the server in [Architecture](docs/design/ARCHITECTURE.md).

Contributor guidelines: [CONTRIBUTING.md](CONTRIBUTING.md). Security reports:
[SECURITY.md](SECURITY.md).

## Acknowledgments

Data and documentation: NASA FIRMS. FIRMS asks that scientific publications use: *"We
acknowledge the use of imagery from the NASA LANCE FIRMS (https://earthdata.nasa.gov/firms),
part of the NASA Earth Science Data and Information System (ESDIS)."*

Design precedent: NASA's Earthdata MCP server.

## License

[Apache License 2.0](LICENSE).
