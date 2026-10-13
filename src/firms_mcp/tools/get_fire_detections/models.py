"""Input and output models for get_fire_detections (ADR-0007)."""

from __future__ import annotations

import datetime as dt
from typing import Any, Literal

from pydantic import BaseModel, Field

from firms_mcp.firms.detections import Detection, SourceSummary
from firms_mcp.maplinks import FireMapLink
from firms_mcp.tools.common import AreaBox, InputModel, KnowledgeRef, ToolOutput, VerbatimText

RECORD_FIELDS = tuple(Detection.model_fields)
MANDATORY_FIELDS = ("source", "latitude", "longitude", "acquired_utc")
MAX_LIMIT = 500


class GetFireDetectionsInput(InputModel):
    area: AreaBox | Literal["world"] = Field(
        description=(
            "Where to look: a box {west, south, east, north} in decimal degrees "
            "(longitudes first; west < east, south < north; split boxes that cross the "
            "antimeridian), or 'world'"
        )
    )
    day_range: int = Field(
        default=1,
        ge=1,
        le=5,
        description="Number of UTC days, 1-5 (FIRMS limit)",
    )
    date: dt.date | None = Field(
        default=None,
        description=(
            "First UTC day (YYYY-MM-DD); returns that day and the following day_range-1 days. "
            "Omit for the most recent days (today back to today-(day_range-1), UTC)."
        ),
    )
    sources: list[str] | None = Field(
        default=None,
        min_length=1,
        max_length=8,
        description=(
            "FIRMS source IDs (see get_fire_data_sources). Default: VIIRS_NOAA20_NRT, "
            "VIIRS_NOAA21_NRT, VIIRS_SNPP_NRT, MODIS_NRT"
        ),
    )
    min_confidence: Literal["nominal", "high"] | None = Field(
        default=None,
        description=(
            "Optional filter on FIRMS's confidence class; never applied unless you ask. "
            "Landsat 'medium' counts as nominal. Removed counts are reported."
        ),
    )
    sort: Literal["newest", "oldest", "frp"] = Field(
        default="newest", description="Record order: newest first, oldest first, or highest FRP"
    )
    limit: int = Field(
        default=50,
        ge=0,
        le=MAX_LIMIT,
        description="Records per page (0-500). 0 returns summaries only.",
    )
    cursor: str | None = Field(
        default=None,
        description=(
            "next_cursor from a previous call, unchanged. The cursor fixes the query; other "
            "query arguments are ignored when it is given."
        ),
    )
    fields: list[str] | None = Field(
        default=None,
        description=(
            "Record fields to return (source, latitude, longitude, and acquired_utc are "
            "always included), e.g. ['frp_mw', 'confidence_class', 'daynight']"
        ),
    )


class DateWindow(BaseModel):
    start: dt.date
    end: dt.date


class QueryEcho(BaseModel):
    area: AreaBox | Literal["world"]
    day_range: int
    date: dt.date | None = None
    window_utc: DateWindow = Field(description="UTC days covered by the request")
    sources: list[str]
    min_confidence: str | None = None
    sort: str


class ConfidenceFilter(BaseModel):
    min_confidence: str
    kept: int
    removed: int = Field(description="Detections below the requested class")
    removed_unclassified: int = Field(
        description="Detections without a recognized confidence class"
    )


class SourceResult(BaseModel):
    source: str
    label: str
    status: Literal["success", "no_results", "error"]
    summary: SourceSummary | None = Field(
        default=None, description="All detections from this source (before any confidence filter)"
    )
    confidence_filter: ConfidenceFilter | None = None
    request_url: str | None = Field(default=None, description="FIRMS request, MAP_KEY redacted")
    retrieved_utc: dt.datetime | None = None
    from_cache: bool | None = None
    estimated_transactions: int | None = None
    processing_note: str
    error_code: str | None = None
    error_message: str | None = None


class GetFireDetectionsOutput(ToolOutput):
    query: QueryEcho | None = None
    by_source: list[SourceResult] = Field(default_factory=list)
    total_records: int | None = Field(
        default=None, description="Detections across all sources after any confidence filter"
    )
    returned: int | None = None
    next_cursor: str | None = Field(
        default=None, description="Pass back as cursor for the next page; absent on the last page"
    )
    records: list[dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Detections (pixel centers), as delivered by FIRMS with typed fields; fields that "
            "do not apply are omitted"
        ),
    )
    notes: list[str] = Field(default_factory=list)
    caveats: list[KnowledgeRef] = Field(
        default_factory=list,
        description="FIRMS documentation that applies; read with get_knowledge_entry",
    )
    disclaimer: VerbatimText | None = Field(
        default=None, description="The FIRMS Fire Map disclaimer, verbatim"
    )
    citation: VerbatimText | None = Field(
        default=None, description="How FIRMS asks to be credited and cited, verbatim"
    )
    map_link: FireMapLink | None = Field(
        default=None, description="FIRMS Fire Map view of the same area, dates, and sources"
    )
