"""get_data_availability: date coverage per FIRMS source (FR-DATA-008).

With a MAP_KEY the documented ``data_availability`` API is used; without one, the public
date service the FIRMS Fire Map itself uses (``/api/map_dates/``), re-keyed to API source IDs.
"""

from __future__ import annotations

from firms_mcp.firms.client import sources_for_map_dates
from firms_mcp.firms.sources import AVAILABILITY_SENSORS
from firms_mcp.redaction import PLACEHOLDER
from firms_mcp.services import Services
from firms_mcp.tools.common import knowledge_refs
from firms_mcp.tools.get_data_availability.models import (
    AvailabilityRow,
    GetDataAvailabilityInput,
    GetDataAvailabilityOutput,
)

KNOWLEDGE = [
    "supplement.api.data-availability",
    "faq.getting-started.for-what-dates-are-the-fire-data-available",
    "faq.getting-started.how-often-is-firms-updated",
    "faq.getting-started.what-are-the-key-differences-between-urt-rt-nrt-and-standard",
]
MAP_DATES_NOTE = (
    "No MAP_KEY is connected, so these dates come from the public date service the FIRMS "
    "Fire Map uses (not a documented API). With a MAP_KEY this tool uses FIRMS's documented "
    "data_availability API."
)
UTC_NOTE = "Dates are UTC days."


async def get_data_availability(
    params: GetDataAvailabilityInput, services: Services
) -> GetDataAvailabilityOutput:
    source = params.source.strip().upper()
    if source not in AVAILABILITY_SENSORS:
        return GetDataAvailabilityOutput.invalid(
            f"Unknown source {params.source!r}. Valid values: {', '.join(AVAILABILITY_SENSORS)}."
        )
    refs = knowledge_refs(services.knowledge, KNOWLEDGE)
    map_key = services.credentials.resolve()
    base = services.firms.base
    if map_key is not None:
        records = await services.firms.data_availability(map_key, source)
        rows = [
            AvailabilityRow(
                source=r.data_id, min_date=r.min_date, max_date=r.max_date, extra=r.extra
            )
            for r in records
        ]
        return GetDataAvailabilityOutput(
            status="success" if rows else "no_results",
            method="firms_api",
            availability=rows,
            request_url=f"{base}/api/data_availability/csv/{PLACEHOLDER}/{source}",
            retrieved_utc=services.now(),
            notes=[UTC_NOTE],
            knowledge_entries=refs,
        )
    dates = sources_for_map_dates(await services.firms.map_dates())
    rows = [
        AvailabilityRow(
            source=source_id,
            min_date=window.start.isoformat(),
            max_date=window.end.isoformat(),
        )
        for source_id, window in sorted(dates.items())
        if source == "ALL" or source_id == source
    ]
    return GetDataAvailabilityOutput(
        status="success" if rows else "no_results",
        method="fire_map_date_service",
        availability=rows,
        request_url=f"{base}/api/map_dates/",
        retrieved_utc=services.now(),
        notes=[MAP_DATES_NOTE, UTC_NOTE],
        knowledge_entries=refs,
    )
