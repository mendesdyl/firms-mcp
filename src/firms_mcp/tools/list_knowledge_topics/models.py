"""Input and output models for list_knowledge_topics."""

from __future__ import annotations

from pydantic import BaseModel, Field

from firms_mcp.tools.common import InputModel, ToolOutput


class ListKnowledgeTopicsInput(InputModel):
    section: str | None = Field(
        default=None, description="List the entries of one section, by ID (e.g. 'caveats')"
    )
    include_entries: bool = Field(
        default=False,
        description="List every entry of every section (about 150 titles) instead of section counts",
    )
    include_retired: bool = Field(
        default=False, description="Include entries FIRMS no longer publishes"
    )


class TopicEntry(BaseModel):
    id: str
    title: str
    kind: str
    status: str


class TopicSection(BaseModel):
    id: str
    title: str
    entry_count: int
    entries: list[TopicEntry] | None = Field(
        default=None, description="Present when a section is requested or include_entries is true"
    )


class KnowledgeSourceInfo(BaseModel):
    id: str
    title: str
    publisher: str
    url: str
    retrieved: str


class ListKnowledgeTopicsOutput(ToolOutput):
    total_entries: int | None = None
    sections: list[TopicSection] = Field(default_factory=list)
    sources: list[KnowledgeSourceInfo] = Field(default_factory=list)
