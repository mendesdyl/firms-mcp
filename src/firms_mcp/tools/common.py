"""Models and helpers shared by the tools (ADR-0002, ADR-0007).

Every tool output carries ``status`` (``success`` | ``no_results`` | ``error``); errors add
a stable ``error_code``, an ``error_message``, and a ``remediation`` sentence for the agent
(Earthdata MCP convention). Fields that do not apply to a result are omitted.
"""

from __future__ import annotations

import base64
import hashlib
import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from firms_mcp.firms.errors import FirmsError
from firms_mcp.firms.geo import BoundingBox
from firms_mcp.knowledge import KnowledgeBase, KnowledgeEntry

ToolStatus = Literal["success", "no_results", "error"]

DISCLAIMER_ENTRY = "supplement.disclaimers.fire-map-disclaimer"
CITATION_ENTRY = (
    "faq.getting-started.are-there-any-restrictions-on-using-data-or-imagery-from-firms"
)


class InputModel(BaseModel):
    """Base for tool inputs: unknown arguments are rejected (ADR-0002)."""

    model_config = ConfigDict(extra="forbid")


class ToolOutput(BaseModel):
    status: ToolStatus
    error_code: str | None = Field(
        default=None, description="Stable error code when status is error"
    )
    error_message: str | None = None
    remediation: str | None = Field(
        default=None, description="What to do about the error, written for the agent"
    )
    retryable: bool | None = None
    retry_after_seconds: float | None = None

    @classmethod
    def from_error(cls, error: FirmsError, **fields: Any):
        return cls(status="error", **error.as_dict(), **fields)

    @classmethod
    def invalid(cls, message: str, **fields: Any):
        return cls(
            status="error",
            error_code="invalid_request",
            error_message=message,
            remediation="Correct the parameters described in the message and try again.",
            retryable=False,
            **fields,
        )


class KnowledgeRef(BaseModel):
    """A pointer to a knowledge-base entry; read it with get_knowledge_entry."""

    id: str
    title: str
    source_url: str


class VerbatimText(BaseModel):
    """FIRMS text reproduced verbatim from a knowledge-base entry, with its source."""

    text: str = Field(description="Verbatim FIRMS text (Markdown)")
    knowledge_entry: str
    source_url: str
    retrieved: str


def knowledge_ref(entry: KnowledgeEntry) -> KnowledgeRef:
    return KnowledgeRef(id=entry.id, title=entry.title, source_url=entry.source_url)


def knowledge_refs(knowledge: KnowledgeBase, entry_ids: list[str]) -> list[KnowledgeRef]:
    """References for the given IDs, in order, without duplicates or unknown IDs."""
    refs = []
    for entry_id in dict.fromkeys(entry_ids):
        entry = knowledge.get(entry_id)
        if entry is not None:
            refs.append(knowledge_ref(entry))
    return refs


def verbatim(knowledge: KnowledgeBase, entry_id: str) -> VerbatimText:
    entry = knowledge.get(entry_id)
    if entry is None:  # pragma: no cover - guarded by a test on the shipped knowledge base
        raise LookupError(f"knowledge entry {entry_id!r} is missing")
    return VerbatimText(
        text=entry.body,
        knowledge_entry=entry.id,
        source_url=entry.source_url,
        retrieved=entry.retrieved.isoformat(),
    )


def fire_map_disclaimer(knowledge: KnowledgeBase) -> VerbatimText:
    return verbatim(knowledge, DISCLAIMER_ENTRY)


def firms_citation(knowledge: KnowledgeBase) -> VerbatimText:
    return verbatim(knowledge, CITATION_ENTRY)


# -- pagination (Earthdata MCP convention: opaque, tool- and query-scoped cursors) --------


class InvalidCursor(ValueError):
    pass


def query_fingerprint(query: dict[str, Any]) -> str:
    canonical = json.dumps(query, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def encode_cursor(tool: str, query: dict[str, Any], offset: int, **state: Any) -> str:
    payload = {"t": tool, "q": query, "o": offset, **state}
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii").rstrip("=")


def decode_cursor(tool: str, cursor: str) -> dict[str, Any]:
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")))
    except (ValueError, UnicodeError) as exc:
        raise InvalidCursor(
            "The cursor is not valid. Pass next_cursor exactly as returned, or start a new "
            "query without a cursor."
        ) from exc
    if not isinstance(payload, dict) or payload.get("t") != tool:
        raise InvalidCursor(
            "This cursor belongs to a different tool. Cursors cannot be reused across tools; "
            "start a new query without a cursor."
        )
    if not isinstance(payload.get("q"), dict) or not isinstance(payload.get("o"), int):
        raise InvalidCursor("The cursor is malformed; start a new query without a cursor.")
    return payload


# -- knowledge entries --------------------------------------------------------------------

RETIRED_NOTICE = (
    "FIRMS no longer publishes this entry on its site; it is kept for provenance and may be "
    "out of date."
)


class KnowledgeEntryResult(BaseModel):
    """A knowledge-base entry with its full verbatim body and provenance."""

    id: str
    title: str = Field(description="The FIRMS question or heading, verbatim")
    kind: str
    section: str
    section_title: str
    status: str = Field(description="current, or retired (no longer on the FIRMS site)")
    notice: str | None = Field(default=None, description="Present for retired entries")
    body: str = Field(description="FIRMS's text, verbatim (Markdown). Quote it; do not alter it.")
    source: str
    source_url: str
    retrieved: str = Field(description="Date the text was retrieved from the source")
    content_sha256: str
    related: list[str] = Field(default_factory=list, description="Related entry IDs")


def entry_result(entry: KnowledgeEntry) -> KnowledgeEntryResult:
    return KnowledgeEntryResult(
        id=entry.id,
        title=entry.title,
        kind=entry.kind,
        section=entry.section,
        section_title=entry.section_title,
        status=entry.status,
        notice=RETIRED_NOTICE if entry.status == "retired" else None,
        body=entry.body,
        source=entry.source,
        source_url=entry.source_url,
        retrieved=entry.retrieved.isoformat(),
        content_sha256=entry.content_sha256,
        related=list(entry.related),
    )


def section_ids(knowledge: KnowledgeBase) -> list[str]:
    return [section.id for section in knowledge.sections(include_retired=True)]


# -- areas --------------------------------------------------------------------------------


class AreaBox(InputModel):
    """A west, south, east, north box in decimal degrees (longitudes first)."""

    west: float = Field(
        ge=-180, le=180, description="Western edge, longitude in degrees (-180 to 180)"
    )
    south: float = Field(
        ge=-90, le=90, description="Southern edge, latitude in degrees (-90 to 90)"
    )
    east: float = Field(
        ge=-180, le=180, description="Eastern edge, longitude in degrees; greater than west"
    )
    north: float = Field(
        ge=-90, le=90, description="Northern edge, latitude in degrees; greater than south"
    )

    @model_validator(mode="after")
    def _valid_box(self) -> AreaBox:
        self.to_bbox()  # raises ValueError with an explanation
        return self

    def to_bbox(self) -> BoundingBox:
        return BoundingBox(west=self.west, south=self.south, east=self.east, north=self.north)


def area_to_bbox(area: AreaBox | str) -> BoundingBox:
    return BoundingBox.world() if area == "world" else area.to_bbox()  # type: ignore[union-attr]
