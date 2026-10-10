# ADR-0009: Interactive in-client map via MCP Apps

- **Status:** Proposed (implementation on branch `feature/mcp-apps-map`, WP12)
- **Date:** 2026-10-09
- **ARL linkage:** ARL5-M1 (enhancement of the prototype in the target environment).

## Context

The owner's longer-term idea is "a map pulling up in the client", ideally "animating
something that a user is looking for". The MCP Apps extension
(`io.modelcontextprotocol/ui`, apps specification 2026-01-26) lets a tool declare a
`ui://` HTML resource in `_meta.ui.resourceUri`; supporting hosts (Claude, Claude Desktop,
VS Code Copilot, Microsoft 365 Copilot, Goose, Postman, MCPJam, and others) render it in a
sandboxed iframe that exchanges JSON-RPC messages with the host over `postMessage`, can
receive the tool's input and result, and can call the server's tools. External origins
must be declared in `_meta.ui.csp`. FastMCP 4 supports MCP Apps.

## Decision (proposed)

1. A tool `show_fire_map` returns the same structured detection result as
   `get_fire_detections` and declares the UI resource `ui://firms/fire-map`.
2. The UI is a single self-contained HTML document (no build step) using a small mapping
   library loaded from a pinned CDN version, declared in `csp.resourceDomains`.
3. Basemap: NASA GIBS WMTS tiles (public, documented, no key), declared in the CSP.
   Detections are drawn from the tool result, **not** fetched by the iframe, so the
   iframe never needs a MAP_KEY and shows exactly what the agent saw.
4. Animation: a time slider and play control step through detections by acquisition time
   (UTC), with cumulative and window modes; the legend states sensor, pixel size, and the
   FIRMS disclaimer.
5. Each detection's popup lists its attributes and links to the FIRMS Fire Map view
   ([ADR-0006](0006-firms-fire-map-deep-links.md)).
6. Hosts without MCP Apps get the normal structured result and the map link; nothing
   essential depends on the UI.

## Alternatives considered

- **Static image rendering on the server.** Simpler, but not interactive and adds an
  imaging dependency.
- **Embedding the FIRMS Fire Map in an iframe.** The FIRMS site may not permit framing
  (`X-Frame-Options: SAMEORIGIN` observed on FIRMS responses), and it would require the
  host to allow framing a third-party origin.

## Consequences

- Adds front-end code that needs its own tests (resource served, CSP declared, rendering of
  sample data in a headless browser where available).
- Status becomes *Accepted* when the branch merges.
