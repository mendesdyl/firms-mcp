"""Data models for knowledge-base entries (ADR-0005)."""

from __future__ import annotations

import datetime as dt
import hashlib
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

EntryKind = Literal["faq", "faq-section-intro", "faq-preamble", "supplement"]
EntryStatus = Literal["current", "retired"]

ID_PATTERN = r"^[a-z0-9]+(?:[.-][a-z0-9]+)*$"


def content_hash(body: str) -> str:
    """SHA-256 of an entry body after newline and trailing-whitespace normalization."""
    normalized = "\n".join(line.rstrip() for line in body.replace("\r\n", "\n").split("\n"))
    return hashlib.sha256(normalized.strip("\n").encode("utf-8")).hexdigest()


class KnowledgeSource(BaseModel):
    """A registered origin of knowledge content (``knowledge/sources.yaml``)."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=ID_PATTERN)
    title: str
    publisher: str
    url: str
    retrieved: dt.date
    license_note: str
    notes: str | None = None


class KnowledgeEntry(BaseModel):
    """One unit of verbatim reference content with its provenance."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=ID_PATTERN, description="Stable identifier, e.g. faq.caveats.…")
    title: str = Field(min_length=1, description="Verbatim question or heading")
    kind: EntryKind
    section: str = Field(pattern=ID_PATTERN)
    section_title: str
    source: str = Field(description="ID of a source in sources.yaml")
    source_url: str
    retrieved: dt.date
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    order: int = Field(ge=0, description="Position within its source, for tables of contents")
    tags: list[str] = Field(default_factory=list)
    related: list[str] = Field(default_factory=list)
    status: EntryStatus = "current"
    body: str = Field(description="Verbatim content (Markdown)")

    @field_validator("tags", "related")
    @classmethod
    def _dedupe(cls, value: list[str]) -> list[str]:
        seen: list[str] = []
        for item in value:
            if item not in seen:
                seen.append(item)
        return seen

    def front_matter(self) -> dict:
        """Front-matter mapping in canonical key order (everything except the body)."""
        data = self.model_dump(mode="json", exclude={"body"})
        order = [
            "id",
            "title",
            "kind",
            "section",
            "section_title",
            "source",
            "source_url",
            "retrieved",
            "content_sha256",
            "order",
            "tags",
            "related",
            "status",
        ]
        return {key: data[key] for key in order}
