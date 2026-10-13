"""Input and output models for get_knowledge_entry."""

from __future__ import annotations

from pydantic import BaseModel, Field

from firms_mcp.tools.common import InputModel, KnowledgeEntryResult, ToolOutput


class GetKnowledgeEntryInput(InputModel):
    entry_ids: list[str] = Field(
        min_length=1,
        max_length=10,
        description="Entry IDs, e.g. from search results, `related`, caveats, or list_knowledge_topics",
    )


class EntryNotFound(BaseModel):
    id: str
    suggestions: list[str] = Field(default_factory=list, description="Closest existing IDs")


class GetKnowledgeEntryOutput(ToolOutput):
    entries: list[KnowledgeEntryResult] = Field(default_factory=list)
    not_found: list[EntryNotFound] = Field(default_factory=list)
