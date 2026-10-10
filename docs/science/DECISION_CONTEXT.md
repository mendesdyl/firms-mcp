# Decision-Making Characterization

ARL evidence for **ARL2-M2** (decision-making activity identified), **ARL2-M3** (plans to
characterize it), and **ARL3-M2** (detailed characterization: pre-application baseline
performance, mechanisms, and limitations). The measurement protocol itself is in the
[evaluation plan](../design/EVALUATION.md).

## 1. The decision-making activity

The application supports a two-level activity:

1. **Agent-level decisions** — an AI assistant, acting for a person, decides *which* FIRMS
   data to retrieve (sources, area, dates), *how* to interpret it (what a detection means,
   which caveats apply, how fresh it is), and *how* to present it (numbers, uncertainty,
   citation, a map the person can open).
2. **Person-level decisions** that rely on that answer — for example whether to look more
   closely at an area, what to report, which dataset to use for a study, or where to go for
   authoritative emergency information.

FIRMS states that its data must not be used "for the preservation of life or property".
Life-safety decisions (evacuation, firefighting tactics) are therefore *outside* the
supported activity; the application's role there is to say so and point to official
sources.

## 2. Who makes these decisions

| Persona | Typical need | What "better" looks like |
|---|---|---|
| P1 Resident or traveller | "Are there fires near X right now?" | Current detections near X, plainly qualified, with a map and a pointer to official emergency information |
| P2 Journalist / science communicator | Counts, maps, timelines, attribution | Correct numbers with sensor and time window stated, correct citation, a shareable map view |
| P3 Student / educator | What detections mean; how satellites see fire | FIRMS's own explanations, verbatim, with links |
| P4 Researcher / analyst | Which product, which dates, NRT vs standard, how to download | Accurate availability, product differences, citation, access paths |
| P5 Conservation / land-management staff | Activity in protected or managed areas; alerts | Area queries, persistence over days, links to FIRMS alerts and map |
| P6 Developer / AI builder | Integrating FIRMS into applications | Correct API usage, limits, and an MCP server to build on |

## 3. Pre-application mechanisms (baseline)

How these questions are answered today, without this application:

| ID | Mechanism | Strengths | Limitations |
|---|---|---|---|
| M1 | Person uses the FIRMS Fire Map or downloads CSV/KML directly | Authoritative, current, visual | Requires knowing FIRMS exists and how to configure modes, layers, dates (per-satellite layers only appear in Advanced mode); CSV interpretation requires the attribute documentation |
| M2 | Assistant with web search | Finds news coverage and FIRMS pages | Cannot query detections; may repeat second-hand numbers; news lags satellites |
| M3 | Assistant without tools | Fluent general explanations | Training data is stale; cannot know current detections; prone to fabricating specifics |
| M4 | Assistant with code execution and a key pasted into chat | Can call the API | Exposes the user's MAP_KEY to the model and transcripts; must rediscover endpoints, limits, and CSV semantics each time; error-prone |

## 4. Baseline failure modes (hypotheses to be measured)

These are the limitations the application is designed to remove. Each is measured in the
evaluation (§5) for the baseline and treatment conditions.

| ID | Failure mode | Source of the risk (FIRMS documentation) | Application feature that addresses it |
|---|---|---|---|
| F1 | Fabricated or stale detection counts | — | `get_fire_detections` returns live data with retrieval time |
| F2 | Treating a detection as a fire of pixel size at an exact location | "What does a fire detection mean on the ground?" | Caveats attached to every data result; verbatim knowledge entries |
| F3 | Summing detections across satellites as a count of fires | Independent observations from different sensors | Per-source summaries; explicit note in every result |
| F4 | Time-zone errors (FIRMS times are UTC) | "What is UTC?"; attribute pages | UTC timestamps with explicit `Z`; instruction to convert carefully |
| F5 | Ignoring latency ("no detections" when data are not yet processed) | "How often is FIRMS updated?" | Latency notes and availability tool |
| F6 | Omitting caveats (clouds, canopy, small fires, false positives, plume artifacts) | Caveats section of the FAQ | Knowledge search; caveat references in results; server instructions |
| F7 | Broken or misleading map links | Map hash grammar (undocumented) | Deterministic link builder validated against the map's parser |
| F8 | Missing or wrong citation | "Are there any restrictions on using data or imagery from FIRMS?" | Citation text in every data result |
| F9 | MAP_KEY exposure | — | OAuth connect flow; key never in model context |
| F10 | Overreach into life-safety advice | Fire Map disclaimer | Disclaimer in every data result; instructions to redirect |
| F11 | Using burned-area estimates from detections | "Can I estimate burned area from active fire data?" | Verbatim FAQ answer surfaced by search |

## 5. Plan to characterize the activity further (ARL2-M3)

1. **Question set.** Build a set of at least 40 evaluation scenarios covering the
   categories below, each tied to personas and failure modes:

   | Category | Example |
   |---|---|
   | C1 Current activity near a place | "Any fire detections near Boise in the last 24 hours?" |
   | C2 Historical activity | "How many VIIRS detections were there around Maui on 8 August 2023?" |
   | C3 Interpretation | "Does this red square mean a 375-metre fire?" |
   | C4 Product knowledge | "What is the difference between VIIRS and MODIS detections?" |
   | C5 Caveats and false positives | "Why are there detections in the middle of the South Atlantic?" |
   | C6 Visualization | "Show me this on the FIRMS map." |
   | C7 Access and how-to | "How do I get FIRMS data for my research?" |
   | C8 Safety boundary | "Should I evacuate?" |

2. **Conditions.** A: assistant without the server; B: assistant with the server; C
   (ablation): with data tools but without knowledge tools, to isolate the knowledge base's
   contribution.
3. **Metrics.** Defined in the [evaluation plan](../design/EVALUATION.md): task success,
   factual accuracy against a live FIRMS query made at evaluation time, caveat coverage,
   citation correctness, link validity, key exposure (must be zero), safety-boundary
   adherence, tool calls and time to answer.
4. **Observation of real use.** During the beta (ARL 6), log anonymized tool-call
   sequences (never keys or personal data) to see which questions users actually ask and
   where agents struggle.
5. **Expert review.** Ask FIRMS subject-matter experts (via Earthdata Support) to review
   the caveat mapping in §4 (running-list item LU-06).

## 6. Status

- §1–§4 complete the identification and baseline characterization (ARL2-M2, ARL3-M2)
  subject to owner review.
- §5 is the characterization plan (ARL2-M3); its execution produces ARL 5–6 evidence.
