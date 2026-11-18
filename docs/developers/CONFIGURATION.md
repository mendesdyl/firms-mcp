# Configuration

The server is keyless and stateless: it never needs or accepts a FIRMS MAP_KEY, and it has
four optional settings, all read from environment variables. A template is in
[`.env.example`](../../.env.example); the server does not read `.env` files itself, so load
one with your shell or process manager if you use it.

| Variable | Default | Purpose |
|---|---|---|
| `FIRMS_MCP_HOST` | `127.0.0.1` | Bind address for `firms-mcp-server http` |
| `FIRMS_MCP_PORT` | `8000` | Port for `firms-mcp-server http` |
| `FIRMS_MCP_ALLOWED_HOSTS` | — | Host names accepted in the `Host` header, comma-separated. Required when binding anywhere but `127.0.0.1`/`localhost`: the server refuses to start without it, so DNS-rebinding protection stays on |
| `FIRMS_MCP_KNOWLEDGE_DIRS` | — | Extra knowledge directories, `:`-separated, validated like the built-in content ([Adding knowledge](ADDING_KNOWLEDGE.md)) |

Referral parameters (`utm_source=firms-mcp&utm_medium=mcp`) are always added to Fire Map links
(FR-MAP-005); the builder can turn them off, but no setting exposes that yet.

## Running the server

After `npm run build`:

```bash
node dist/index.js
```

starts the server on stdio (for local MCP clients such as Claude Desktop and Claude Code). For
stateless Streamable HTTP at `http://127.0.0.1:8000/mcp`, with `/health`:

```bash
node dist/index.js http
```

## Container

The [`Dockerfile`](../../Dockerfile) builds a Node 26 image that serves HTTP on port 8000 as
the unprivileged `node` user. Inside the container the server binds `0.0.0.0`, so
`FIRMS_MCP_ALLOWED_HOSTS` defaults to `localhost,127.0.0.1` (local access through a published
port); set it to your host name for anything else:

```bash
docker build -t firms-mcp .
```

```bash
docker run -p 8000:8000 -e FIRMS_MCP_ALLOWED_HOSTS=firms-mcp.example.org,localhost firms-mcp
```

## Outbound requests

The URL tools (`firms_build_fire_map_url`, `firms_build_api_url`, `firms_list_data_sources`)
make one keyless request per call to FIRMS's map date service
(`https://firms.modaps.eosdis.nasa.gov/api/map_dates/`, 10-second timeout). Without outbound
access they fall back to the dates saved in `src/sources/sources.json` and say so in
`coverage`. Nothing else leaves the server.
