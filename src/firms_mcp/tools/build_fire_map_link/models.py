"""Input and output models for build_fire_map_link."""

from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import Field

from firms_mcp.maplinks import FireMapLink
from firms_mcp.tools.common import AreaBox, InputModel, ToolOutput

Basemap = Literal["earth", "firefly", "street", "light_gray", "dark_gray", "topo_shade", "topo"]


class MapCenter(InputModel):
    longitude: float = Field(ge=-180, le=180)
    latitude: float = Field(ge=-90, le=90)


class BuildFireMapLinkInput(InputModel):
    area: AreaBox | None = Field(
        default=None,
        description="Box {west, south, east, north} to fit and outline on the map (longitudes first)",
    )
    center: MapCenter | None = Field(
        default=None, description="Map center instead of an area; use with zoom"
    )
    zoom: float | None = Field(
        default=None,
        ge=1,
        le=16,
        description="Zoom with a center (global map 1-16, US/Canada map 4-16; default 8)",
    )
    period: Literal["today", "24hrs", "48hrs", "72hrs", "7days"] | None = Field(
        default=None,
        description="Relative period (today = 00:00 UTC to now; 24hrs = 00:00 UTC yesterday to now). Default 24hrs.",
    )
    start_date: dt.date | None = Field(
        default=None, description="First UTC day, instead of a period"
    )
    end_date: dt.date | None = Field(default=None, description="Last UTC day (default: start_date)")
    sources: list[str] | None = Field(
        default=None,
        max_length=8,
        description=(
            "FIRMS source IDs to show per satellite (as in get_fire_detections); switches the "
            "map to Advanced mode. Without sources the map shows all fire detections combined."
        ),
    )
    extra_layers: list[str] | None = Field(
        default=None,
        max_length=10,
        description="Additional FIRMS Fire Map layer IDs, e.g. geostationary 'fires_goes_g18' (Advanced mode)",
    )
    basemap: Basemap = Field(default="earth", description="Basemap")
    overlays: list[str] | None = Field(
        default=None, description="Overlay layer IDs; default ['country-outline']; [] for none"
    )
    mode: Literal["basic", "advanced", "burned_area", "smoke", "experimental"] | None = Field(
        default=None, description="Fire Map mode; chosen automatically by default"
    )
    map: Literal["global", "us-canada"] = Field(
        default="global", description="Global map (/map/) or the US/Canada map (/usfs/map/)"
    )


class BuildFireMapLinkOutput(ToolOutput):
    link: FireMapLink | None = None
    notes: list[str] = Field(default_factory=list)
