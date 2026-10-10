# ADR-0003: Target MCP 2026-07-28 with backward compatibility

- **Status:** Accepted
- **Date:** 2026-10-09
- **ARL linkage:** ARL4-M1 (technical integration), ARL5-M1 ("prototype implementations
  conform to the end-user's target environment and standard interfaces").

## Context

The owner asked for "the most up to date standard and technology that enterprises are
using today". The current MCP specification revision is **2026-07-28** (released
2026-07-28). Its major changes: stateless requests (no `initialize` handshake and no
`Mcp-Session-Id`), mandatory `server/discover`, Multi Round-Trip Requests in place of
server-initiated elicitation and sampling, `resultType` on every result, cacheability
hints (`ttlMs`, `cacheScope`), standard `Mcp-Method`/`Mcp-Name` HTTP headers, Tasks as an
extension, deprecation of Roots/Sampling/Logging and of Dynamic Client Registration in
favour of Client ID Metadata Documents, and RFC 9207 issuer identification. Many hosts in
the field still speak the earlier "handshake-era" revisions (2025-06-18, 2025-11-25).

FastMCP 4.x (4.1.0, 2026-10-08) on the MCP Python SDK 2.x (2.3.0) serves both eras from
one deployment, negotiating per connection.

## Decision

1. Build on FastMCP 4 / MCP SDK 2 and serve **2026-07-28** as the primary revision while
   accepting handshake-era clients.
2. Transports: **Streamable HTTP** for remote use (path `/mcp`), **stdio** for local use.
   The deprecated HTTP+SSE transport is not offered.
3. Design for statelessness: no per-session server state; any cross-call state (for
   example pagination) is carried in opaque, server-minted handles passed as tool
   arguments, as the specification recommends.
4. Use only non-deprecated features: no Sampling, no Roots, no protocol Logging (logs go to
   stderr / structured logs).
5. Every tool declares an `outputSchema` and returns `structuredContent`, plus a text
   rendering for clients that ignore structured content.
6. Every tool declares annotations (`readOnlyHint`, `destructiveHint`, `idempotentHint`,
   `openWorldHint`) and a human-readable `title`.
7. `tools/list` order is deterministic (the specification's SHOULD).
8. List and read results carry cache hints appropriate to the content (static knowledge
   can be cached; live data cannot).
9. Optional extension: **MCP Apps** (`io.modelcontextprotocol/ui`) for the in-client map
   ([ADR-0009](0009-interactive-map-via-mcp-apps.md)); the server degrades gracefully for
   hosts without it.
10. Authorization follows the 2026-07-28 authorization specification
    ([ADR-0004](0004-authentication-bring-your-own-map-key.md)).

## Alternatives considered

- **Target only 2025-11-25.** Rejected: already superseded; the owner asked for current
  practice.
- **Target only 2026-07-28.** Rejected: would exclude hosts that have not upgraded; dual-era
  support costs nothing with FastMCP 4.

## Consequences

- Tests exercise both the modern and the legacy client modes.
- Server-initiated elicitation is not used for anything essential.
- The client compatibility matrix is tracked (running-list item LU-09).

## References

- <https://modelcontextprotocol.io/specification/2026-07-28>
- <https://modelcontextprotocol.io/specification/2026-07-28/changelog>
- FastMCP 4 release notes: <https://gofastmcp.com/getting-started/whats-new>
