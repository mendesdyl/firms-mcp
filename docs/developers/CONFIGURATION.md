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
| `FIRMS_MCP_KNOWLEDGE_DIRS` | — | Extra knowledge directories, `:`-separated |
| `FIRMS_MCP_ALLOW_OPERATOR_KEY` | `false` | On remote deployments, serve anonymous data requests with `FIRMS_MAP_KEY` |

Authentication settings for remote deployments (token keys, public URL) are documented in
[Authentication](../design/AUTHENTICATION.md).
