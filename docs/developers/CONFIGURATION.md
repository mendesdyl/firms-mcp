# Configuration

The server reads environment variables (and a `.env` file in the working directory, which
is git-ignored). A template is in [`.env.example`](../../.env.example). Secrets are held as
`SecretStr` and never logged.

| Variable | Default | Purpose |
|---|---|---|
| `FIRMS_MAP_KEY` | — | The user's FIRMS MAP_KEY for local (stdio) use. On remote deployments it is the optional operator key (see `FIRMS_MCP_ALLOW_OPERATOR_KEY`) |
| `FIRMS_API_BASE_URL` | `https://firms.modaps.eosdis.nasa.gov` | FIRMS host (tests point this elsewhere) |
| `FIRMS_MCP_HTTP_TIMEOUT` | `60` | Seconds per FIRMS request |
| `FIRMS_MCP_HTTP_RETRIES` | `2` | Retries for 5xx, timeouts, and connection errors (never for 4xx) |
| `FIRMS_MCP_RETRY_BACKOFF` | `0.5` | Initial backoff in seconds (doubles per retry) |
| `FIRMS_MCP_CACHE_TTL_NRT` | `300` | Cache lifetime for near-real-time sources, seconds |
| `FIRMS_MCP_CACHE_TTL_SP` | `21600` | Cache lifetime for standard-processing sources, seconds |
| `FIRMS_MCP_CACHE_MAX_ENTRIES` | `256` | Response cache size (0 disables caching) |
| `FIRMS_MCP_TRANSACTION_BUDGET` | `4500` | Client-side ceiling on estimated FIRMS transactions per key per 10 minutes (FIRMS allows 5,000) |
| `FIRMS_MCP_REFERRAL` | `true` | Add `utm_source=firms-mcp&utm_medium=mcp` to FIRMS Fire Map links |
| `FIRMS_MCP_KNOWLEDGE_DIRS` | — | Extra knowledge directories, `:`-separated (read through the settings, so `.env` works too) |
| `FIRMS_MCP_HOST` | `127.0.0.1` | Bind address for `firms-mcp http` |
| `FIRMS_MCP_PORT` | `8000` | Port for `firms-mcp http` |
| `FIRMS_MCP_LOG_LEVEL` | `INFO` | Log level; logs are JSON lines on stderr with MAP_KEYs redacted |
| `FIRMS_MCP_ALLOW_OPERATOR_KEY` | `false` | On remote deployments, serve anonymous data requests with `FIRMS_MAP_KEY` |
| `FIRMS_MCP_AUTH` | `oauth` | HTTP only: `oauth` runs the MAP_KEY connect flow; `none` disables it (private deployments) |
| `FIRMS_MCP_PUBLIC_URL` | `http://<host>:<port>` | Public base URL clients use (OAuth issuer and resource); set it behind a proxy or in a container |
| `FIRMS_MCP_TOKEN_KEYS` | temporary key | Token encryption keys, `kid:key` comma-separated (generate with `firms-mcp keygen`); first encrypts, all decrypt |
| `FIRMS_MCP_ACCESS_TOKEN_TTL` | `3600` | Access-token lifetime, seconds |
| `FIRMS_MCP_REFRESH_TOKEN_TTL` | `2592000` | Refresh-token lifetime, seconds (30 days) |
| `FIRMS_MCP_ENABLE_CIMD` | `true` | Accept Client ID Metadata Documents |
| `FIRMS_MCP_ENABLE_DCR` | `true` | Offer Dynamic Client Registration |

## Running the server

```bash
uv run firms-mcp
```

starts the server on stdio (for local MCP clients). For Streamable HTTP at
`http://127.0.0.1:8000/mcp`, with `/health` and `/.well-known/ard.json`:

```bash
uv run firms-mcp http --host 127.0.0.1 --port 8000
```

On stdio the MAP_KEY comes from `FIRMS_MAP_KEY`. Over HTTP the server is meant for remote
users who connect their own key (see [Authentication](../design/AUTHENTICATION.md)); the
operator's `FIRMS_MAP_KEY` is used for anonymous requests only when
`FIRMS_MCP_ALLOW_OPERATOR_KEY=true` (owner decision OD-04).

Authentication settings for remote deployments (token keys, public URL) are documented in
[Authentication](../design/AUTHENTICATION.md).
