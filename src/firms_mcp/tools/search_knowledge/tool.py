"""search_knowledge: deterministic search over the verbatim FIRMS knowledge base (FR-KB-005)."""

from __future__ import annotations

from firms_mcp.services import Services
from firms_mcp.tools.common import entry_result, section_ids
from firms_mcp.tools.search_knowledge.models import (
    SearchHitResult,
    SearchKnowledgeInput,
    SearchKnowledgeOutput,
)


async def search_knowledge(
    params: SearchKnowledgeInput, services: Services
) -> SearchKnowledgeOutput:
    knowledge = services.knowledge
    sections = section_ids(knowledge)
    if params.section is not None and params.section not in sections:
        return SearchKnowledgeOutput.invalid(
            f"Unknown section {params.section!r}. Valid sections: {', '.join(sections)}."
        )
    hits = knowledge.search(
        params.query,
        limit=params.limit,
        section=params.section,
        include_retired=params.include_retired,
    )
    if not hits:
        return SearchKnowledgeOutput(
            status="no_results",
            query=params.query,
            total=0,
            suggestion=(
                "No entry matched. Try FIRMS's own terms (for example 'detection confidence', "
                "'latency', 'false detections') or browse list_knowledge_topics."
            ),
        )
    return SearchKnowledgeOutput(
        status="success",
        query=params.query,
        total=len(hits),
        results=[
            SearchHitResult(
                **entry_result(hit.entry).model_dump(), score=hit.score, snippet=hit.snippet
            )
            for hit in hits
        ],
    )
