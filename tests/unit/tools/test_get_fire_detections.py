"""get_fire_detections against a mocked FIRMS (ADR-0007).

FR-DATA-001/002/005/006/014, NFR-004, SEC-001, FR-AUTH-001, FR-AUTH-010.
"""

from __future__ import annotations

import datetime as dt
import json
from urllib.parse import urlsplit

import pytest
import respx
from fastmcp import Client

from firms_mcp.credentials import CredentialMode
from tests.fixtures import firms_csv
from tests.fixtures.firms_csv import MAP_KEY
from tests.fixtures.services import FIRMS_BASE, NOW, make_server, make_services, repo_knowledge

LA = {"west": -119.2, "south": 33.8, "east": -117.6, "north": 34.6}
LA_API = "-119.2,33.8,-117.6,34.6"
DAY = "2025-01-08"


def area_url(source: str, area: str = LA_API, days: int = 1, date: str | None = DAY) -> str:
    url = f"{FIRMS_BASE}/api/area/csv/{MAP_KEY}/{source}/{area}/{days}"
    return f"{url}/{date}" if date else url


async def call(arguments: dict, services=None) -> dict:
    services = services or make_services(map_key=MAP_KEY)
    async with Client(make_server(services)) as client:
        result = await client.call_tool("get_fire_detections", arguments, raise_on_error=False)
    assert result.is_error == (result.structured_content["status"] == "error")
    return result.structured_content


def mock_two_sources(router: respx.MockRouter, **kwargs) -> tuple:
    viirs = router.get(area_url("VIIRS_NOAA20_NRT", **kwargs)).respond(
        200, text=firms_csv.VIIRS_NOAA20_NRT
    )
    modis = router.get(area_url("MODIS_NRT", **kwargs)).respond(200, text=firms_csv.MODIS_NRT)
    return viirs, modis


TWO_SOURCES = {"area": LA, "date": DAY, "sources": ["VIIRS_NOAA20_NRT", "MODIS_NRT"]}


@pytest.mark.req("FR-DATA-001", "FR-DATA-004", "FR-DATA-006", "SEC-001")
async def test_result_carries_summaries_caveats_disclaimer_citation_and_link() -> None:
    knowledge = repo_knowledge()
    with respx.mock(assert_all_called=True) as router:
        mock_two_sources(router)
        result = await call(TWO_SOURCES)

    assert result["status"] == "success"
    assert result["query"]["window_utc"] == {"start": DAY, "end": DAY}
    summaries = {s["source"]: s for s in result["by_source"]}
    assert summaries["VIIRS_NOAA20_NRT"]["summary"]["detections"] == 3
    assert summaries["VIIRS_NOAA20_NRT"]["summary"]["overpasses"] == 2
    assert summaries["MODIS_NRT"]["summary"]["by_satellite"] == {"Aqua": 2, "Terra": 1}
    assert result["total_records"] == 6 and result["returned"] == 6

    # Caveats: FIRMS's own entries, starting with what a detection means.
    caveat_ids = [c["id"] for c in result["caveats"]]
    assert caveat_ids[0] == "faq.getting-started.what-does-a-fire-detection-mean-on-the-ground"
    assert "faq.viirs.what-is-the-viirs-375-m-active-fire-product" in caveat_ids
    assert all(knowledge.get(i) is not None for i in caveat_ids)
    # Disclaimer and citation verbatim from the knowledge base.
    disclaimer = knowledge.get("supplement.disclaimers.fire-map-disclaimer")
    assert result["disclaimer"]["text"] == disclaimer.body
    assert result["disclaimer"]["text"].startswith("Do not use for the preservation of life")
    citation = knowledge.get(
        "faq.getting-started.are-there-any-restrictions-on-using-data-or-imagery-from-firms"
    )
    assert result["citation"]["text"] == citation.body
    # Notes: independence of observations, UTC, no interpretation, RT/URT replacement.
    notes = " ".join(result["notes"])
    assert "Do not add counts across sources" in notes
    assert "UTC" in notes
    assert "RT and URT data are removed" in notes  # the VIIRS fixture has a URT record
    # Map link reproduces the query: per-satellite layers, the UTC day, and the box.
    link = result["map_link"]
    assert urlsplit(link["url"]).fragment == (
        "m:advanced;d:2025-01-08;"
        "l:fires_viirs_noaa20,fires_modis_terra,fires_modis_aqua,country-outline,earth;"
        f"i:{LA_API}"
    )
    # Provenance with the key redacted; the key appears nowhere in the result.
    assert summaries["MODIS_NRT"]["request_url"] == area_url("MODIS_NRT").replace(
        MAP_KEY, "[MAP_KEY]"
    )
    assert summaries["MODIS_NRT"]["estimated_transactions"] == 1
    assert MAP_KEY not in json.dumps(result)


@pytest.mark.req("FR-DATA-005", "NFR-004", "FR-DATA-012")
async def test_records_are_paged_with_a_query_scoped_cursor() -> None:
    services = make_services(map_key=MAP_KEY)
    with respx.mock(assert_all_called=True) as router:
        viirs, modis = mock_two_sources(router)
        page1 = await call({**TWO_SOURCES, "limit": 4}, services)
        assert page1["returned"] == 4 and page1["total_records"] == 6
        assert page1["next_cursor"]
        times = [r["acquired_utc"] for r in page1["records"]]
        assert times == sorted(times, reverse=True)  # newest first by default

        # The cursor fixes the query: a different area here is ignored.
        page2 = await call(
            {"area": "world", "cursor": page1["next_cursor"], "limit": 4, "fields": ["frp_mw"]},
            services,
        )
        assert page2["query"]["area"] == LA
        assert page2["returned"] == 2 and "next_cursor" not in page2
        assert set(page2["records"][0]) <= {
            "source",
            "latitude",
            "longitude",
            "acquired_utc",
            "frp_mw",
        }
        seen = {(r["source"], r["latitude"]) for r in page1["records"] + page2["records"]}
        assert len(seen) == 6
    # Later pages are served from the response cache: one FIRMS call per source.
    assert viirs.call_count == 1 and modis.call_count == 1


@pytest.mark.req("FR-DATA-005")
async def test_sort_orders_and_field_selection() -> None:
    with respx.mock() as router:
        mock_two_sources(router)
        oldest = await call({**TWO_SOURCES, "sort": "oldest", "fields": ["confidence"]})
        by_frp = await call({**TWO_SOURCES, "sort": "frp"})
    times = [r["acquired_utc"] for r in oldest["records"]]
    assert times == sorted(times)
    assert set(oldest["records"][0]) == {
        "source",
        "latitude",
        "longitude",
        "acquired_utc",
        "confidence",
    }
    frp = [r.get("frp_mw") for r in by_frp["records"]]
    assert frp[:5] == sorted(frp[:5], reverse=True) and frp[-1] is None  # missing FRP last


@pytest.mark.req("FR-DATA-005")
async def test_invalid_and_expired_cursors() -> None:
    with respx.mock(assert_all_called=True) as router:
        bad = await call({**TWO_SOURCES, "cursor": "not-a-cursor"})
        assert bad["error_code"] == "invalid_cursor"
        router.get(area_url("MODIS_NRT", date=None)).respond(200, text=firms_csv.MODIS_NRT)
        recent = {"area": LA, "sources": ["MODIS_NRT"], "limit": 1}
        first = await call(recent)
        tomorrow = make_services(map_key=MAP_KEY, now=NOW + dt.timedelta(days=1))
        expired = await call({**recent, "cursor": first["next_cursor"]}, tomorrow)
    assert expired["error_code"] == "cursor_expired"


@pytest.mark.req("NFR-004")
async def test_page_size_is_bounded_and_zero_gives_summaries_only() -> None:
    too_big = await call({**TWO_SOURCES, "limit": 501})
    assert too_big["error_code"] == "invalid_request" and "limit" in too_big["error_message"]
    with respx.mock() as router:
        mock_two_sources(router)
        summaries_only = await call({**TWO_SOURCES, "limit": 0})
    assert summaries_only["returned"] == 0 and summaries_only["records"] == []
    assert summaries_only["total_records"] == 6 and "next_cursor" not in summaries_only


@pytest.mark.req("FR-DATA-014")
async def test_confidence_filter_applies_only_on_request_and_reports_counts() -> None:
    with respx.mock() as router:
        mock_two_sources(router)
        unfiltered = await call(TWO_SOURCES)
        filtered = await call({**TWO_SOURCES, "min_confidence": "high"})
    assert unfiltered["total_records"] == 6
    assert all("confidence_filter" not in s for s in unfiltered["by_source"])
    assert filtered["total_records"] == 2
    by_source = {s["source"]: s for s in filtered["by_source"]}
    assert by_source["VIIRS_NOAA20_NRT"]["confidence_filter"] == {
        "min_confidence": "high",
        "kept": 1,
        "removed": 2,
        "removed_unclassified": 0,
    }
    assert by_source["MODIS_NRT"]["confidence_filter"]["kept"] == 1  # 85 % is high (Table 11)
    # Summaries still describe everything FIRMS returned.
    assert by_source["MODIS_NRT"]["summary"]["detections"] == 3
    assert any("confidence filter was applied" in n for n in filtered["notes"])


@pytest.mark.req("FR-DATA-002")
@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        ({"area": {**LA, "west": -117.0}}, "west must be less than east"),
        ({"area": LA, "date": "2026-10-11"}, "in the future"),
        ({"area": LA, "day_range": 6}, "day_range"),
        ({"area": LA, "sources": ["VIIRS_J1_NRT"]}, "unknown FIRMS source"),
        ({"area": LA, "fields": ["colour"]}, "Unknown record field"),
        ({"area": LA, "map_key": MAP_KEY}, "Extra inputs are not permitted"),
    ],
)
async def test_invalid_requests_never_reach_firms(arguments: dict, message: str) -> None:
    with respx.mock(assert_all_called=False) as router:
        route = router.route(host="firms.test")
        result = await call(arguments)
    assert result["status"] == "error" and result["error_code"] == "invalid_request"
    assert message in result["error_message"]
    assert route.call_count == 0
    assert MAP_KEY not in json.dumps(result)


async def test_partial_failure_reports_the_failed_source() -> None:
    services = make_services(map_key=MAP_KEY, FIRMS_MCP_HTTP_RETRIES=0)
    with respx.mock() as router:
        router.get(area_url("VIIRS_NOAA20_NRT")).respond(200, text=firms_csv.VIIRS_NOAA20_NRT)
        router.get(area_url("MODIS_NRT")).respond(503, text="Service unavailable")
        result = await call(TWO_SOURCES, services)
    assert result["status"] == "success" and result["total_records"] == 3
    failed = next(s for s in result["by_source"] if s["source"] == "MODIS_NRT")
    assert failed["status"] == "error" and failed["error_code"] == "upstream_unavailable"
    assert any("Some sources failed" in n for n in result["notes"])


@pytest.mark.req("FR-DATA-007")
async def test_invalid_key_fails_the_whole_call_with_remediation() -> None:
    with respx.mock() as router:
        router.get(area_url("VIIRS_NOAA20_NRT")).respond(400, text="Invalid MAP_KEY.")
        router.get(area_url("MODIS_NRT")).respond(400, text="Invalid MAP_KEY.")
        result = await call(TWO_SOURCES)
    assert result["status"] == "error" and result["error_code"] == "invalid_map_key"
    assert "map_key" in result["remediation"].lower()


@pytest.mark.req("FR-DATA-006")
async def test_no_detections_still_carries_caveats_disclaimer_and_link() -> None:
    with respx.mock() as router:
        router.get(area_url("VIIRS_NOAA20_NRT")).respond(200, text=firms_csv.HEADER_ONLY)
        router.get(area_url("MODIS_NRT")).respond(200, text=firms_csv.HEADER_ONLY)
        result = await call(TWO_SOURCES)
    assert result["status"] == "no_results" and result["total_records"] == 0
    caveat_ids = [c["id"] for c in result["caveats"]]
    assert "faq.caveats.how-do-i-know-if-a-fire-detection-was-missed-due-to-cloud-or" in caveat_ids
    assert result["disclaimer"]["text"] and result["citation"]["text"] and result["map_link"]["url"]


@pytest.mark.req("FR-DATA-001", "FR-MAP-003")
async def test_recent_days_window_and_map_dates() -> None:
    with respx.mock(assert_all_called=True) as router:
        router.get(area_url("MODIS_NRT", date=None)).respond(200, text=firms_csv.MODIS_NRT)
        router.get(area_url("MODIS_NRT", days=3, date=None)).respond(200, text=firms_csv.MODIS_NRT)
        today = await call({"area": LA, "sources": ["MODIS_NRT"]})
        three = await call({"area": LA, "sources": ["MODIS_NRT"], "day_range": 3})
    assert today["query"]["window_utc"] == {"start": "2026-10-10", "end": "2026-10-10"}
    assert ";d:today;" in today["map_link"]["url"]
    assert three["query"]["window_utc"] == {"start": "2026-10-08", "end": "2026-10-10"}
    assert ";d:2026-10-08..2026-10-10;" in three["map_link"]["url"]


async def test_world_queries_and_landsat_note() -> None:
    with respx.mock(assert_all_called=True) as router:
        router.get(area_url("LANDSAT_NRT", area="world", date=None)).respond(
            200, text=firms_csv.LANDSAT_NRT
        )
        result = await call({"area": "world", "sources": ["LANDSAT_NRT"]})
    assert result["status"] == "success"
    assert "i:" not in urlsplit(result["map_link"]["url"]).fragment
    assert any("US/Canada only" in n for n in result["notes"])


@pytest.mark.req("FR-AUTH-001", "FR-AUTH-010")
async def test_which_key_is_used() -> None:
    with respx.mock() as router:
        router.get(area_url("MODIS_NRT")).respond(200, text=firms_csv.MODIS_NRT)
        args = {"area": LA, "date": DAY, "sources": ["MODIS_NRT"]}
        local = await call(args, make_services(map_key=MAP_KEY))
        no_key = await call(args, make_services())
        remote_default = await call(
            args, make_services(map_key=MAP_KEY, mode=CredentialMode.REMOTE)
        )
        remote_operator = await call(
            args,
            make_services(
                map_key=MAP_KEY, mode=CredentialMode.REMOTE, FIRMS_MCP_ALLOW_OPERATOR_KEY=True
            ),
        )
        malformed = await call(args, make_services(map_key="not-a-key"))
    assert local["status"] == "success"
    assert no_key["error_code"] == "auth_required"
    assert "never ask the user to paste" in no_key["remediation"].lower()
    # Remote deployments ignore the operator's key unless explicitly allowed (OD-04).
    assert remote_default["error_code"] == "auth_required"
    assert remote_operator["status"] == "success"
    assert malformed["error_code"] == "invalid_map_key"
    assert "not-a-key" not in json.dumps(malformed)
