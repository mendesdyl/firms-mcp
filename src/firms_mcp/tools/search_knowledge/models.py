"""Input and output models for search_knowledge."""

from __future__ import annotations

from pydantic import Field

from firms_mcp.tools.common import InputModel, KnowledgeEntryResult, ToolOutput


class SearchKnowledgeInput(InputModel):
    query: str = Field(
        min_length=1,
        max_length=500,
        description="What to look for, in plain words, e.g. 'why was a fire not detected'",
    )
    limit: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of entries to return (1-10). Entries are returned in full.",
    )
    section: str | None = Field(
        default=None,
        description="Only search one section, by ID from list_knowledge_topics (e.g. 'caveats')",
    )
    include_retired: bool = Field(
        default=False,
        description="Also search entries FIRMS no longer publishes (kept for provenance)",
    )


class SearchHitResult(KnowledgeEntryResult):
    score: float = Field(
        description="Relevance score (higher is better; comparable within a search)"
    )
    snippet: str = Field(description="Where the query terms appear; a navigation aid, not a quote")


class SearchKnowledgeOutput(ToolOutput):
    query: str | None = None
    total: int | None = Field(default=None, description="Number of entries returned")
    results: list[SearchHitResult] = Field(default_factory=list)
    suggestion: str | None = None
