"""get_fire_data_sources: the FIRMS detection source catalog (FR-DATA-010)."""

from __future__ import annotations

from firms_mcp.firms.sources import DEFAULT_SOURCES, SOURCES, get_source
from firms_mcp.services import Services
from firms_mcp.tools.common import knowledge_refs
from firms_mcp.tools.get_fire_data_sources.models import (
    GetFireDataSourcesInput,
    GetFireDataSourcesOutput,
    SourceInfo,
)

NOTES = (
    "Detections from different sources are independent observations of the same fires; do "
    "not add counts across sources to count fires.",
    "Use get_data_availability for the dates each source currently covers.",
    "Geostationary detections (GOES, Meteosat, Himawari) appear as layers in the FIRMS Fire "
    "Map but were not offered by the FIRMS area API when this catalog was compiled "
    "(2026-10-09).",
)


async def get_fire_data_sources(
    params: GetFireDataSourcesInput, services: Services
) -> GetFireDataSourcesOutput:
    try:
        chosen = [get_source(s) for s in dict.fromkeys(params.source_ids or SOURCES)]
    except ValueError as exc:
        return GetFireDataSourcesOutput.invalid(str(exc))
    return GetFireDataSourcesOutput(
        status="success",
        sources=[
            SourceInfo(
                id=source.id,
                label=source.label,
                family=source.family,
                instrument=source.instrument,
                platforms=list(source.platforms),
                processing=source.processing,
                processing_note=source.processing_note,
                nominal_resolution_m=source.nominal_resolution_m,
                coverage=source.coverage,
                default=source.id in DEFAULT_SOURCES,
                fire_map_layers=list(source.map_layers),
                kml_sensor=source.kml_sensor,
                record_start_per_faq=source.record_start_per_faq,
                knowledge_entries=knowledge_refs(
                    services.knowledge, list(source.knowledge_entries)
                ),
            )
            for source in chosen
        ],
        default_sources=list(DEFAULT_SOURCES),
        notes=list(NOTES),
    )
