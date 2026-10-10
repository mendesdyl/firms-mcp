"""Async client for the FIRMS API (ADR-0007).

Endpoints (FIRMS API v4.1.16, 2026-10-09):

* ``/api/area/csv/{MAP_KEY}/{SOURCE}/{AREA}/{DAY_RANGE}[/{DATE}]`` — detections
* ``/api/data_availability/csv/{MAP_KEY}/{SENSOR}`` — date coverage per product
* ``/mapserver/mapkey_status/?MAP_KEY=…`` — transactions used for a key
* ``/api/map_dates/`` — public date coverage used by the Fire Map (undocumented; no key)

The MAP_KEY is passed per call and never stored, logged, or returned: URLs reported to
callers have the key replaced by ``[MAP_KEY]``.
"""

from __future__ import annotations

import asyncio
import csv
import datetime as dt
import io
import json
import logging
import re
from collections.abc import Awaitable, Callable
from typing import Any

import httpx
from pydantic import BaseModel, Field

from firms_mcp import __version__
from firms_mcp.config import Settings, get_settings
from firms_mcp.firms.budget import TransactionBudget, transaction_weight
from firms_mcp.firms.cache import ResponseCache
from firms_mcp.firms.detections import Detection, parse_csv
from firms_mcp.firms.errors import (
    FirmsError,
    InvalidMapKey,
    InvalidRequest,
    MapKeyRejected,
    RateLimited,
    UpstreamFormatError,
    UpstreamUnavailable,
)
from firms_mcp.firms.geo import BoundingBox
from firms_mcp.firms.sources import AVAILABILITY_SENSORS, SOURCES, FireSource, get_source
from firms_mcp.redaction import PLACEHOLDER, install_log_redaction, redact, register_secret

logger = logging.getLogger(__name__)

MAX_DAY_RANGE = 5  # FIRMS area API: DAY_RANGE 1..5


class DetectionsResult(BaseModel):
    source: str
    detections: list[Detection]
    request_url: str = Field(description="FIRMS URL with the MAP_KEY redacted")
    retrieved_utc: dt.datetime
    from_cache: bool
    estimated_transactions: int


class AvailabilityRecord(BaseModel):
    data_id: str
    min_date: str | None = None
    max_date: str | None = None
    extra: dict[str, str] = Field(default_factory=dict)


class MapKeyStatus(BaseModel):
    transaction_limit: int | None = None
    current_transactions: int | None = None
    transaction_interval: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict, description="Full response from FIRMS")


class DateRange(BaseModel):
    start: dt.date
    end: dt.date


def validate_query(day_range: int, date: dt.date | None, today: dt.date | None = None) -> None:
    if not 1 <= day_range <= MAX_DAY_RANGE:
        raise InvalidRequest(f"day_range must be between 1 and {MAX_DAY_RANGE} (FIRMS limit)")
    today = today or dt.datetime.now(dt.UTC).date()
    if date is not None and date > today:
        raise InvalidRequest(f"date {date.isoformat()} is in the future (today is {today} UTC)")


class FirmsClient:
    def __init__(
        self,
        settings: Settings | None = None,
        *,
        http: httpx.AsyncClient | None = None,
        cache: ResponseCache | None = None,
        budget: TransactionBudget | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self.settings = settings or get_settings()
        # FIRMS URLs carry the MAP_KEY; make sure no logger can print them (SEC-001).
        install_log_redaction()
        self._own_http = http is None
        self.http = http or httpx.AsyncClient(
            timeout=self.settings.http_timeout_seconds,
            headers={"User-Agent": f"firms-mcp/{__version__}"},
            follow_redirects=True,
        )
        self.cache = cache or ResponseCache(self.settings.cache_max_entries)
        self.budget = budget or TransactionBudget(self.settings.transaction_budget)
        self._sleep = sleep

    async def aclose(self) -> None:
        if self._own_http:
            await self.http.aclose()

    async def __aenter__(self) -> FirmsClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()

    # -- URLs -------------------------------------------------------------------------------
    @property
    def base(self) -> str:
        return self.settings.firms_base_url.rstrip("/")

    def area_url(
        self,
        map_key: str,
        source: FireSource,
        area: BoundingBox,
        day_range: int,
        date: dt.date | None,
    ) -> str:
        url = f"{self.base}/api/area/csv/{map_key}/{source.id}/{area.to_api()}/{day_range}"
        return f"{url}/{date.isoformat()}" if date else url

    # -- HTTP -------------------------------------------------------------------------------
    async def _get(self, url: str) -> httpx.Response:
        attempts = self.settings.http_retries + 1
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                response = await self.http.get(url)
            except httpx.TimeoutException as exc:
                last_error = UpstreamUnavailable(f"FIRMS request timed out: {exc!r}")
            except httpx.TransportError as exc:
                last_error = UpstreamUnavailable(f"could not reach FIRMS: {exc!r}")
            else:
                if response.status_code < 400:
                    return response
                error = self._map_error(response)
                if not isinstance(error, UpstreamUnavailable):
                    raise error
                last_error = error
            if attempt + 1 < attempts:
                await self._sleep(self.settings.retry_backoff_seconds * (2**attempt))
        assert last_error is not None
        raise last_error

    @staticmethod
    def _map_error(response: httpx.Response) -> FirmsError:
        status = response.status_code
        raw = response.text.strip()
        body = redact(raw)[:300]
        detail = f"FIRMS returned HTTP {status}: {body or response.reason_phrase}"
        if status in (400, 401) and re.search(r"invalid\s+map_?key", raw, re.IGNORECASE):
            return InvalidMapKey(detail)
        if status == 403:
            return MapKeyRejected(detail)
        if status == 429:
            return RateLimited(detail)
        if status >= 500:
            return UpstreamUnavailable(detail)
        return InvalidRequest(detail)

    # -- endpoints --------------------------------------------------------------------------
    async def fetch_detections(
        self,
        map_key: str,
        source_id: str,
        area: BoundingBox,
        day_range: int = 1,
        date: dt.date | None = None,
    ) -> DetectionsResult:
        """Detections for one source. Results are cached; upstream calls are budgeted."""
        source = get_source(source_id)
        validate_query(day_range, date)
        register_secret(map_key)
        weight = transaction_weight(source.id, area, day_range)
        key = ("area", source.id, area.to_api(), day_range, date.isoformat() if date else None)
        ttl = (
            self.settings.cache_ttl_sp_seconds
            if source.processing == "SP"
            else self.settings.cache_ttl_nrt_seconds
        )

        async def fetch() -> tuple[list[Detection], dt.datetime]:
            self.budget.charge(map_key, weight)
            response = await self._get(self.area_url(map_key, source, area, day_range, date))
            text = response.text
            if text.lstrip().lower().startswith("invalid"):
                raise InvalidRequest(f"FIRMS rejected the request: {redact(text.strip())[:300]}")
            return parse_csv(text, source), dt.datetime.now(dt.UTC)

        (detections, retrieved), from_cache = await self.cache.get_or_fetch(key, ttl, fetch)
        return DetectionsResult(
            source=source.id,
            detections=detections,
            request_url=self.area_url(PLACEHOLDER, source, area, day_range, date),
            retrieved_utc=retrieved,
            from_cache=from_cache,
            estimated_transactions=0 if from_cache else weight,
        )

    async def data_availability(
        self, map_key: str, sensor: str = "ALL"
    ) -> list[AvailabilityRecord]:
        sensor = sensor.upper()
        if sensor not in AVAILABILITY_SENSORS:
            raise InvalidRequest(
                f"unknown sensor {sensor!r}; valid: {', '.join(AVAILABILITY_SENSORS)}"
            )
        register_secret(map_key)
        url = f"{self.base}/api/data_availability/csv/{map_key}/{sensor}"
        response = await self._get(url)
        text = response.text.strip()
        reader = csv.DictReader(io.StringIO(text))
        fields = [f.strip().lower() for f in (reader.fieldnames or [])]
        if "data_id" not in fields:
            raise UpstreamFormatError(
                "FIRMS data_availability response is not CSV: " + redact(text[:200])
            )
        records = []
        for raw in reader:
            row = {(k or "").strip().lower(): (v or "").strip() for k, v in raw.items()}
            records.append(
                AvailabilityRecord(
                    data_id=row.get("data_id", ""),
                    min_date=row.get("min_date") or None,
                    max_date=row.get("max_date") or None,
                    extra={
                        k: v for k, v in row.items() if k not in {"data_id", "min_date", "max_date"}
                    },
                )
            )
        return records

    async def map_key_status(self, map_key: str) -> MapKeyStatus:
        register_secret(map_key)
        response = await self._get(f"{self.base}/mapserver/mapkey_status/?MAP_KEY={map_key}")
        try:
            data = response.json()
        except (json.JSONDecodeError, ValueError) as exc:
            raise UpstreamFormatError(
                "FIRMS MAP_KEY status response is not JSON: " + redact(response.text[:200])
            ) from exc
        if not isinstance(data, dict):
            raise UpstreamFormatError("FIRMS MAP_KEY status response is not a JSON object")

        def as_int(value: Any) -> int | None:
            try:
                return int(value)
            except (TypeError, ValueError):
                return None

        return MapKeyStatus(
            transaction_limit=as_int(data.get("transaction_limit")),
            current_transactions=as_int(data.get("current_transactions")),
            transaction_interval=str(data["transaction_interval"])
            if data.get("transaction_interval") is not None
            else None,
            raw=data,
        )

    async def map_dates(self) -> dict[str, DateRange]:
        """Public date coverage per Fire Map product (no MAP_KEY). Cached for one hour."""

        async def fetch() -> dict[str, DateRange]:
            response = await self._get(f"{self.base}/api/map_dates/")
            try:
                data = response.json()
            except (json.JSONDecodeError, ValueError) as exc:
                raise UpstreamFormatError("FIRMS map date service did not return JSON") from exc
            result = {}
            for key, value in data.items():
                if isinstance(value, list) and len(value) == 2:
                    try:
                        result[key] = DateRange(
                            start=dt.date.fromisoformat(value[0]),
                            end=dt.date.fromisoformat(value[1]),
                        )
                    except (TypeError, ValueError):
                        logger.warning("ignoring unparseable map date entry %s", key)
            return result

        value, _ = await self.cache.get_or_fetch(("map_dates",), 3600, fetch)
        return value


def sources_for_map_dates(dates: dict[str, DateRange]) -> dict[str, DateRange]:
    """Re-key the map date service's product keys to FIRMS API source IDs."""
    return {
        source.id: dates[source.map_dates_key]
        for source in SOURCES.values()
        if source.map_dates_key in dates
    }
