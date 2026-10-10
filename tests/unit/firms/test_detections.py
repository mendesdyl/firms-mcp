"""CSV parsing, normalization, and summaries (FR-DATA-003, FR-DATA-004)."""

from __future__ import annotations

import datetime as dt

import pytest

from firms_mcp.firms.detections import (
    confidence_class,
    parse_acquisition,
    parse_csv,
    processing_level,
    summarize,
)
from firms_mcp.firms.errors import UpstreamFormatError
from firms_mcp.firms.sources import get_source
from tests.fixtures import firms_csv


@pytest.mark.req("FR-DATA-003")
def test_viirs_rows_are_typed_and_in_utc() -> None:
    rows = parse_csv(firms_csv.VIIRS_NOAA20_NRT, get_source("VIIRS_NOAA20_NRT"))
    assert len(rows) == 3
    first = rows[0]
    assert first.latitude == pytest.approx(34.07012)
    assert first.acquired_utc == dt.datetime(2025, 1, 8, 9, 42, tzinfo=dt.UTC)
    assert first.brightness_k == 367.0 and first.brightness_2_k == 295.1
    assert first.frp_mw == 45.2 and first.daynight == "N"
    assert first.confidence == "h" and first.confidence_class == "high"
    assert first.processing_level == "NRT"
    # acq_time without leading zero is the same time
    assert rows[1].acquired_utc == first.acquired_utc
    assert rows[2].processing_level == "URT"


@pytest.mark.req("FR-DATA-003")
def test_modis_landsat_and_standard_processing() -> None:
    modis = parse_csv(firms_csv.MODIS_NRT, get_source("MODIS_NRT"))
    assert [d.confidence_class for d in modis] == ["high", "nominal", "low"]
    assert modis[2].frp_mw is None and modis[2].processing_level == "RT"
    sp = parse_csv(firms_csv.MODIS_SP, get_source("MODIS_SP"))[0]
    assert sp.type == 1 and sp.processing_level == "SP"
    landsat = parse_csv(firms_csv.LANDSAT_NRT, get_source("LANDSAT_NRT"))
    assert [d.confidence_class for d in landsat] == ["high", "medium"]
    assert landsat[0].acquired_utc == dt.datetime(2025, 1, 8, 18, 25, tzinfo=dt.UTC)
    assert landsat[0].path == 41 and landsat[0].row == 36 and landsat[0].scan == 3542


@pytest.mark.req("FR-DATA-003")
def test_unknown_columns_are_kept_and_missing_columns_tolerated() -> None:
    (row,) = parse_csv(firms_csv.WITH_UNKNOWN_COLUMN, get_source("VIIRS_NOAA21_NRT"))
    assert row.extra == {"new_field": "surprise"}
    assert row.brightness_k is None and row.version is None and row.processing_level is None


@pytest.mark.req("FR-DATA-003")
def test_empty_and_header_only_responses() -> None:
    source = get_source("VIIRS_SNPP_NRT")
    assert parse_csv("", source) == []
    assert parse_csv(firms_csv.HEADER_ONLY, source) == []


@pytest.mark.req("FR-DATA-003", "FR-DATA-007")
def test_non_csv_responses_are_format_errors() -> None:
    with pytest.raises(UpstreamFormatError):
        parse_csv("<html>Service unavailable</html>", get_source("MODIS_NRT"))
    with pytest.raises(UpstreamFormatError):
        parse_csv(
            "latitude,longitude,acq_date,acq_time\nx,1,2025-01-01,0000\n", get_source("MODIS_NRT")
        )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("0", "low"),
        ("29.9", "low"),
        ("30", "nominal"),
        ("79", "nominal"),
        ("80", "high"),
        ("100", "high"),
    ],
)
def test_modis_confidence_thresholds_follow_user_guide_table_11(value: str, expected: str) -> None:
    assert confidence_class("modis", value) == expected


def test_letter_confidence_by_family() -> None:
    assert confidence_class("viirs", "n") == "nominal"
    assert confidence_class("viirs", "NOMINAL") == "nominal"
    assert confidence_class("viirs", "m") is None  # 'M' is a Landsat code only
    assert confidence_class("landsat", "M") == "medium"
    assert confidence_class("viirs", "85") is None  # numbers are MODIS only
    assert confidence_class("modis", "") is None


def test_processing_level_from_version() -> None:
    assert processing_level("6.1URT") == "URT"
    assert processing_level("2.0RT") == "RT"
    assert processing_level("2.0NRT") == "NRT"
    assert processing_level("1.0.7 NRT") == "NRT"
    assert processing_level("6.1") == "SP"
    assert processing_level("beta") is None and processing_level(None) is None


def test_acquisition_time_formats() -> None:
    assert parse_acquisition("2026-10-08", "5").hour == 0
    assert parse_acquisition("2026-10-08", "0005").minute == 5
    assert parse_acquisition("2026-10-08", "23:59").minute == 59


@pytest.mark.req("FR-DATA-004")
def test_summary_counts_and_statistics() -> None:
    source = get_source("VIIRS_NOAA20_NRT")
    summary = summarize(source, parse_csv(firms_csv.VIIRS_NOAA20_NRT, source))
    assert summary.detections == 3
    assert summary.overpasses == 2  # "0942" and "942" are the same overpass (09:42 UTC)
    assert summary.by_daynight == {"D": 1, "N": 2}
    assert summary.by_confidence == {"high": 1, "low": 1, "nominal": 1}
    assert summary.by_processing_level == {"NRT": 2, "URT": 1}
    assert summary.first_acquired_utc == dt.datetime(2025, 1, 8, 9, 42, tzinfo=dt.UTC)
    assert summary.last_acquired_utc == dt.datetime(2025, 1, 8, 20, 41, tzinfo=dt.UTC)
    assert summary.frp is not None
    assert summary.frp.count == 3 and summary.frp.max_mw == 45.2 and summary.frp.median_mw == 12.7
    assert summary.extent is not None and summary.extent.contains(-118.55011, 34.07012)


@pytest.mark.req("FR-DATA-004")
def test_summary_of_nothing() -> None:
    summary = summarize(get_source("MODIS_NRT"), [])
    assert summary.detections == 0 and summary.frp is None and summary.extent is None
