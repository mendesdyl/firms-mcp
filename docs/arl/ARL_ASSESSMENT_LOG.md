# ARL Assessment Log

This log applies the NASA Application Readiness Level metric
([reference](ARL_METRIC_REFERENCE.md)) to the FIRMS MCP project. It is **append-only**:
assessments are never edited after they are recorded; corrections are made by adding a
new entry.

**Determination rule (from the NASA document):** *"a project's ARL is determined at any
given time by the highest level for which all milestones preceding it have been completed
in full."* The milestone board below is the single source of truth for that computation.

## Milestone board

Status key: ✅ complete in full (with evidence) · 🟡 in progress · ⬜ not started.
"Commit" is the commit in which the evidence was completed.

| Milestone | Status | Evidence | Completed | Commit |
|---|---|---|---|---|
| ARL1-M1 Ideas for how research results could enhance decision making | 🟡 | [Plan §1, §3, §7](../plan/PROJECT_PLAN.md) | | |
| ARL1-M2 Baseline support research identified and documented | 🟡 | [Data products](../science/DATA_PRODUCTS.md), [References](../research/REFERENCES.md) | | |
| ARL2-M1 Independent application components formulated and created | ⬜ | | | |
| ARL2-M2 Decision making activity identified | ⬜ | | | |
| ARL2-M3 Plans to better characterize the decision making activity | ⬜ | | | |
| ARL3-M1 Components tested and validated independently | ⬜ | | | |
| ARL3-M2 Detailed characterization of user decision making process | ⬜ | | | |
| ARL3-M3 Convincing case for viability | ⬜ | | | |
| ARL4-M1 Components integrated; technical integration issues worked out | ⬜ | | | |
| ARL4-M2 Organizational and human process issues identified and managed | ⬜ | | | |
| ARL5-M1 Functioning prototype with realistic supporting elements | ⬜ | | | |
| ARL5-M2 Potential to improve decision making articulated | ⬜ | | | |
| ARL6-M1 Beta-tested in simulated operational environment | ⬜ | | | |
| ARL6-M2 Projected improvements demonstrated | ⬜ | | | |
| ARL7-M1 Integrated into end-user's operational environment | ⬜ | | | |
| ARL7-M2 Functionality tested & demonstrated in decision making | ⬜ | | | |
| ARL8-M1 Finalized system tested and proven operational | ⬜ | | | |
| ARL8-M2 Qualified and approved by user | ⬜ | | | |
| ARL8-M3 User documentation and training completed | ⬜ | | | |
| ARL9-M1 Sustained use in decision making context | ⬜ | | | |

**Computed current ARL:** 0 (no level has all milestones complete). Updated with each
LifeCycle entry below.

---

## Start-of-Project ARL

**Date:** 2026-10-09 · **Assessed by:** implementing agent, for owner approval · **ARL: 1**

Rationale:

- The research base this application depends on is mature and published: the MODIS and
  VIIRS active fire algorithms and their validation (Giglio et al. 2003; Schroeder et al.
  2014, 2016; Csiszar et al. 2006, 2014; Hall et al. 2019), the FIRMS distribution system,
  the FIRMS API, and the FIRMS FAQ. The ARL 1 milestones explicitly count baseline research
  "whether done by the PI's Team or not".
- The application idea — giving AI agents FIRMS data, FIRMS's own documentation, and map
  links through MCP — was articulated by the owner at project start.
- No application component existed, and the decision-making activity had not been
  characterized, so ARL 2 had not been reached.

The ARL 1 milestones are marked 🟡 rather than ✅ because the *documentation* the
milestones require is produced by work packages WP0 and WP1. They are closed in the first
LifeCycle entry that cites the committed evidence.

## Goal ARL

**Goal (End-of-Project) ARL: 7** — *Application Prototype in Partner's Decision Making
(Functionality Demonstrated).*

Rationale and conditions:

1. ARL 1–5 are within the project team's control: they require documentation, working
   software, tests, live validation with a real FIRMS `MAP_KEY`, and an evaluation design.
2. ARL 6 requires external beta testers using the server through real chatbot clients.
3. ARL 7 requires a **partner** — an organization whose operational environment the
   prototype is integrated into (for example a NASA FIRMS / Earthdata channel, or an
   organization operating a public assistant). Risk R9 in the plan covers the case where
   no partner is secured; the fallback End-of-Project ARL would then be 6.
4. ARL 8–9 require partner qualification and sustained operational use. They are planned
   as sustainment beyond this project and are not claimed as goals.

## LifeCycle ARL assessments

*(Append new entries at the bottom. Each entry lists the milestones newly completed, the
evidence, and the computed ARL.)*

### L-0 — 2026-10-09 — Project initialization

- Repository created; plan, ARL reference, and decision-record process committed.
- Milestones newly complete: none yet (ARL 1 evidence in progress).
- Computed ARL: 0 by the strict rule; Start-of-Project ARL recorded as 1 above on the
  basis of external baseline research, pending documentation.

## Fiscal Year ARL

| Fiscal year | Date assessed | ARL | Notes |
|---|---|---|---|
| FY2027 | due August 2027 | — | — |

## End-of-Project ARL

Not yet assessed.
