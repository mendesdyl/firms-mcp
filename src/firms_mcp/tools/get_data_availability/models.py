"""Input and output models for get_data_availability."""

from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel, Field

from firms_mcp.tools.common import InputModel, KnowledgeRef, ToolOutput


class GetDataAvailabilityInput(InputModel):
    source: str = Field(
        default="ALL", description="A FIRMS source ID (see get_fire_data_sources), or ALL"
    )


class AvailabilityRow(BaseModel):
    source: str = Field(description="FIRMS source or product identifier, as FIRMS reports it")
    min_date: str | None = Field(default=None, description="First UTC day with data")
    max_date: str | None = Field(default=None, description="Last UTC day with data")
    extra: dict[str, str] = Field(default_factory=dict, description="Other columns FIRMS returned")


class GetDataAvailabilityOutput(ToolOutput):
    method: Literal["firms_api", "fire_map_date_service"] | None = Field(
        default=None,
        description=(
            "firms_api: FIRMS's documented data_availability API (needs a MAP_KEY); "
            "fire_map_date_service: the public date service the FIRMS Fire Map uses"
        ),
    )
    availability: list[AvailabilityRow] = Field(default_factory=list)
    request_url: str | None = Field(default=None, description="FIRMS request, MAP_KEY redacted")
    retrieved_utc: dt.datetime | None = None
    notes: list[str] = Field(default_factory=list)
    knowledge_entries: list[KnowledgeRef] = Field(default_factory=list)
