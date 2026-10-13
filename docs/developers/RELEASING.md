# Versioning and Releasing

Versioning follows the NASA Earthdata MCP's methodology
([ADR-0010](../decisions/0010-branching-commits-and-versioning.md)): the server and each
tool have their own semantic versions.

## Versions

| What | Where | Major | Minor | Patch |
|---|---|---|---|---|
| Server | `pyproject.toml` `version` (and `server.json`) | Breaking protocol or framework change, removed tool | New tool, resource, prompt, or feature | Internal change |
| Tool | `src/firms_mcp/tools/<name>/manifest.json` `version` | Removed or renamed parameter or output field | Added parameter or output field | Fix without interface change |
| Knowledge base | Each entry's `retrieved` and `content_sha256` | — | — | Refreshes noted in the changelog |

When a tool's version changes, update its heading in the [tool catalog](../design/TOOLS.md)
(a test checks it). When the server version changes, update `server.json` (`version` and
the package `version`; a test checks both against `pyproject.toml`).

## Releasing

1. On `main`, with the changelog's *Unreleased* section complete: set the version in
   `pyproject.toml` and `server.json`, move *Unreleased* to the new version with the date,
   and commit (signed).
2. Tag the commit `vX.Y.Z` (signed) and push the tag. The **Release** workflow checks that
   the tag equals the package version, builds the wheel and sdist, and publishes to PyPI
   with trusted publishing (configure the `pypi` environment and the trusted publisher on
   PyPI first).
3. Run the **Publish to MCP Registry** workflow by hand once the version is on PyPI. The
   registry checks the `io.github.<owner>` namespace through GitHub OIDC and the PyPI
   package through the `mcp-name:` marker at the top of `README.md`.
4. Record the release in the work summary and, if it changes a milestone (for example a
   public endpoint for ARL 5–7), in the ARL log.

Publication needs owner decisions first: the license (OD-01), the public repository and
its name (OD-03; the registry name in `server.json` is provisional), and, for a remote
endpoint, hosting (OD-02).

## Container image

`Dockerfile` builds a two-stage image: dependencies and the project are installed as a
wheel with uv into a virtual environment, which is copied into a slim runtime image that
runs as an unprivileged user. The default command is `firms-mcp http` on port 8000 with a
health check on `/health`. Configuration is by environment variables
([Configuration](CONFIGURATION.md)); remote deployments need at least
`FIRMS_MCP_PUBLIC_URL` and `FIRMS_MCP_TOKEN_KEYS`
([Operations and governance §4.1](../project/OPERATIONS_AND_GOVERNANCE.md#41-deploying-a-remote-endpoint)).

```bash
docker build -t firms-mcp .
```

```bash
docker run --rm firms-mcp keygen
```
