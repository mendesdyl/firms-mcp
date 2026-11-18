# Versioning and Releasing

> **Nothing is published in iteration 2** ([ADR-0011 §9](../decisions/0011-keyless-scope-typescript-rewrite-standard-data-first.md)):
> no npm package, container registry image, or MCP Registry entry until the owner has spoken
> with FIRMS. The iteration-1 PyPI and MCP Registry workflows and `server.json` remain at tag
> `v0-iteration-1`.

Versioning follows the NASA Earthdata MCP's methodology
([ADR-0010](../decisions/0010-branching-commits-and-versioning.md)): the server and each
tool have their own semantic versions.

## Versions

| What | Where | Major | Minor | Patch |
|---|---|---|---|---|
| Server | `package.json` `version` and `src/version.ts` (a test keeps them equal) | Breaking protocol or framework change, removed tool | New tool, resource, prompt, or feature | Internal change |
| Tool | `version` in its `defineTool(...)` | Removed or renamed parameter or output field | Added parameter or output field | Fix without interface change |
| Knowledge base | Each entry's `retrieved` and `content_sha256` | — | — | Refreshes noted in the changelog |

When a tool's version changes, run `npm run contracts` and update its heading in the
[tool catalog](../design/TOOLS.md) (a test checks it).

## Releasing (when publication is decided)

1. On `main`, with the changelog's *Unreleased* section complete: set the version, move
   *Unreleased* to the new version with the date, and commit (signed).
2. Tag the commit `vX.Y.Z` (signed) and push the tag.
3. Record the release in the work summary and, if it changes a milestone (for example a
   public endpoint for ARL 5–7), in the ARL log.

Publication needs owner decisions first: the license (OD-01) and, for a remote endpoint,
hosting (OD-02). How the image is built and run: [Configuration](CONFIGURATION.md#container).
