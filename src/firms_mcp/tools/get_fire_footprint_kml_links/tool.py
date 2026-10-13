"""get_fire_footprint_kml_links: FIRMS KML/KMZ footprint downloads (FR-DATA-011)."""

from __future__ import annotations

from firms_mcp.firms.kml import LANDSAT_REGIONS, SENSORS, kml_footprint_link
from firms_mcp.services import Services
from firms_mcp.tools.common import knowledge_refs
from firms_mcp.tools.get_fire_footprint_kml_links.models import (
    GetFireFootprintKmlLinksInput,
    GetFireFootprintKmlLinksOutput,
)

NOTES = (
    "These files are public downloads; no MAP_KEY is needed.",
    "Footprint colors show time since detection; the legend is in the knowledge entry "
    "supplement.api.kml-fire-footprints.",
)


async def get_fire_footprint_kml_links(
    params: GetFireFootprintKmlLinksInput, services: Services
) -> GetFireFootprintKmlLinksOutput:
    if params.sensors is None:
        sensors = [s for s in SENSORS if s != "landsat" or params.region in LANDSAT_REGIONS]
    else:
        sensors = list(dict.fromkeys(params.sensors))
    try:
        links = [
            kml_footprint_link(params.region, params.period, sensor, services.firms.base)
            for sensor in sensors
        ]
    except ValueError as exc:
        return GetFireFootprintKmlLinksOutput.invalid(str(exc))
    return GetFireFootprintKmlLinksOutput(
        status="success",
        links=links,
        notes=list(NOTES),
        knowledge_entries=knowledge_refs(
            services.knowledge, ["supplement.api.kml-fire-footprints"]
        ),
    )
