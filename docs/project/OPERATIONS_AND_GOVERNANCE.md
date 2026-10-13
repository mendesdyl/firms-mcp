# Operations and Governance

The organizational and human-process side of running FIRMS MCP: who owns what, the issues
that are not technical integration problems, how each is managed, and the procedures that
keep the service correct over time. This document is the evidence for **ARL4-M2**
(*organizational challenges and human process issues identified and managed*); technical
integration issues (ARL4-M1) are in the [integration issues log](INTEGRATION_ISSUES.md).
Its verification is owner review: each issue below has an owner and a mitigation.

## 1. Roles

| Role | Who | Responsibilities |
|---|---|---|
| Owner / PI | Dylan Mendes | Decisions (OD-01 … OD-05), ARL assessments, releases, signing commits, contact with NASA FIRMS / Earthdata, approving changes to the knowledge base |
| Maintainer | The owner, and contributors the owner accepts | Code, tests, documentation, scheduled checks (§4), dependency updates |
| Operator | Whoever runs a remote deployment (none yet; hosting is OD-02) | Hosting, HTTPS, secrets (`FIRMS_MCP_TOKEN_KEYS`), monitoring, incident response for that deployment |
| User | A person connecting a chat client | Requesting their own FIRMS MAP_KEY, connecting it, keeping it private |
| NASA FIRMS / LANCE / ESDIS | External | Source of the data, the documentation, and the map; policy on third-party use; support for data questions (Earthdata Support) |

## 2. Issue register

Status: **Managed** (mitigation in place and verified) · **Open** (mitigation in place;
a decision or an external answer is still needed — named in the last column).

| ID | Issue | Who is affected | Owner | Management | Status |
|---|---|---|---|---|---|
| OG-01 | **Getting a MAP_KEY.** FIRMS issues keys by email; a user without one cannot get detections | Users | Owner | Anonymous tools (knowledge, catalog, links) work without a key; the connect page, the `auth_required` remediation, and the README link to FIRMS's free key request page; the user can return to the same connect page | Managed |
| OG-02 | **Transaction limits.** 5,000 transactions per key per 10 minutes; large or repeated requests can exhaust a key | Users, FIRMS | Maintainer | Response cache and request coalescing; a client-side budget (4,500) with retry-after; `get_map_key_status`; tool descriptions and instructions steer agents to small areas and summaries ([viability case §3.3](../plan/VIABILITY_CASE.md)) | Managed |
| OG-03 | **Third-party handling of users' keys.** FIRMS's public documentation does not say whether a service may collect users' MAP_KEYs on their behalf | Owner, FIRMS, users | Owner | Keys are used only for the user's own requests, never shown to the model, never logged, and stored only inside encrypted tokens (ADR-0004); local (stdio) use does not involve the server operator at all. Question sent to Earthdata Support once a contact is made (LU-06); fallback in [viability case K1](../plan/VIABILITY_CASE.md#4-what-would-make-the-concept-not-viable) | Open (LU-06) |
| OG-04 | **An operator-wide key** would let anyone use one person's quota and departs from FIRMS's per-user model | Operator, FIRMS | Owner | Disabled by default; when enabled it serves only anonymous calls; a connected user's own key always wins (FR-AUTH-010) | Open (OD-04) |
| OG-05 | **Terms, disclaimer, and citation.** FIRMS data come with a disclaimer and a requested citation | Users, FIRMS | Maintainer | Every data result carries the Fire Map disclaimer and FIRMS's citation text verbatim from the knowledge base (FR-DATA-006); the instructions put official emergency information first | Managed |
| OG-06 | **Endorsement and branding.** The service must not appear to be an official NASA product | Owner, NASA | Owner | "Not an official NASA product" in the README, the connect page ("not operated or endorsed by NASA"), the server instructions, the discovery document, and `server.json`; no NASA logos; attribution as FIRMS requests | Managed |
| OG-07 | **Knowledge-base governance.** FIRMS text must stay verbatim and current; edits by maintainers could drift from the source | Users, owner | Maintainer (owner approves) | Verbatim-only rule (ADR-0005); provenance and content hash per entry; the loader refuses edited content whose hash no longer matches; FAQ refresh procedure with a change report (§4.2); completeness test against the owner's FAQ text | Managed |
| OG-08 | **Fire Map URL grammar and layers** are not a published API and may change | Users | Maintainer | Catalog snapshot with a drift check (`scripts/check_map_catalog.py`, §4.3); links described in plain language; FIRMS asked to confirm (LU-05, LU-14) | Open (LU-05, LU-14) |
| OG-09 | **FIRMS API changes** (endpoints, limits, columns) | Users | Maintainer | Strict parsing with clear `upstream_format` errors; unknown columns kept; live tests on demand (WP11, OD-05); FIRMS outage page in remediation text | Managed |
| OG-10 | **Security of user keys and tokens** | Users, operator | Operator (deployment), maintainer (code) | Redaction everywhere (SEC-001); JWE tokens; token-key rotation (§4.4); [SECURITY.md](../../SECURITY.md) reporting route; incident procedure (§4.5) | Managed |
| OG-11 | **Support.** Users may mistake the server for FIRMS support, or report data problems to the wrong place | Users, FIRMS | Owner | Server questions: the project's issue tracker (once the repository is public, OD-03) or the security contact; questions about FIRMS data: Earthdata Support (earthdata-support@nasa.gov, subject "FIRMS"), as SECURITY.md and the FAQ entries say | Open (OD-03) |
| OG-12 | **Operations ownership.** A public endpoint needs hosting, HTTPS, monitoring, and someone to respond | Operator | Owner | Container and CI in WP10; `/health` for liveness; JSON logs; the deployment checklist (§4.1); hosting chosen by the owner | Open (OD-02) |
| OG-13 | **Privacy.** The server handles a credential and sees what users ask about | Users | Operator | §3: no key in logs or results; no tool arguments logged; OAuth records expire; no analytics; referral parameters on links are configurable (`FIRMS_MCP_REFERRAL`) | Managed |
| OG-14 | **Licensing.** Code license and the reuse of NASA text | Owner | Owner | Apache-2.0 provisionally; FIRMS documentation is a U.S. Government work reproduced with attribution and source links (`knowledge/sources.yaml`) | Open (OD-01) |
| OG-15 | **Change and release management.** Changes must stay reviewable and attributable | Owner, maintainers | Owner | ADR-0010 (feature branches, `--no-ff`, Conventional Commits, per-tool versions), changelog, ARL log, signed commits; while the owner is away, finished features are held as tree snapshots and replayed as signed commits (running list, *Pending signed commits*) | Managed |
| OG-16 | **Dependency churn.** FastMCP 4 and the MCP SDK 2 change quickly (plan risk R10) | Maintainer | Maintainer | Bounded version ranges, a lockfile, tests in both protocol eras, integration issues recorded when an SDK behaviour must be worked around (II-10 … II-12) | Managed |
| OG-17 | **Accessibility of the connect page** | Users | Maintainer | Semantic HTML with labelled input, `role="alert"` errors, no scripts, system fonts, high-contrast colours; to be checked with real users in the beta (WP13) | Managed |
| OG-18 | **A partner for ARL 7.** The goal level needs an organization that runs or endorses the service (plan risk R9) | Owner | Owner | Engage FIRMS / Earthdata support early, alongside OG-03; public beta evidence (ARL 6) supports the approach | Open (WP14) |

## 3. Data handled

| Data | Where | Retention | Notes |
|---|---|---|---|
| User's MAP_KEY | Memory while a request runs; inside encrypted tokens held by the client; encrypted inside a pending code (5 min) | Token lifetimes (1 h access, 30 d refresh) | Never logged or returned; registered for redaction |
| Pseudonymous subject | Inside tokens | Token lifetime | Keyed hash of the key; not reversible without the server key |
| Client registrations | OAuth store | 90 days | Client metadata the client chose to send |
| Pending authorizations, codes, refresh-rotation records | OAuth store | 10 min, 5 min, refresh lifetime | |
| Logs | stderr (JSON) | Operator's choice | Levels, logger names, messages; client IDs when a key is connected; errors without key material; no tool arguments |
| FIRMS responses | Response cache | 5 min (NRT), 6 h (SP) | Public data |

FIRMS receives the user's key with each request it serves; FIRMS's own policies apply to
that. The Fire Map links carry `utm_source=firms-mcp&utm_medium=mcp` so FIRMS can see MCP
referrals; operators can turn this off.

## 4. Procedures

### 4.1 Deploying a remote endpoint

1. Choose a host (OD-02) and a public HTTPS URL; set `FIRMS_MCP_PUBLIC_URL`.
2. Generate token keys with `firms-mcp keygen`; store `FIRMS_MCP_TOKEN_KEYS` in the host's
   secret manager; use the same value on every replica.
3. With more than one replica, configure a shared OAuth store (see
   [Authentication](../design/AUTHENTICATION.md#deployment)).
4. Leave `FIRMS_MCP_ALLOW_OPERATOR_KEY` off unless the owner decides otherwise (OD-04).
5. Check `/health`, `/.well-known/oauth-protected-resource/mcp`, and
   `/.well-known/oauth-authorization-server` from outside; connect once with a test client.
6. Monitor `/health` and error-level logs.

### 4.2 Refreshing the FIRMS FAQ

1. Run `uv run python -m firms_mcp.knowledge sync` and read the change report in
   `knowledge/reports/`.
2. Review every added, changed, and retired entry against the live page; never edit FIRMS
   wording by hand.
3. Run the tests (completeness, validation), note the refresh in the changelog, and commit
   on a `docs/` or `feature/` branch.
4. Cadence: monthly, and whenever FIRMS announces changes.

### 4.3 Checking the Fire Map catalog

Run `uv run python scripts/check_map_catalog.py` monthly and after FIRMS map releases.
On drift, update the catalog snapshot, re-verify affected links in the real map, and bump
the `build_fire_map_link` tool version.

### 4.4 Rotating token keys

1. `firms-mcp keygen`; set `FIRMS_MCP_TOKEN_KEYS=<new>,<old>` and redeploy.
2. After the refresh-token lifetime (30 days by default), remove the old key and redeploy.
3. In an emergency (key exposed), set only the new key: every token becomes invalid and
   users reconnect.

### 4.5 Security incidents

- **Token key exposed:** rotate immediately with the emergency path (§4.4); review logs
  for unusual activity; inform users through the project's channels.
- **A user's MAP_KEY exposed:** the user requests a new key from FIRMS and reconnects;
  revoke their refresh tokens if known.
- **Vulnerability report:** handle per [SECURITY.md](../../SECURITY.md); fix on a `fix/`
  branch with a test; record it in the changelog.

### 4.6 Responding to FIRMS changes

When live tests fail, users report errors, or FIRMS announces a change: reproduce with a
live test, update the client or catalog, add a regression test with a recorded response
(key removed), bump affected tool versions, and record the change in the running list and
changelog.

## 5. Review cadence

| Review | When | Output |
|---|---|---|
| Operations review (§2, §4 checks) | Monthly while a deployment exists | Running-list items |
| ARL LifeCycle assessment | Each merge and phase gate | [ARL log](../arl/ARL_ASSESSMENT_LOG.md) entry |
| Fiscal Year ARL | Every August | ARL log, Fiscal Year table |
| This document | When an OD or LU item closes, or a new issue appears | Updated register |
