# ADR-0004: Authentication — bring your own FIRMS MAP_KEY

- **Status:** Accepted
- **Date:** 2026-10-09
- **ARL linkage:** ARL2-M1 (auth component), ARL4-M1 (integration), ARL4-M2 (human
  process: how users obtain and connect a key; organizational: FIRMS limits and terms).

## Context

- FIRMS authenticates API calls with a **MAP_KEY**: free, requested with an email address
  at <https://firms.modaps.eosdis.nasa.gov/api/map_key/>, delivered by email, limited to
  5,000 transactions per 10-minute interval. The owner asked to keep "the auth system they
  have" while making it "easy for the end user on a public chatbot to connect up".
- Public chatbots (for example Claude.ai custom connectors, ChatGPT apps) connect to a
  remote MCP server by URL and implement the MCP authorization flow (Protected Resource
  Metadata discovery, authorization-server metadata, client registration, PKCE). Their
  users usually cannot set custom HTTP headers.
- Pasting a key into a chat would place it in the model's context, in transcripts, and
  possibly in provider logs.
- The MCP authorization specification (2026-07-28): stdio servers SHOULD take credentials
  from the environment; HTTP servers SHOULD use OAuth 2.1 with Protected Resource Metadata
  (RFC 9728); clients and authorization servers SHOULD support Client ID Metadata
  Documents; Dynamic Client Registration is deprecated but retained for compatibility;
  servers MUST validate token audience and MUST NOT accept or pass through tokens issued
  for other resources.
- The Earthdata MCP allows anonymous discovery and challenges only for tools that need
  credentials (per-tool step-up), proxying to Earthdata Login. FIRMS MAP_KEYs are not
  issued through Earthdata Login, so that proxy pattern cannot produce a MAP_KEY.

## Decision

### 1. Local use (stdio)

The MAP_KEY is read from the `FIRMS_MAP_KEY` environment variable (or a `.env` file). No
OAuth.

### 2. Remote use (Streamable HTTP): "Connect your MAP_KEY" authorization server

The server is its own OAuth 2.1 authorization server, co-hosted with the MCP endpoint.
The user-facing "login" step is a single page on which the user enters their own FIRMS
MAP_KEY:

1. A tool that needs FIRMS data is called without a valid token → HTTP **401** with
   `WWW-Authenticate: Bearer resource_metadata="…", scope="firms:data"`.
2. The client fetches Protected Resource Metadata, then authorization-server metadata,
   registers using a **Client ID Metadata Document** (preferred) or Dynamic Client
   Registration (compatibility), and opens `/authorize` with PKCE (S256), `state`, and the
   `resource` indicator.
3. `/authorize` shows the **connect page**: what is being connected and why; a link to
   request a free key; a password-type input; a statement that the key goes only to FIRMS
   and is never shown to the AI model.
4. On submit the server validates the key's format and checks it with FIRMS's MAP_KEY
   status service. On success it issues a single-use authorization code and redirects to
   the client's registered redirect URI with `code`, `state`, and `iss` (RFC 9207).
5. The token endpoint verifies PKCE and returns a short-lived **access token** and a
   rotating **refresh token**.

### 3. Token format

Access and refresh tokens are **JWE compact serializations** (`alg: dir`,
`enc: A256GCM`, with a `kid`) encrypted with a server key. The payload carries the issuer,
audience (the canonical MCP resource URI), client ID, scopes, issue and expiry times, a
token ID, a pseudonymous subject (a keyed hash of the MAP_KEY), and the MAP_KEY itself.
Consequences:

- The MCP request path is **stateless**: verifying a token needs only the key, matching
  the stateless 2026-07-28 protocol and allowing horizontal scaling.
- The MAP_KEY never leaves the server in clear text; the client holds an opaque value.
- Keys rotate via `FIRMS_MCP_TOKEN_KEYS` (first key encrypts; all keys decrypt).

Short-lived OAuth artifacts — client registrations, pending authorizations,
authorization codes (single-use), refresh-token rotation records — live in a pluggable
key-value store (in-memory by default; a shared store for multi-instance deployments).

### 4. Per-tool step-up

Tool manifests declare `require_auth`. Knowledge, source-catalog, map-link, and KML-link
tools are anonymous. Detection and key-status tools require a token with scope
`firms:data`. Enforcement happens at the HTTP layer before MCP processing (using the
`Mcp-Method`/`Mcp-Name` headers of 2026-07-28 requests, or the JSON-RPC body for
handshake-era requests) **and** again inside the tool (defense in depth).

### 5. Prohibitions

- The MAP_KEY is never a tool parameter, never appears in tool results, logs, error
  messages, or links. Upstream request URLs are recorded with the key redacted.
- Tokens issued by other authorization servers are rejected.

### 6. Optional operator key (off by default)

An operator may configure a server-wide MAP_KEY for anonymous use in a private deployment
(`FIRMS_MCP_ALLOW_OPERATOR_KEY=true`). It is disabled by default because it departs from
the per-user FIRMS key model and concentrates rate-limit consumption (owner decision
OD-04; FIRMS policy question LU-06).

## Alternatives considered

| Alternative | Why rejected |
|---|---|
| MAP_KEY as a tool argument | The key would enter the model's context and transcripts |
| Custom request header (`X-FIRMS-MAP-KEY`) | Public chatbot UIs cannot set headers; OAuth works for developer clients too. May be revisited for private deployments |
| OAuth proxy to Earthdata Login (as Earthdata MCP) | Earthdata Login does not issue FIRMS MAP_KEYs; reconsider if FIRMS binds keys to Earthdata Login accounts |
| URL-mode elicitation to collect the key | Without an authenticated identity there is nothing stable to bind the key to in a stateless protocol; host support varies |
| Opaque tokens with the key stored server-side | Viable, but puts a store lookup on every MCP request; encrypted tokens keep the hot path stateless |
| Operator-wide key by default | Departs from FIRMS's per-user model; one user can exhaust everyone's quota |

## Consequences

- Operators must provision and protect a token-encryption key.
- The connect page is security-sensitive: same origin as the MCP endpoint, HTTPS only,
  CSRF protection bound to the pending authorization, strict redirect-URI matching, no
  third-party scripts, clear "not a NASA site" labelling.
- Revocation of an access token before expiry is not supported (stateless); access tokens
  are therefore short-lived (default 1 hour) and refresh tokens rotate with replay
  detection.
- The full OAuth flow is covered by integration tests (metadata, CIMD and DCR
  registration, PKCE, code reuse, audience checks, refresh rotation, step-up challenges).

## References

- MCP Authorization 2026-07-28: <https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization>
- RFC 9728, RFC 8414, RFC 8707, RFC 7591, RFC 9207, RFC 7516 (JWE), OAuth 2.1 draft 13,
  draft-ietf-oauth-client-id-metadata-document-00
- FIRMS MAP_KEY page: <https://firms.modaps.eosdis.nasa.gov/api/map_key/>
