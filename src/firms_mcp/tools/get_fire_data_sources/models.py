"""Input and output models for get_fire_data_sources."""

from __future__ import annotations

from pydantic import BaseModel, Field

from firms_mcp.tools.common import InputModel, KnowledgeRef, ToolOutput


class GetFireDataSourcesInput(InputModel):
    source_ids: list[str] | None = Field(
        default=None,
        min_length=1,
        max_length=8,
        description="Only these FIRMS source IDs; all sources by default",
    )


class SourceInfo(BaseModel):
    id: str = Field(description="FIRMS area-API SOURCE value")
    label: str = Field(description="FIRMS's own display name")
    family: str
    instrument: str
    platforms: list[str]
    processing: str = Field(
        description="NRT (near real time, with RT/URT) or SP (standard processing)"
    )
    processing_note: str
    nominal_resolution_m: int = Field(description="Nominal pixel size at nadir, metres")
    coverage: str
    default: bool = Field(description="Queried by get_fire_detections when no sources are given")
    fire_map_layers: list[str] = Field(description="FIRMS Fire Map layer IDs (Advanced mode)")
    kml_sensor: str | None = Field(default=None, description="Sensor value for KML footprint links")
    record_start_per_faq: str | None = None
    knowledge_entries: list[KnowledgeRef] = Field(default_factory=list)


class GetFireDataSourcesOutput(ToolOutput):
    sources: list[SourceInfo] = Field(default_factory=list)
    default_sources: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
