"""get_knowledge_entry: knowledge entries by ID, verbatim (FR-KB-006, FR-KB-009)."""

from __future__ import annotations

from firms_mcp.services import Services
from firms_mcp.tools.common import entry_result
from firms_mcp.tools.get_knowledge_entry.models import (
    EntryNotFound,
    GetKnowledgeEntryInput,
    GetKnowledgeEntryOutput,
)


async def get_knowledge_entry(
    params: GetKnowledgeEntryInput, services: Services
) -> GetKnowledgeEntryOutput:
    knowledge = services.knowledge
    entries, missing = [], []
    for entry_id in dict.fromkeys(i.strip() for i in params.entry_ids):
        entry = knowledge.get(entry_id)
        if entry is None:
            missing.append(EntryNotFound(id=entry_id, suggestions=knowledge.suggestions(entry_id)))
        else:
            entries.append(entry_result(entry))
    return GetKnowledgeEntryOutput(
        status="success" if entries else "no_results",
        entries=entries,
        not_found=missing,
    )
