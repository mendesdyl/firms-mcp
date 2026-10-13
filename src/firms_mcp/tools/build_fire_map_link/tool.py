"""build_fire_map_link: deterministic FIRMS Fire Map links (FR-MAP-001 … FR-MAP-006)."""

from __future__ import annotations

from firms_mcp.maplinks import MapLinkError
from firms_mcp.maplinks import build_fire_map_link as build_link
from firms_mcp.services import Services
from firms_mcp.tools.build_fire_map_link.models import (
    BuildFireMapLinkInput,
    BuildFireMapLinkOutput,
)

NOTES = (
    "The FIRMS Fire Map renders FIRMS's own data when the link is opened; what it shows can "
    "differ from earlier tool results as new detections arrive.",
    "Times in the map's date selection are UTC.",
)


async def build_fire_map_link(
    params: BuildFireMapLinkInput, services: Services
) -> BuildFireMapLinkOutput:
    try:
        link = build_link(
            area=params.area.to_bbox() if params.area else None,
            center=(params.center.longitude, params.center.latitude) if params.center else None,
            zoom=params.zoom,
            period=params.period,
            start_date=params.start_date,
            end_date=params.end_date,
            sources=params.sources,
            extra_layers=params.extra_layers,
            basemap=params.basemap,
            overlays=params.overlays,
            mode=params.mode,
            map_name=params.map,
            referral=services.settings.referral_params,
            today=services.today(),
        )
    except MapLinkError as exc:
        return BuildFireMapLinkOutput.invalid(str(exc))
    return BuildFireMapLinkOutput(status="success", link=link, notes=list(NOTES))
