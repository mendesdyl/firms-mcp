"""Parse FIRMS area-API CSV into typed detections and summarize them (ADR-0007).

FR-DATA-003: one parser for every source family; columns that are absent are left empty,
columns that are not recognized are kept in ``extra`` rather than dropped.
FR-DATA-004: per-source summaries (counts, time range, overpasses, day/night, confidence,
processing level, FRP statistics, extent).

Confidence classes follow FIRMS's documentation:
* MODIS — a 0-100 % value; classes per the MODIS C6/C6.1 Active Fire Product User's Guide
  v1.0 (May 2021), section 8.4.3, Table 11: low 0 <= C < 30, nominal 30 <= C < 80,
  high 80 <= C <= 100.
* VIIRS — low / nominal / high (VIIRS C2 375 m Active Fire Product User's Guide v1.2).
* Landsat — H / M / L: higher / medium / lower (FIRMS FAQ, Landsat attribute table).
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import re
import statistics
from collections import Counter
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from firms_mcp.firms.errors import UpstreamFormatError
from firms_mcp.firms.geo import BoundingBox
from firms_mcp.firms.sources import FireSource

ConfidenceClass = Literal["low", "nominal", "high", "medium"]
ProcessingLevel = Literal["URT", "RT", "NRT", "SP"]

KNOWN_COLUMNS = {
    "latitude",
    "longitude",
    "acq_date",
    "acq_time",
    "satellite",
    "instrument",
    "confidence",
    "version",
    "frp",
    "daynight",
    "scan",
    "track",
    "type",
    "brightness",
    "bright_ti4",
    "bright_t31",
    "bright_ti5",
    "path",
    "row",
}


class Detection(BaseModel):
    """One FIRMS detection: the center of a pixel flagged as containing a thermal anomaly."""

    model_config = ConfigDict(extra="forbid")

    source: str = Field(description="FIRMS API source ID")
    latitude: float = Field(description="Pixel center latitude (WGS84)")
    longitude: float = Field(description="Pixel center longitude (WGS84)")
    acquired_utc: dt.datetime = Field(description="Acquisition date and time in UTC")
    acq_date: str
    acq_time: str = Field(description="As delivered by FIRMS (HHMM, UTC)")
    satellite: str | None = None
    instrument: str | None = None
    confidence: str | None = Field(default=None, description="As delivered by FIRMS")
    confidence_class: ConfidenceClass | None = Field(
        default=None, description="Class per FIRMS documentation for this sensor"
    )
    brightness_k: float | None = Field(
        default=None, description="Mid-infrared brightness temperature (VIIRS I-4 / MODIS 21-22)"
    )
    brightness_2_k: float | None = Field(
        default=None, description="Thermal-infrared brightness temperature (VIIRS I-5 / MODIS 31)"
    )
    frp_mw: float | None = Field(default=None, description="Fire radiative power, MW")
    scan: float | None = Field(
        default=None,
        description="Along-scan pixel size (km) for MODIS/VIIRS; pixel index for Landsat",
    )
    track: float | None = Field(
        default=None,
        description="Along-track pixel size (km) for MODIS/VIIRS; pixel index for Landsat",
    )
    daynight: Literal["D", "N"] | None = None
    version: str | None = None
    processing_level: ProcessingLevel | None = Field(
        default=None, description="From the version suffix: URT, RT, NRT, or SP (no suffix)"
    )
    type: int | None = Field(
        default=None,
        description="Standard-processing MODIS only: 0 vegetation fire, 1 volcano, 2 other static land source, 3 offshore",
    )
    path: int | None = None
    row: int | None = None
    extra: dict[str, str] = Field(default_factory=dict, description="Unrecognized columns")


def _float(value: str | None) -> float | None:
    if value is None or value.strip() == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _int(value: str | None) -> int | None:
    number = _float(value)
    return int(number) if number is not None and number.is_integer() else None


def parse_acquisition(acq_date: str, acq_time: str) -> dt.datetime:
    """Combine FIRMS ``acq_date`` (YYYY-MM-DD) and ``acq_time`` (HHMM, UTC)."""
    date = dt.date.fromisoformat(acq_date.strip()[:10])
    text = acq_time.strip()
    if ":" in text:
        hours, minutes = (int(p) for p in text.split(":")[:2])
    else:
        digits = re.sub(r"\D", "", text).zfill(4)[-4:]
        hours, minutes = int(digits[:2]), int(digits[2:])
    return dt.datetime(date.year, date.month, date.day, hours, minutes, tzinfo=dt.UTC)


def confidence_class(family: str, value: str | None) -> ConfidenceClass | None:
    if value is None or not value.strip():
        return None
    text = value.strip().lower()
    numeric = _float(text)
    if numeric is not None:
        if family != "modis":
            return None
        if numeric < 30:
            return "low"
        if numeric < 80:
            return "nominal"
        return "high"
    words: dict[str, ConfidenceClass] = {
        "l": "low",
        "low": "low",
        "lower": "low",
        "n": "nominal",
        "nominal": "nominal",
        "h": "high",
        "high": "high",
        "higher": "high",
    }
    if family == "landsat":
        words.update({"m": "medium", "medium": "medium"})
    return words.get(text)


def processing_level(version: str | None) -> ProcessingLevel | None:
    if not version:
        return None
    text = version.strip().upper().replace(" ", "")
    for suffix in ("URT", "NRT", "RT"):
        if text.endswith(suffix):
            return suffix  # type: ignore[return-value]
    return "SP" if re.fullmatch(r"[0-9.]+", text) else None


def parse_csv(text: str, source: FireSource) -> list[Detection]:
    """Parse an area-API CSV response. Raises UpstreamFormatError if it is not a FIRMS CSV."""
    stripped = text.lstrip("﻿").strip()
    if not stripped:
        return []
    reader = csv.DictReader(io.StringIO(stripped))
    header = [h.strip().lower() for h in (reader.fieldnames or [])]
    if "latitude" not in header or "longitude" not in header:
        raise UpstreamFormatError(
            "FIRMS response is not a detection CSV: " + stripped[:200].replace("\n", " ")
        )
    detections: list[Detection] = []
    for raw in reader:
        row = {(k or "").strip().lower(): (v or "").strip() for k, v in raw.items()}
        try:
            acquired = parse_acquisition(row.get("acq_date", ""), row.get("acq_time", ""))
            latitude = float(row["latitude"])
            longitude = float(row["longitude"])
        except (KeyError, ValueError) as exc:
            raise UpstreamFormatError(f"malformed FIRMS row: {exc}") from exc
        brightness = row.get("bright_ti4") or row.get("brightness")
        brightness_2 = row.get("bright_ti5") or row.get("bright_t31")
        daynight = row.get("daynight", "").upper() or None
        detections.append(
            Detection(
                source=source.id,
                latitude=latitude,
                longitude=longitude,
                acquired_utc=acquired,
                acq_date=row.get("acq_date", ""),
                acq_time=row.get("acq_time", ""),
                satellite=row.get("satellite") or None,
                instrument=row.get("instrument") or None,
                confidence=row.get("confidence") or None,
                confidence_class=confidence_class(source.family, row.get("confidence")),
                brightness_k=_float(brightness),
                brightness_2_k=_float(brightness_2),
                frp_mw=_float(row.get("frp")),
                scan=_float(row.get("scan")),
                track=_float(row.get("track")),
                daynight=daynight if daynight in ("D", "N") else None,
                version=row.get("version") or None,
                processing_level=processing_level(row.get("version")),
                type=_int(row.get("type")),
                path=_int(row.get("path")),
                row=_int(row.get("row")),
                extra={k: v for k, v in row.items() if k and k not in KNOWN_COLUMNS},
            )
        )
    return detections


class FrpStatistics(BaseModel):
    count: int = Field(description="Detections with an FRP value")
    min_mw: float
    median_mw: float
    max_mw: float
    sum_mw: float = Field(
        description="Sum over detections; only meaningful within one overpass of one sensor"
    )


class SourceSummary(BaseModel):
    source: str
    label: str
    detections: int
    first_acquired_utc: dt.datetime | None = None
    last_acquired_utc: dt.datetime | None = None
    overpasses: int = Field(
        description="Distinct (satellite, acquisition time) combinations in the results"
    )
    by_satellite: dict[str, int] = Field(default_factory=dict)
    by_daynight: dict[str, int] = Field(default_factory=dict)
    by_confidence: dict[str, int] = Field(
        default_factory=dict, description="Counts by confidence class (raw value if unclassified)"
    )
    by_processing_level: dict[str, int] = Field(default_factory=dict)
    frp: FrpStatistics | None = None
    extent: BoundingBox | None = Field(default=None, description="Box around detection centers")


def summarize(source: FireSource, detections: list[Detection]) -> SourceSummary:
    times = [d.acquired_utc for d in detections]
    frp_values = [d.frp_mw for d in detections if d.frp_mw is not None]
    overpasses = {(d.satellite, d.acquired_utc) for d in detections}

    def counts(values) -> dict[str, int]:
        return dict(sorted(Counter(v for v in values if v).items()))

    return SourceSummary(
        source=source.id,
        label=source.label,
        detections=len(detections),
        first_acquired_utc=min(times) if times else None,
        last_acquired_utc=max(times) if times else None,
        overpasses=len(overpasses),
        by_satellite=counts(d.satellite for d in detections),
        by_daynight=counts(d.daynight for d in detections),
        by_confidence=counts(d.confidence_class or d.confidence for d in detections),
        by_processing_level=counts(d.processing_level for d in detections),
        frp=FrpStatistics(
            count=len(frp_values),
            min_mw=min(frp_values),
            median_mw=round(statistics.median(frp_values), 3),
            max_mw=max(frp_values),
            sum_mw=round(sum(frp_values), 3),
        )
        if frp_values
        else None,
        extent=BoundingBox.around([(d.longitude, d.latitude) for d in detections]),
    )
