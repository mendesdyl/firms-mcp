"""get_fire_detections: FIRMS detections for an area and UTC days (ADR-0007).

Returns per-source summaries, a page of records, the FIRMS documentation that applies,
the Fire Map disclaimer and FIRMS citation verbatim, a Fire Map link reproducing the
query, and provenance with the MAP_KEY redacted (FR-DATA-001, FR-DATA-005, FR-DATA-006,
FR-DATA-014, NFR-004). The server does not group detections into fires or interpret them.
"""

from __future__ import annotations

import asyncio
import datetime as dt
from typing import Any

from pydantic import ValidationError

from firms_mcp.firms.client import DetectionsResult
from firms_mcp.firms.detections import Detection, summarize
from firms_mcp.firms.errors import (
    AuthRequired,
    FirmsError,
    InvalidMapKey,
    MapKeyRejected,
    RateLimited,
)
from firms_mcp.firms.sources import DEFAULT_SOURCES, FireSource, get_source
from firms_mcp.maplinks import MapLinkError, build_fire_map_link
from firms_mcp.services import Services
from firms_mcp.tools.common import (
    InvalidCursor,
    area_to_bbox,
    decode_cursor,
    encode_cursor,
    fire_map_disclaimer,
    firms_citation,
    knowledge_refs,
)
from firms_mcp.tools.get_fire_detections.models import (
    MANDATORY_FIELDS,
    RECORD_FIELDS,
    ConfidenceFilter,
    DateWindow,
    GetFireDetectionsInput,
    GetFireDetectionsOutput,
    QueryEcho,
    SourceResult,
)

TOOL = "get_fire_detections"

GENERAL_CAVEATS = (
    "faq.getting-started.what-does-a-fire-detection-mean-on-the-ground",
    "faq.caveats.are-all-active-fire-hotspots-vegetation-fires",
    "faq.caveats.are-there-ever-false-fire-detections-or-data-artifacts",
    "faq.getting-started.why-was-a-particular-fire-not-detected",
    "faq.getting-started.what-is-the-detection-confidence",
    "faq.getting-started.what-is-utc",
    "faq.getting-started.how-often-is-firms-updated",
    "faq.caveats.can-i-estimate-burned-area-from-active-fire-data",
)
NO_DETECTION_CAVEATS = ("faq.caveats.how-do-i-know-if-a-fire-detection-was-missed-due-to-cloud-or",)

INDEPENDENCE_NOTE = (
    "Detections from different satellites, and from different overpasses of one satellite, "
    "are independent observations: the same fire is often detected several times. Do not "
    "add counts across sources or overpasses to count fires."
)
UTC_NOTE = (
    "All dates and times are UTC (acquired_utc); convert carefully before giving local times."
)
NO_INTERPRETATION_NOTE = (
    "Records are FIRMS detections as delivered. This server does not group them into fires, "
    "estimate burned area, or assess danger."
)
RT_URT_NOTE = (
    'FIRMS area API: "RT and URT data are removed when corresponding NRT detections are '
    'processed or RT/URT is older than 6 hours."'
)
LANDSAT_NOTE = "LANDSAT_NRT is offered by FIRMS for US/Canada only."
SP_EMPTY_NOTE = (
    "Standard-processing (SP) sources are published months after observation; use "
    "get_data_availability to see the dates each source covers."
)
CONFIDENCE_NOTE = (
    "A confidence filter was applied at your request. Read the caveat entry 'What is the "
    "detection confidence?' before relying on it."
)
CONFIDENCE_RANK = {"low": 0, "nominal": 1, "medium": 1, "high": 2}
WHOLE_CALL_ERRORS = (AuthRequired, InvalidMapKey, MapKeyRejected, RateLimited)


def date_window(day_range: int, date: dt.date | None, today: dt.date) -> DateWindow:
    """UTC days FIRMS returns: DATE..DATE+DAY_RANGE-1, or TODAY-(DAY_RANGE-1)..TODAY."""
    if date is None:
        return DateWindow(start=today - dt.timedelta(days=day_range - 1), end=today)
    return DateWindow(start=date, end=min(date + dt.timedelta(days=day_range - 1), today))


def _query_payload(query: GetFireDetectionsInput) -> dict[str, Any]:
    return query.model_dump(
        mode="json", include={"area", "day_range", "date", "sources", "min_confidence", "sort"}
    )


def _sorted(detections: list[Detection], order: str) -> list[Detection]:
    def tie(d: Detection) -> tuple:
        return (d.source, d.latitude, d.longitude)

    if order == "frp":
        return sorted(
            detections,
            key=lambda d: (
                d.frp_mw is None,
                -(d.frp_mw or 0.0),
                -d.acquired_utc.timestamp(),
                tie(d),
            ),
        )
    return sorted(detections, key=lambda d: (d.acquired_utc, *tie(d)), reverse=order == "newest")


def _record(detection: Detection, fields: list[str] | None) -> dict[str, Any]:
    record = detection.model_dump(mode="json", exclude_none=True)
    if not record.get("extra"):
        record.pop("extra", None)
    if fields:
        keep = set(MANDATORY_FIELDS) | set(fields)
        record = {k: v for k, v in record.items() if k in keep}
    return record


def _confidence_filter(
    detections: list[Detection], minimum: str
) -> tuple[list[Detection], ConfidenceFilter]:
    threshold = CONFIDENCE_RANK[minimum]
    kept, removed, unclassified = [], 0, 0
    for detection in detections:
        rank = CONFIDENCE_RANK.get(detection.confidence_class or "")
        if rank is None:
            unclassified += 1
        elif rank >= threshold:
            kept.append(detection)
        else:
            removed += 1
    return kept, ConfidenceFilter(
        min_confidence=minimum, kept=len(kept), removed=removed, removed_unclassified=unclassified
    )


def _error_output(code: str, message: str, remediation: str) -> GetFireDetectionsOutput:
    return GetFireDetectionsOutput(
        status="error",
        error_code=code,
        error_message=message,
        remediation=remediation,
        retryable=False,
    )


async def get_fire_detections(
    params: GetFireDetectionsInput, services: Services
) -> GetFireDetectionsOutput:
    today = services.today()
    query, offset, first_page = params, 0, None
    if params.cursor:
        try:
            payload = decode_cursor(TOOL, params.cursor)
            query = GetFireDetectionsInput.model_validate(
                {**payload["q"], "limit": params.limit, "fields": params.fields}
            )
        except (InvalidCursor, ValidationError) as exc:
            message = str(exc) if isinstance(exc, InvalidCursor) else "The cursor is malformed."
            return _error_output("invalid_cursor", message, "Start a new query without a cursor.")
        offset, first_page = payload["o"], payload

    if query.date is not None and query.date > today:
        return GetFireDetectionsOutput.invalid(
            f"date {query.date.isoformat()} is in the future (today is {today.isoformat()} UTC)."
        )
    window = date_window(query.day_range, query.date, today)
    if first_page is not None and first_page.get("w") != window.start.isoformat():
        return _error_output(
            "cursor_expired",
            "The UTC day has changed since the first page, so 'the most recent days' now means "
            "a different window.",
            "Start a new query without a cursor (or give an explicit date).",
        )
    try:
        sources: list[FireSource] = [
            get_source(s)
            for s in dict.fromkeys(s.strip().upper() for s in query.sources or DEFAULT_SOURCES)
        ]
    except ValueError as exc:
        return GetFireDetectionsOutput.invalid(str(exc))
    unknown_fields = sorted(set(query.fields or []) - set(RECORD_FIELDS))
    if unknown_fields:
        return GetFireDetectionsOutput.invalid(
            f"Unknown record field(s): {', '.join(unknown_fields)}. "
            f"Valid fields: {', '.join(RECORD_FIELDS)}."
        )

    map_key = services.credentials.require()
    area = area_to_bbox(query.area)
    outcomes = await asyncio.gather(
        *(
            services.firms.fetch_detections(map_key, s.id, area, query.day_range, query.date)
            for s in sources
        ),
        return_exceptions=True,
    )

    by_source: list[SourceResult] = []
    kept_all: list[Detection] = []
    errors: list[FirmsError] = []
    for source, outcome in zip(sources, outcomes, strict=True):
        if isinstance(outcome, WHOLE_CALL_ERRORS):
            raise outcome
        if isinstance(outcome, FirmsError):
            errors.append(outcome)
            by_source.append(
                SourceResult(
                    source=source.id,
                    label=source.label,
                    status="error",
                    processing_note=source.processing_note,
                    error_code=outcome.code,
                    error_message=outcome.message,
                )
            )
            continue
        if isinstance(outcome, BaseException):
            raise outcome
        result: DetectionsResult = outcome
        kept, applied = result.detections, None
        if query.min_confidence is not None:
            kept, applied = _confidence_filter(result.detections, query.min_confidence)
        kept_all.extend(kept)
        by_source.append(
            SourceResult(
                source=source.id,
                label=source.label,
                status="success" if result.detections else "no_results",
                summary=summarize(source, result.detections),
                confidence_filter=applied,
                request_url=result.request_url,
                retrieved_utc=result.retrieved_utc,
                from_cache=result.from_cache,
                estimated_transactions=result.estimated_transactions,
                processing_note=source.processing_note,
            )
        )

    echo = QueryEcho(
        area=query.area,
        day_range=query.day_range,
        date=query.date,
        window_utc=window,
        sources=[s.id for s in sources],
        min_confidence=query.min_confidence,
        sort=query.sort,
    )
    if len(errors) == len(sources):
        first = errors[0]
        return GetFireDetectionsOutput(
            status="error", **first.as_dict(), query=echo, by_source=by_source
        )

    ordered = _sorted(kept_all, query.sort)
    total = len(ordered)
    page = ordered[offset : offset + query.limit] if query.limit else []
    next_offset = offset + query.limit
    next_cursor = (
        encode_cursor(TOOL, _query_payload(query), next_offset, w=window.start.isoformat(), n=total)
        if query.limit and next_offset < total
        else None
    )

    notes = [INDEPENDENCE_NOTE, UTC_NOTE, NO_INTERPRETATION_NOTE]
    if any(d.processing_level in ("URT", "RT") for d in ordered):
        notes.append(RT_URT_NOTE)
    if any(s.id == "LANDSAT_NRT" for s in sources):
        notes.append(LANDSAT_NOTE)
    if any(r.status == "no_results" and r.source.endswith("_SP") for r in by_source):
        notes.append(SP_EMPTY_NOTE)
    if query.min_confidence is not None:
        notes.append(CONFIDENCE_NOTE)
    if errors:
        notes.append(
            "Some sources failed (see by_source); the summaries and records cover only the "
            "sources that succeeded."
        )
    if first_page is not None and first_page.get("n") != total:
        notes.append(
            f"FIRMS data changed since the first page ({first_page.get('n')} detections then, "
            f"{total} now); pages may overlap or skip records. Start a new query for a "
            "consistent set."
        )

    caveat_ids = [*GENERAL_CAVEATS]
    if total == 0:
        caveat_ids.extend(NO_DETECTION_CAVEATS)
    for source in sources:
        caveat_ids.extend(source.knowledge_entries)

    map_link = None
    try:
        recent_today = query.date is None and query.day_range == 1
        map_link = build_fire_map_link(
            area=None if area.is_world else area,
            period="today" if recent_today else None,
            start_date=None if recent_today else window.start,
            end_date=None if recent_today else window.end,
            sources=[s.id for s in sources],
            referral=services.settings.referral_params,
            today=today,
        )
    except MapLinkError as exc:
        notes.append(f"No Fire Map link could be built: {exc}")

    return GetFireDetectionsOutput(
        status="success" if total else "no_results",
        query=echo,
        by_source=by_source,
        total_records=total,
        returned=len(page),
        next_cursor=next_cursor,
        records=[_record(d, query.fields) for d in page],
        notes=notes,
        caveats=knowledge_refs(services.knowledge, caveat_ids),
        disclaimer=fire_map_disclaimer(services.knowledge),
        citation=firms_citation(services.knowledge),
        map_link=map_link,
    )
