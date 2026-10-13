"""list_knowledge_topics: table of contents of the knowledge base (FR-KB-007)."""

from __future__ import annotations

from firms_mcp.services import Services
from firms_mcp.tools.common import section_ids
from firms_mcp.tools.list_knowledge_topics.models import (
    KnowledgeSourceInfo,
    ListKnowledgeTopicsInput,
    ListKnowledgeTopicsOutput,
    TopicEntry,
    TopicSection,
)


async def list_knowledge_topics(
    params: ListKnowledgeTopicsInput, services: Services
) -> ListKnowledgeTopicsOutput:
    knowledge = services.knowledge
    if params.section is not None and params.section not in section_ids(knowledge):
        return ListKnowledgeTopicsOutput.invalid(
            f"Unknown section {params.section!r}. Valid sections: "
            f"{', '.join(section_ids(knowledge))}."
        )
    sections = []
    total = 0
    for section in knowledge.sections(include_retired=params.include_retired):
        if params.section is not None and section.id != params.section:
            continue
        total += len(section.entry_ids)
        entries = None
        if params.section is not None or params.include_entries:
            entries = []
            for entry_id in section.entry_ids:
                entry = knowledge.get(entry_id)
                assert entry is not None
                entries.append(
                    TopicEntry(id=entry.id, title=entry.title, kind=entry.kind, status=entry.status)
                )
        sections.append(
            TopicSection(
                id=section.id,
                title=section.title,
                entry_count=len(section.entry_ids),
                entries=entries,
            )
        )
    return ListKnowledgeTopicsOutput(
        status="success",
        total_entries=total,
        sections=sections,
        sources=[
            KnowledgeSourceInfo(
                id=source.id,
                title=source.title,
                publisher=source.publisher,
                url=source.url,
                retrieved=source.retrieved.isoformat(),
            )
            for source in knowledge.sources.values()
        ],
    )
