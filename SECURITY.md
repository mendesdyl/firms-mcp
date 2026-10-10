# Security Policy

## Reporting a vulnerability

Please report suspected vulnerabilities privately to the maintainer rather than in a
public issue. Include the affected version or commit, reproduction steps, and the impact
you observed. You will receive an acknowledgment, and fixes will be released as quickly as
practical.

## What this project protects

- **Users' FIRMS MAP_KEYs.** A MAP_KEY is never accepted as a tool argument, never sent to
  the AI model, never written to logs or tool results, and is held only inside encrypted
  tokens on remote deployments. See
  [ADR-0004](docs/decisions/0004-authentication-bring-your-own-map-key.md).
- **Token-encryption keys** (`FIRMS_MCP_TOKEN_KEYS`). Operators must store them in a secret
  manager and rotate them by prepending a new key.
- **The connect page.** Served from the same origin as the MCP endpoint, over HTTPS, with
  no third-party scripts, strict redirect-URI validation, and CSRF protection.

## Scope notes

FIRMS data must not be used for the preservation of life or property. Reports about the
accuracy of FIRMS data itself should go to NASA Earthdata Support
(earthdata-support@nasa.gov, subject "FIRMS").
