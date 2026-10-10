# ADR-0001: Record architecture decisions

- **Status:** Accepted
- **Date:** 2026-10-09
- **ARL linkage:** supports the documentation requirements of every milestone, in
  particular ARL1-M2, ARL2-M1, ARL4-M1.

## Context

The owner asked to be able to "read through the various decisions" and for documentation
suitable for the owner, the implementing agent, and other people. The project also
follows the NASA ARL metric, which asks for evidence that milestones were met. Decisions
spread across commit messages and chat transcripts cannot serve either purpose.

## Decision

Record every significant decision as a numbered Architecture Decision Record in
`docs/decisions/`, using a fixed structure: Status, Date, ARL linkage, Context, Decision,
Alternatives considered, Consequences, References. Records are immutable once accepted;
reversals are new records marked as superseding the old one. The index in
`docs/decisions/README.md` is updated in the same commit.

"Significant" means a choice that constrains future work, affects users or the handling
of scientific content, or would be hard to reverse.

## Alternatives considered

- **Decisions only in the project plan.** Rejected: the plan would grow without bound and
  lose the "why" behind each choice.
- **Decisions only in commit messages.** Rejected: not discoverable by non-developers.

## Consequences

- Each feature branch includes or updates the ADR it implements.
- Reviewers can audit decisions without reading code.

## References

- M. Nygard, "Documenting Architecture Decisions" (2011).
