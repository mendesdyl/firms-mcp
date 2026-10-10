# NASA Application Readiness Level (ARL) Metric — Reference

> **Source:** NASA Applied Sciences Program, *The Application Readiness Level Metric*
> (11 slides). <https://carbon.nasa.gov/docs/The%20ARL%20Metric.pdf>
> Retrieved 2026-10-09. The level names, descriptions, and milestone text below are
> transcribed **verbatim** from that document so that this project's plan and
> assessments can be checked against the original wording. Nothing here is paraphrased;
> interpretation for this project lives in [`PROJECT_PLAN.md`](../plan/PROJECT_PLAN.md)
> and [`ARL_ASSESSMENT_LOG.md`](ARL_ASSESSMENT_LOG.md).

## How the metric is used (verbatim, slide 1)

> The NASA Applied Sciences Program has instituted a nine-step Application Readiness
> Level (ARL) index to track and manage the progression and distribution of funded
> projects. This index is an adaptation of a scale used by NASA for managing technology
> development and risk (Technology Readiness Levels, TRLs), and reflects three main tiers
> of project research, development, and deployment. In general, ARLs 1-3 encompass
> discovery and feasibility; ARLs 4-6 address development, testing, and validation; and,
> ARLs 7-9 focus on integration of the "application" into an end-user's decision-making
> activity. Using this scale, project teams are being asked to assess the "maturity" of
> their Applied Sciences project on a regular basis, starting with the project proposal.
>
> At the beginning of each project, project teams are asked to assess which ARL the
> project is starting at (**Start-of-Project ARL**) and also to project what level the
> project will reach upon completion (**Goal ARL**). Throughout the duration of most
> projects, teams are expected to re-assess their project's ARL on periodic basis
> (**LifeCycle ARL**), every August for a federal "**Fiscal Year ARL**" measure, and at
> the close-out of their award (**End-of-Project ARL**). It is not expected that all
> projects will start at ARL 1 and end at ARL 9, so please carefully read through the
> milestones that need to be met to achieve each ARL, and choose appropriately. In
> addition, while some projects may complete a few milestones out of phase with this
> generalized progression from ARL 1 to ARL 9 or may have project components at different
> levels, **a project's ARL is determined at any given time by the highest level for
> which all milestones preceding it have been completed in full.**

### Assessment types required by the metric

| Assessment | When | Where this project records it |
|---|---|---|
| Start-of-Project ARL | At project start | [`ARL_ASSESSMENT_LOG.md` § Start-of-Project](ARL_ASSESSMENT_LOG.md#start-of-project-arl) |
| Goal ARL | At project start | [`ARL_ASSESSMENT_LOG.md` § Goal](ARL_ASSESSMENT_LOG.md#goal-arl) |
| LifeCycle ARL | Periodically (this project: at every phase gate and major merge) | [`ARL_ASSESSMENT_LOG.md` § LifeCycle](ARL_ASSESSMENT_LOG.md#lifecycle-arl-assessments) |
| Fiscal Year ARL | Every August | [`ARL_ASSESSMENT_LOG.md` § Fiscal Year](ARL_ASSESSMENT_LOG.md#fiscal-year-arl) |
| End-of-Project ARL | At close-out | [`ARL_ASSESSMENT_LOG.md` § End-of-Project](ARL_ASSESSMENT_LOG.md#end-of-project-arl) |

### Determination rule (operationalized)

The ARL at any time is the highest level *N* such that **every milestone of levels 1..N
is complete in full**. A completed milestone at a higher level does not raise the ARL
while any lower-level milestone is incomplete. This project enforces the rule
mechanically: the assessment log lists every milestone of every level with an evidence
link, and the computed ARL is the first level with an unchecked milestone, minus one.

## Phases (slide 2)

| Phase | Levels | Theme |
|---|---|---|
| Phase I | ARL 1–3 | Discovery & Feasibility |
| Phase II | ARL 4–6 | Development, Testing, & Validation |
| Phase III | ARL 7–9 | Integration into Partner's System |

## Levels (slide 2)

| ARL | Name |
|---|---|
| 1 | Basic Research (Baseline Ideas) |
| 2 | Application Concept (Invention) |
| 3 | Proof of Application Concept (Viability Established) |
| 4 | Initial Integration and Verification (Prototype/Plan) |
| 5 | Validation in Relevant Environment (Potential Determined) |
| 6 | Demonstration in Relevant Environment (Potential Demonstrated) |
| 7 | Application Prototype in Partner's Decision Making (Functionality Demonstrated) |
| 8 | Application Completed and Qualified (Functionality Proven) |
| 9 | Approved, Operational Deployment and Use in Decision Making (Sustained Use) |

---

### ARL 1 — Basic Research (Baseline Ideas) — slide 3

> This level is the foundation upon which application concepts are developed. At this
> level, basic scientific concepts, connections, and insights and are observed and
> reported, and research produces results that provide the **basis for applications
> ideas**.

Milestones:

- **ARL1-M1** — Ideas for how specific research results could enhance decision making developed
- **ARL1-M2** — Baseline support research identified and documented (i.e., results on the theory, models, remotely sensed products, and other current or planned measurements needed to support the application idea) – *whether done by the PI's Team or not*

### ARL 2 — Application Concept (Invention) — slide 4

> Application invention and formulation of concept begins here. Initial understanding and
> characterization of the decision making activity are articulated. At this level, the
> full **application system is still speculative** and there is no proof or detailed
> analysis to support the assumption.

Milestones:

- **ARL2-M1** — Independent application components formulated and created
- **ARL2-M2** — Decision making activity to be enhanced by the application identified
- **ARL2-M3** — Plans to better characterize the decision making activity developed

### ARL 3 — Proof of Application Concept (Viability Established) — slide 5

> Feasibility studies to assess the potential viability of and provide a proof-of-concept
> for the application are conducted. In addition, a more complete characterization of the
> decision making process is completed. Different components of the application system are
> **not yet integrated**.

Milestones:

- **ARL3-M1** — Components of application tested and validated independently
- **ARL3-M2** — Detailed characterization of user decision making process completed (e.g., pre-application baseline performance, mechanisms, and limitations)
- **ARL3-M3** — Convincing case for the viability of the application concept made

### ARL 4 — Initial Integration & Verification (Prototype/Plan) — slide 6

> Basic components of Earth science products and the decision making activity (decision
> support system, tool, etc.) are integrated together into a prototype "application
> system" to establish that they will work together. At this level, the technical,
> organizational, and human process issues related to the decision support activities are
> also worked out. Project team must **verify that components will work together** to
> achieve this ARL.

Milestones:

- **ARL4-M1** — Components of eventual application system brought together and technical integration issues worked out
- **ARL4-M2** — Organizational challenges and human process issues identified and managed

### ARL 5 — Validation in Relevant Environment (Potential Determined) — slide 7

> Basic components are integrated with reasonably realistic supporting elements so
> application can be tested in a simulated decision making environment. Prototype
> implementations conform to the end-user's target environment and standard interfaces.
> Validation that the decision making activity both functions with the Earth science
> products and is projected to improve performance is achieved. Project team must
> **articulate the potential** for performance improvement in decision making to achieve
> this ARL.

Milestones:

- **ARL5-M1** — Application components integrated into a functioning prototype application system with realistic supporting elements
- **ARL5-M2** — The application system's potential to improve the decision making activity determined and articulated (e.g., projected impacts on cost, functionality, delivery time, etc.)

### ARL 6 — Demonstration in Relevant Environment (Potential Demonstrated) — slide 8

> Achieving this level represents a major increase in the application's demonstrated
> readiness. The prototype application system is demonstrated in a relevant environment
> or in a simulated operational decision making environment. Any application component(s)
> already deployed in the end-user's environment are tested in operational decision making
> context. Project team must **demonstrate the potential** for performance improvement in
> decision making to achieve this ARL.

Milestones:

- **ARL6-M1** — Prototype application system beta-tested in a simulated operational environment
- **ARL6-M2** — Projected improvements in performance of decision making activity demonstrated in simulated operational environment

### ARL 7 — Application Prototype in Partner's Decision Making (Functionality Demonstrated) — slide 9

> Prototype application system and all pre-deployed components are fully integrated into
> the end-user's operational environment, such as the partner's decision making activity.
> At this level of application system maturity, functionality is demonstrated to win the
> confidence of the partner. Project team must **demonstrate the functionality** of the
> integrated components in the decision making activity to achieve this ARL.

Milestones:

- **ARL7-M1** — Prototype application system integrated into end-user's operational environment
- **ARL7-M2** — Prototype application functionality tested & demonstrated in decision making activity

### ARL 8 — Application Completed & Qualified (Functionality Proven) — slide 10

> Actual application system is completed and 'qualified' by the partner through testing
> and demonstration in the targeted decision making activity. The application is proven
> to work in its final form and under expected conditions. In addition, most user
> documentation, training documentation, and maintenance documentation are completed.
> **Partner must approve** the application system for use in their decision making
> activity to achieve this ARL.

Milestones:

- **ARL8-M1** — Finalized application system tested, proven operational, and shown to operate as expected within user's environment
- **ARL8-M2** — Application qualified and approved by user for use in decision making activity
- **ARL8-M3** — User documentation and training completed

### ARL 9 — Approved, Operational Deployment & Use in Decision Making (Sustained Use) — slide 11

> Actual operational, successful use of application by users in their decision making
> activities. To reach ARL 9, full integration and **repeated use** in the decision making
> organization's operations has been achieved.

Milestone:

- **ARL9-M1** — Sustained use of application system in decision making context

---

*The milestone identifiers (`ARL1-M1` …) are this project's labels for cross-referencing;
they are not part of the NASA document.*
