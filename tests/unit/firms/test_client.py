"""FIRMS client behaviour against mocked HTTP (FR-DATA-001/002/007/008/009/012, SEC-001)."""

from __future__ import annotations

import datetime as dt
import logging

import httpx
import pytest
import respx

from firms_mcp.config import Settings
from firms_mcp.firms.client import FirmsClient, sources_for_map_dates, validate_query
from firms_mcp.firms.errors import (
    InvalidMapKey,
    InvalidRequest,
    MapKeyRejected,
    RateLimited,
    UpstreamFormatError,
    UpstreamUnavailable,
)
from firms_mcp.firms.geo import BoundingBox
from tests.fixtures import firms_csv
from tests.fixtures.firms_csv import MAP_KEY

BASE = "https://firms.test"
BOX = BoundingBox(west=-119.2, south=33.8, east=-117.6, north=34.6)


def make_client(**overrides) -> FirmsClient:
    settings = Settings(
        _env_file=None,
        FIRMS_API_BASE_URL=BASE,
        FIRMS_MCP_RETRY_BACKOFF=0,
        **overrides,
    )

    async def no_sleep(_: float) -> None:
        return None

    return FirmsClient(settings, sleep=no_sleep)


@pytest.fixture
async def client():
    async with make_client() as c:
        yield c


@pytest.mark.req("FR-DATA-001")
async def test_fetch_detections_builds_the_documented_url(client: FirmsClient) -> None:
    with respx.mock(assert_all_called=True) as router:
        route = router.get(
            f"{BASE}/api/area/csv/{MAP_KEY}/VIIRS_NOAA20_NRT/-119.2,33.8,-117.6,34.6/3/2025-01-07"
        ).respond(200, text=firms_csv.VIIRS_NOAA20_NRT)
        result = await client.fetch_detections(
            MAP_KEY, "VIIRS_NOAA20_NRT", BOX, day_range=3, date=dt.date(2025, 1, 7)
        )
    assert route.call_count == 1
    assert len(result.detections) == 3
    assert result.from_cache is False
    assert result.estimated_transactions == 6  # 1 x 1 x 2 x 3 days
    assert result.request_url == (
        f"{BASE}/api/area/csv/[MAP_KEY]/VIIRS_NOAA20_NRT/-119.2,33.8,-117.6,34.6/3/2025-01-07"
    )


@pytest.mark.req("FR-DATA-001")
async def test_world_and_latest_data(client: FirmsClient) -> None:
    with respx.mock(assert_all_called=True) as router:
        router.get(f"{BASE}/api/area/csv/{MAP_KEY}/MODIS_NRT/world/1").respond(
            200, text=firms_csv.HEADER_ONLY
        )
        result = await client.fetch_detections(MAP_KEY, "MODIS_NRT", BoundingBox.world())
    assert result.detections == []


@pytest.mark.req("FR-DATA-012")
async def test_identical_requests_are_served_from_cache(client: FirmsClient) -> None:
    with respx.mock() as router:
        route = router.get(url__regex=r".*/api/area/csv/.*").respond(200, text=firms_csv.MODIS_NRT)
        first = await client.fetch_detections(MAP_KEY, "MODIS_NRT", BOX)
        second = await client.fetch_detections(MAP_KEY, "MODIS_NRT", BOX)
    assert route.call_count == 1
    assert second.from_cache and second.estimated_transactions == 0
    assert second.retrieved_utc == first.retrieved_utc
    assert client.budget.used(MAP_KEY) == 1  # charged once


@pytest.mark.req("FR-DATA-002")
@pytest.mark.parametrize(
    ("day_range", "date", "message"),
    [
        (0, None, "between 1 and 5"),
        (6, None, "between 1 and 5"),
        (1, dt.date(2026, 10, 11), "future"),
    ],
)
def test_query_validation(day_range: int, date: dt.date | None, message: str) -> None:
    with pytest.raises(InvalidRequest, match=message):
        validate_query(day_range, date, today=dt.date(2026, 10, 10))


@pytest.mark.req("FR-DATA-002")
async def test_unknown_source_is_rejected_before_any_request(client: FirmsClient) -> None:
    with respx.mock(assert_all_called=False) as router, pytest.raises(ValueError, match="unknown"):
        await client.fetch_detections(MAP_KEY, "GOES_NRT", BOX)
    assert router.calls.call_count == 0


@pytest.mark.req("FR-DATA-007")
@pytest.mark.parametrize(
    ("status", "body", "error"),
    [
        (400, "Invalid MAP_KEY.", InvalidMapKey),
        (401, "Invalid MAP_KEY.", InvalidMapKey),
        (
            403,
            "MAP_KEY is invalid or your have exceeded your transaction/time limit. Please try again later.",
            MapKeyRejected,
        ),
        (429, "Too many requests", RateLimited),
        (400, "Invalid area coordinates", InvalidRequest),
        (404, "Not found", InvalidRequest),
    ],
)
async def test_upstream_errors_map_to_stable_codes(client, status, body, error) -> None:
    with respx.mock() as router:
        route = router.get(url__regex=r".*/api/area/csv/.*").respond(status, text=body)
        with pytest.raises(error) as raised:
            await client.fetch_detections(MAP_KEY, "VIIRS_SNPP_NRT", BOX)
    assert route.call_count == 1  # 4xx are never retried
    payload = raised.value.as_dict()
    assert payload["error_code"] == error.code
    assert payload["remediation"]
    assert MAP_KEY not in payload["error_message"]


@pytest.mark.req("FR-DATA-007")
async def test_server_errors_and_timeouts_are_retried_then_reported(client: FirmsClient) -> None:
    with respx.mock() as router:
        route = router.get(url__regex=r".*/api/area/csv/.*").mock(
            side_effect=[
                httpx.Response(503, text="busy"),
                httpx.ReadTimeout("slow"),
                httpx.Response(502, text="bad gateway"),
            ]
        )
        with pytest.raises(UpstreamUnavailable):
            await client.fetch_detections(MAP_KEY, "VIIRS_SNPP_NRT", BOX)
    assert route.call_count == 3  # 1 attempt + 2 retries


@pytest.mark.req("FR-DATA-007")
async def test_transient_failure_then_success(client: FirmsClient) -> None:
    with respx.mock() as router:
        router.get(url__regex=r".*/api/area/csv/.*").mock(
            side_effect=[httpx.ConnectError("down"), httpx.Response(200, text=firms_csv.MODIS_NRT)]
        )
        result = await client.fetch_detections(MAP_KEY, "MODIS_NRT", BOX)
    assert len(result.detections) == 3


@pytest.mark.req("FR-DATA-007")
async def test_error_text_with_status_200_is_an_error(client: FirmsClient) -> None:
    with respx.mock() as router:
        router.get(url__regex=r".*/api/area/csv/.*").respond(200, text="Invalid day range.")
        with pytest.raises(InvalidRequest, match="Invalid day range"):
            await client.fetch_detections(MAP_KEY, "MODIS_NRT", BOX)


@pytest.mark.req("FR-DATA-013")
async def test_budget_blocks_before_contacting_firms() -> None:
    async with make_client(FIRMS_MCP_TRANSACTION_BUDGET=40) as small:
        with respx.mock() as router:
            route = router.get(url__regex=r".*/api/area/csv/.*").respond(
                200, text=firms_csv.HEADER_ONLY
            )
            await small.fetch_detections(MAP_KEY, "VIIRS_SNPP_NRT", BoundingBox.world())  # 36
            with pytest.raises(RateLimited):
                await small.fetch_detections(MAP_KEY, "VIIRS_NOAA20_NRT", BoundingBox.world())
        assert route.call_count == 1


@pytest.mark.req("FR-DATA-008")
async def test_data_availability(client: FirmsClient) -> None:
    csv_text = "data_id,min_date,max_date\nMODIS_NRT,2020-11-01,2026-10-10\nVIIRS_SNPP_SP,2012-01-20,2026-06-30\n"
    with respx.mock() as router:
        router.get(f"{BASE}/api/data_availability/csv/{MAP_KEY}/ALL").respond(200, text=csv_text)
        records = await client.data_availability(MAP_KEY)
    assert [(r.data_id, r.min_date, r.max_date) for r in records] == [
        ("MODIS_NRT", "2020-11-01", "2026-10-10"),
        ("VIIRS_SNPP_SP", "2012-01-20", "2026-06-30"),
    ]
    with pytest.raises(InvalidRequest, match="unknown sensor"):
        await client.data_availability(MAP_KEY, "GOES")


@pytest.mark.req("FR-DATA-008")
async def test_data_availability_format_error(client: FirmsClient) -> None:
    with respx.mock() as router:
        router.get(url__regex=r".*/api/data_availability/.*").respond(200, text="<html></html>")
        with pytest.raises(UpstreamFormatError):
            await client.data_availability(MAP_KEY, "MODIS_NRT")


@pytest.mark.req("FR-DATA-008")
async def test_public_map_dates_are_rekeyed_to_api_sources(client: FirmsClient) -> None:
    payload = {
        "modis_nrt": ["2020-11-01", "2026-10-10"],
        "suomi_viirs_c2_sp": ["2012-01-20", "2026-06-30"],
        "goesr_abi_c1_nrt": ["2022-08-09", "2026-10-10"],
        "broken": ["not-a-date", "x"],
    }
    with respx.mock() as router:
        route = router.get(f"{BASE}/api/map_dates/").respond(200, json=payload)
        dates = await client.map_dates()
        await client.map_dates()  # cached
    assert route.call_count == 1
    assert "broken" not in dates and "goesr_abi_c1_nrt" in dates
    by_source = sources_for_map_dates(dates)
    assert by_source["MODIS_NRT"].start == dt.date(2020, 11, 1)
    assert by_source["VIIRS_SNPP_SP"].end == dt.date(2026, 6, 30)
    assert "LANDSAT_NRT" not in by_source


@pytest.mark.req("FR-DATA-009")
async def test_map_key_status(client: FirmsClient) -> None:
    payload = {
        "transaction_limit": 5000,
        "current_transactions": 12,
        "transaction_interval": "10 minutes",
    }
    with respx.mock() as router:
        router.get(f"{BASE}/mapserver/mapkey_status/", params={"MAP_KEY": MAP_KEY}).respond(
            200, json=payload
        )
        status = await client.map_key_status(MAP_KEY)
    assert status.transaction_limit == 5000 and status.current_transactions == 12
    assert status.transaction_interval == "10 minutes"
    assert status.raw == payload


@pytest.mark.req("FR-DATA-009", "FR-DATA-007")
async def test_map_key_status_rejected_and_malformed(client: FirmsClient) -> None:
    with respx.mock() as router:
        router.get(url__regex=r".*/mapkey_status/.*").respond(
            403, text="MAP_KEY is invalid or your have exceeded your transaction/time limit."
        )
        with pytest.raises(MapKeyRejected):
            await client.map_key_status(MAP_KEY)
    with respx.mock() as router:
        router.get(url__regex=r".*/mapkey_status/.*").respond(200, text="not json")
        with pytest.raises(UpstreamFormatError):
            await client.map_key_status(MAP_KEY)


@pytest.mark.req("SEC-001")
async def test_map_key_never_reaches_logs_or_errors(client: FirmsClient, caplog) -> None:
    caplog.set_level(logging.DEBUG)
    with respx.mock() as router:
        router.get(url__regex=r".*/api/area/csv/.*").respond(
            400, text=f"Invalid request for /api/area/csv/{MAP_KEY}/X"
        )
        with pytest.raises(InvalidRequest) as raised:
            await client.fetch_detections(MAP_KEY, "VIIRS_SNPP_NRT", BOX)
    assert MAP_KEY not in str(raised.value)
    assert MAP_KEY not in caplog.text
