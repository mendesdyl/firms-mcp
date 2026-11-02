# ARL Guide — how readiness is scored in this project

A plain-language guide to the NASA **Application Readiness Level (ARL)** as this project
applies it: what each level means here, what evidence proves it, where the project stands
at the start of iteration 2, and what has to happen next. It is written for the owner's
review.

The NASA wording is transcribed verbatim in the [ARL metric reference](ARL_METRIC_REFERENCE.md);
the scores themselves are recorded only in the append-only
[ARL assessment log](ARL_ASSESSMENT_LOG.md). This guide interprets; it does not score.

## 1. What the ARL measures

NASA's Applied Sciences Program uses a nine-level scale, adapted from Technology
Readiness Levels, to track how mature an *application* is — not how good the code is, but
how far a use of Earth science data has progressed from an idea to something people rely
on in their decisions. The nine levels fall into three phases:

| Phase | Levels | In this project |
|---|---|---|
| I — Discovery & Feasibility | 1–3 | Is giving agents FIRMS's documentation and links through MCP a sound idea, and do the parts work? |
| II — Development, Testing & Validation | 4–6 | Does the whole server work, in realistic conditions, and does it help? |
| III — Integration into Partner's System | 7–9 | Does an organization (ideally NASA FIRMS) run it and rely on it? |

Here the "decision-making activity" is a person asking an AI agent about fires and
reaching their own conclusion. The application improves that activity if the agent's
answer carries FIRMS's own data paths, wording, and caveats instead of guesses — see the
[decision-making characterization](../science/DECISION_CONTEXT.md).

## 2. The rule that computes the score

> The ARL is the highest level for which **every milestone of that level and of all
> levels below it** is complete in full.

A finished milestone at a higher level does not raise the score while any lower one is
open. The log's milestone board lists all 20 milestones with evidence; the score is read
straight off it.

Two more conventions this project uses:

- A milestone whose verification is "owner review" is recorded as complete when the
  evidence is submitted, and **reverts** if the owner does not accept it.
- The log is **append-only**. A score that goes down is recorded as a new entry with the
  reason; old entries are never edited.

## 3. When the score is assessed

| Assessment | When | Status |
|---|---|---|
| Start-of-Project | At the start | ARL 1 (2026-10-09) |
| Goal | At the start | ARL 7, fallback 6 without a partner |
| LifeCycle | At every phase gate and major change | L-0 … L-8 |
| Fiscal Year | Every August | First due August 2027 |
| End-of-Project | At close-out | Not yet |

## 4. Level by level

For each level: what NASA's milestones ask for, what that means for this project, the
evidence, and its status at the start of iteration 2.

### ARL 1 — Basic Research (Baseline Ideas)

| Milestone | Means here | Evidence | Status |
|---|---|---|---|
| ARL1-M1 Ideas for how research results could enhance decision making | How FIRMS data and documentation could make an agent's answers about fires better | [Project plan §1, §3, §7](../plan/PROJECT_PLAN.md) | ✅ |
| ARL1-M2 Baseline research identified and documented | The MODIS and VIIRS active-fire algorithms, FIRMS, its API and FAQ — research done by others counts | [Data products](../science/DATA_PRODUCTS.md), [References](../research/REFERENCES.md) | ✅ |

### ARL 2 — Application Concept

| Milestone | Means here | Evidence | Status |
|---|---|---|---|
| ARL2-M1 Independent components formulated and created | Each part exists on its own: knowledge base, Fire Map link builder, source catalog and API access | Iteration 1 modules (`v0-iteration-1`) | ✅ (see §5) |
| ARL2-M2 Decision-making activity identified | Who asks agents about fires, and what they decide | [Decision context §1–§3](../science/DECISION_CONTEXT.md) | ✅ |
| ARL2-M3 Plans to characterize it better | How the evaluation will measure answers with and without the server | [Decision context §5](../science/DECISION_CONTEXT.md), [Evaluation plan](../design/EVALUATION.md) | ✅ |

### ARL 3 — Proof of Application Concept

| Milestone | Means here | Evidence | Status |
|---|---|---|---|
| ARL3-M1 Components tested and validated independently | Each part has its own tests and checks against the real thing (the FAQ text, the real map) | Iteration 1: 52 knowledge tests incl. line-by-line FAQ check; 24 map-link tests and links verified in the real map; 73 API-client tests | ✅ (see §5) |
| ARL3-M2 Detailed characterization of the decision process | Mechanisms (M1–M4) and failure modes (F1–F11) of agents answering fire questions today | [Decision context §3–§4](../science/DECISION_CONTEXT.md) | ✅ — the quantitative baseline comes from the first evaluation run |
| ARL3-M3 Convincing case for viability | Criteria fixed in advance (V1–V9), rated with evidence, and the conditions that would kill the idea (K1–K4) | [Viability case](../plan/VIABILITY_CASE.md) | ✅ — **owner review pending** |

### ARL 4 — Initial Integration & Verification

| Milestone | Means here | Evidence needed in iteration 2 | Status |
|---|---|---|---|
| ARL4-M1 Components brought together; technical integration issues worked out | The **TypeScript** server assembling the keyless components, tested end to end over stdio and Streamable HTTP, with integration issues logged and closed | TypeScript integration tests; [integration issues log](../project/INTEGRATION_ISSUES.md) continued | 🟡 |
| ARL4-M2 Organizational and human-process issues identified and managed | The issues around running the server: FIRMS's undocumented services, reviewing the weekly FAQ pull request, endorsement, support, licensing, who hosts it | [Operations and governance](../project/OPERATIONS_AND_GOVERNANCE.md), revised for the keyless scope | 🟡 — **owner review needed** |

### ARL 5 — Validation in a Relevant Environment

| Milestone | Means here | Evidence needed |
|---|---|---|
| ARL5-M1 Functioning prototype with realistic supporting elements | The server used from real agent hosts (Claude Desktop, Claude Code), with real FIRMS: the knowledge synced from the live FAQ, built URLs that actually return data when a real MAP_KEY is filled in, map links that open correctly | Live validation run; requires a MAP_KEY in your local `.env` (running list OD-05) |
| ARL5-M2 Potential to improve decision making articulated | Numbers from the evaluation: agent answers with and without the server, scored against the failure modes F1–F11 | First evaluation run (`evaluation/`) and a projected-impact write-up |

### ARL 6 — Demonstration in a Relevant Environment

| Milestone | Means here |
|---|---|
| ARL6-M1 Beta-tested in a simulated operational environment | People outside the project use their own copy, or a test deployment, in their own agent tools |
| ARL6-M2 Projected improvements demonstrated | The beta testers' sessions show the improvement measured in ARL 5 |

### ARL 7 — Prototype in the Partner's Decision Making (the Goal)

| Milestone | Means here |
|---|---|
| ARL7-M1 Integrated into the end-user's operational environment | A partner — ideally NASA FIRMS — runs the server in its own environment |
| ARL7-M2 Functionality demonstrated in decision making | The partner's users rely on it and it works as intended |

Without a partner the project cannot pass ARL 6; that is why the Goal has a fallback.

### ARL 8–9 — Qualified, then Sustained Use

The partner formally approves the system (ARL 8: tested, qualified, user documentation
and training complete) and then uses it repeatedly over time (ARL 9). These belong to
whoever operates the server after this project and are not claimed as goals.

## 5. Where the project stands: ARL 3

At the end of iteration 1 the computed score was **ARL 4**. Iteration 2 replaces the
Python code with TypeScript and narrows the scope to the keyless server
([ADR-0011](../decisions/0011-keyless-scope-typescript-rewrite-standard-data-first.md)).
The owner chose to record a LifeCycle reassessment to **ARL 3** (log entry L-8):

- **ARL 1–3 stay complete.** They are about the *concept* and a *proof of concept*. The
  components were formulated, created, and validated independently in iteration 1, and
  that evidence remains true and preserved at `v0-iteration-1`. The rewrite changes the
  implementation language, not the components' design or what their tests proved.
  Narrowing the scope removes two components (API client, authentication); it does not
  invalidate the evidence for the ones that remain.
- **ARL4-M1 reopens.** Integration has to be verified on the code that actually ships.
  The Python integration tests say nothing about the TypeScript server.
- **ARL4-M2 reopens.** The issue register was written for a server that holds keys. It
  needs revising for the keyless server — several issues disappear (OG-01 … OG-04, OG-10,
  OG-13 move to the extension design), and new ones appear (the weekly FAQ review duty,
  two more undocumented FIRMS services, the reminder about keys pasted into chat).

**A stricter reading is possible**, and a reviewer might take it: that ARL2-M1 and
ARL3-M1 also reopen until the TypeScript components exist and pass their own tests,
which would put the project at ARL 1 for the duration of the rewrite. This project does
not take that reading, for the reasons above, but the TypeScript component tests are
written so that they would satisfy it too: every component gets its own tests before
integration.

## 6. What brings it back to ARL 4

1. The TypeScript components each pass their own tests (knowledge base including the
   line-by-line FAQ check, map links, API URL builder with SP-first selection, source
   catalog, sync).
2. The server assembles them and passes integration tests over stdio and Streamable
   HTTP; integration issues are logged and closed. → **ARL4-M1**
3. Operations and governance is revised for the keyless scope and **you accept it**.
   → **ARL4-M2**
4. A LifeCycle entry records the evidence. → **computed ARL 4**

## 7. What needs your review

These are owner decisions the score depends on. Each is recorded as complete or pending
in the log; if you do not accept one, the score falls back.

| Item | What to review | Effect if not accepted |
|---|---|---|
| ARL3-M3 | The [viability case](../plan/VIABILITY_CASE.md) (submitted 2026-10-10). Its criteria still apply to the keyless scope; V3 (FIRMS limits) and V4 (credential handling) matter less now, and K1 (FIRMS objecting to key handling) no longer applies to the keyless server | Score falls to 2 |
| ARL4-M2 | The revised operations and governance document (comes with the iteration-2 work) | Score stays at 3 |
| This guide's reading in §5 | Whether ARL 1–3 stay complete through the rewrite | If not, the log records ARL 1 until the TypeScript component tests pass |
| Goal ARL | Still ARL 7 with NASA FIRMS as the hoped-for partner, fallback 6 | — |
