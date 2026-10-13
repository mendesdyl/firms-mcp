"""Input and output models for get_fire_footprint_kml_links."""

from __future__ import annotations

from pydantic import Field

from firms_mcp.firms.kml import KmlLink, Period, Region, Sensor
from firms_mcp.tools.common import InputModel, KnowledgeRef, ToolOutput


class GetFireFootprintKmlLinksInput(InputModel):
    region: Region = Field(description="FIRMS KML region")
    period: Period = Field(default="24h", description="24h, 48h, 72h, or 7d")
    sensors: list[Sensor] | None = Field(
        default=None,
        description="KML sensors; default every sensor offered for the region (Landsat: Canada and USA only)",
    )


class GetFireFootprintKmlLinksOutput(ToolOutput):
    links: list[KmlLink] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    knowledge_entries: list[KnowledgeRef] = Field(default_factory=list)
