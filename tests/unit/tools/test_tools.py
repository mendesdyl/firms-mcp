"""The knowledge, catalog, availability, key-status, link, and KML tools."""

from __future__ import annotations

import json
from urllib.parse import parse_qs, urlsplit

import pytest
import respx
from fastmcp import Client

from firms_mcp.firms.sources import DEFAULT_SOURCES, SOURCES
from firms_mcp.knowledge import KnowledgeBase
from tests.fixtures.firms_csv import MAP_KEY
from tests.fixtures.services import FIRMS_BASE, make_server, make_services, repo_knowledge

UTC_ENTRY = "faq.getting-started.what-is-utc"


async def call(name: str, arguments: dict, services=None) -> dict:
    async with Client(make_server(services or make_services())) as client:
        result = await client.call_tool(name, arguments, raise_on_error=False)
    return result.structured_content


# -- knowledge -------------------------------------------------------------------------


@pytest.mark.req("FR-KB-005", "FR-KB-001")
async def test_search_returns_full_verbatim_bodies() -> None:
    result = await call("search_knowledge", {"query": "what is UTC", "limit": 2})
    assert result["status"] == "success" and result["total"] == 2
    top = result["results"][0]
    entry = repo_knowledge().get(top["id"])
    assert top["id"] == UTC_ENTRY
    assert top["body"] == entry.body  # whole entry, verbatim
    assert top["source_url"] == entry.source_url and top["retrieved"] == "2026-10-09"
    assert top["content_sha256"] == entry.content_sha256


@pytest.mark.req("FR-KB-005")
async def test_search_sections_and_no_results() -> None:
    caveats = await call("search_knowledge", {"query": "false detections", "section": "caveats"})
    assert all(r["section"] == "caveats" for r in caveats["results"])
    unknown = await call("search_knowledge", {"query": "x", "section": "nope"})
    assert unknown["error_code"] == "invalid_request" and "caveats" in unknown["error_message"]
    nothing = await call("search_knowledge", {"query": "zzzzqqqq"})
    assert nothing["status"] == "no_results" and "list_knowledge_topics" in nothing["suggestion"]


@pytest.mark.req("FR-KB-006")
async def test_get_entries_by_id_with_suggestions_for_unknown_ids() -> None:
    result = await call(
        "get_knowledge_entry", {"entry_ids": [UTC_ENTRY, "faq.getting-started.what-is-gmt"]}
    )
    assert result["status"] == "success"
    assert [e["id"] for e in result["entries"]] == [UTC_ENTRY]
    assert result["not_found"][0]["id"] == "faq.getting-started.what-is-gmt"
    assert UTC_ENTRY in result["not_found"][0]["suggestions"]
    none = await call("get_knowledge_entry", {"entry_ids": ["nothing.here"]})
    assert none["status"] == "no_results"


@pytest.mark.req("FR-KB-009")
async def test_retired_entries_are_flagged_and_not_searched() -> None:
    base = repo_knowledge()
    retired = base.get(UTC_ENTRY).model_copy(update={"status": "retired"})
    knowledge = KnowledgeBase(entries={**base.entries, UTC_ENTRY: retired}, sources=base.sources)
    services = make_services(knowledge=knowledge)
    got = await call("get_knowledge_entry", {"entry_ids": [UTC_ENTRY]}, services)
    assert got["entries"][0]["status"] == "retired"
    assert "no longer publishes" in got["entries"][0]["notice"]
    services = make_services(knowledge=knowledge)
    search = await call("search_knowledge", {"query": "what is UTC", "limit": 10}, services)
    assert UTC_ENTRY not in [r["id"] for r in search["results"]]
    services = make_services(knowledge=knowledge)
    included = await call(
        "search_knowledge", {"query": "what is UTC", "include_retired": True}, services
    )
    assert included["results"][0]["id"] == UTC_ENTRY


@pytest.mark.req("FR-KB-007")
async def test_table_of_contents() -> None:
    knowledge = repo_knowledge()
    overview = await call("list_knowledge_topics", {})
    assert overview["total_entries"] == len(knowledge.ordered())
    assert all("entries" not in s for s in overview["sections"])
    assert {s["id"] for s in overview["sources"]} == set(knowledge.sources)
    caveats = await call("list_knowledge_topics", {"section": "caveats"})
    (section,) = caveats["sections"]
    assert section["entry_count"] == len(section["entries"]) > 0
    everything = await call("list_knowledge_topics", {"include_entries": True})
    assert sum(len(s["entries"]) for s in everything["sections"]) == len(knowledge.ordered())
    unknown = await call("list_knowledge_topics", {"section": "nope"})
    assert unknown["error_code"] == "invalid_request"


# -- catalog and availability ------------------------------------------------------------


@pytest.mark.req("FR-DATA-010")
async def test_source_catalog() -> None:
    result = await call("get_fire_data_sources", {})
    assert [s["id"] for s in result["sources"]] == list(SOURCES)
    assert result["default_sources"] == list(DEFAULT_SOURCES)
    by_id = {s["id"]: s for s in result["sources"]}
    assert by_id["VIIRS_NOAA20_NRT"]["default"] is True and by_id["MODIS_SP"]["default"] is False
    assert by_id["LANDSAT_NRT"]["nominal_resolution_m"] == 30
    for source in result["sources"]:
        assert source["knowledge_entries"], source["id"]
    one = await call("get_fire_data_sources", {"source_ids": ["modis_sp"]})
    assert [s["id"] for s in one["sources"]] == ["MODIS_SP"]
    bad = await call("get_fire_data_sources", {"source_ids": ["GOES"]})
    assert bad["error_code"] == "invalid_request"


@pytest.mark.req("FR-DATA-008")
async def test_availability_without_a_key_uses_the_map_date_service() -> None:
    with respx.mock(assert_all_called=True) as router:
        router.get(f"{FIRMS_BASE}/api/map_dates/").respond(
            200,
            json={
                "modis_v6": ["2000-11-01", "2026-07-31"],
                "jpss2_viirs_c2_nrt": ["2024-01-17", "2026-10-10"],
            },
        )
        result = await call("get_data_availability", {})
    assert result["method"] == "fire_map_date_service"
    assert {r["source"]: r["max_date"] for r in result["availability"]} == {
        "MODIS_SP": "2026-07-31",
        "VIIRS_NOAA21_NRT": "2026-10-10",
    }
    assert any("not a documented API" in n for n in result["notes"])


@pytest.mark.req("FR-DATA-008", "SEC-001")
async def test_availability_with_a_key_uses_the_documented_api() -> None:
    with respx.mock(assert_all_called=True) as router:
        router.get(f"{FIRMS_BASE}/api/data_availability/csv/{MAP_KEY}/MODIS_SP").respond(
            200, text="data_id,min_date,max_date\nMODIS_SP,2000-11-01,2026-07-31\n"
        )
        result = await call(
            "get_data_availability", {"source": "MODIS_SP"}, make_services(map_key=MAP_KEY)
        )
    assert result["method"] == "firms_api"
    assert result["availability"] == [
        {"source": "MODIS_SP", "min_date": "2000-11-01", "max_date": "2026-07-31", "extra": {}}
    ]
    assert result["request_url"].endswith("/api/data_availability/csv/[MAP_KEY]/MODIS_SP")
    assert MAP_KEY not in json.dumps(result)
    bad = await call("get_data_availability", {"source": "GOES"})
    assert bad["error_code"] == "invalid_request"


@pytest.mark.req("FR-DATA-009", "SEC-001")
async def test_map_key_status() -> None:
    with respx.mock(assert_all_called=True) as router:
        router.get(f"{FIRMS_BASE}/mapserver/mapkey_status/", params={"MAP_KEY": MAP_KEY}).respond(
            200,
            json={
                "transaction_limit": 5000,
                "current_transactions": 120,
                "transaction_interval": "10 minutes",
                "map_key": MAP_KEY,
            },
        )
        result = await call("get_map_key_status", {}, make_services(map_key=MAP_KEY))
    assert result["remaining"] == 4880 and result["transaction_interval"] == "10 minutes"
    assert result["server_budget"] == {"budget": 4500, "estimated_used": 0}
    assert MAP_KEY not in json.dumps(result)  # even when FIRMS echoes the key
    no_key = await call("get_map_key_status", {})
    assert no_key["error_code"] == "auth_required"


# -- links -----------------------------------------------------------------------------


@pytest.mark.req("FR-MAP-001", "FR-MAP-005", "FR-MAP-006")
async def test_fire_map_links() -> None:
    result = await call(
        "build_fire_map_link",
        {
            "area": {"west": -119.2, "south": 33.8, "east": -117.6, "north": 34.6},
            "start_date": "2025-01-07",
            "end_date": "2025-01-09",
            "sources": ["VIIRS_NOAA20_NRT", "VIIRS_SNPP_NRT"],
            "basemap": "street",
        },
    )
    link = result["link"]
    parts = urlsplit(link["url"])
    assert parts.path == "/map/"
    assert parse_qs(parts.query) == {"utm_source": ["firms-mcp"], "utm_medium": ["mcp"]}
    assert parts.fragment == (
        "m:advanced;d:2025-01-07..2025-01-09;"
        "l:fires_viirs_noaa20,fires_viirs_snpp,country-outline,street;i:-119.2,33.8,-117.6,34.6"
    )
    assert "2025-01-07 to 2025-01-09 (UTC)" in link["description"]
    no_referral = await call(
        "build_fire_map_link", {"period": "today"}, make_services(FIRMS_MCP_REFERRAL=False)
    )
    assert "utm_source" not in no_referral["link"]["url"]


@pytest.mark.req("FR-MAP-002", "FR-MAP-004")
async def test_fire_map_link_errors_and_us_canada_map() -> None:
    us = await call(
        "build_fire_map_link",
        {"center": {"longitude": -116.2, "latitude": 43.6}, "zoom": 6, "map": "us-canada"},
    )
    assert urlsplit(us["link"]["url"]).path == "/usfs/map/"
    low_zoom = await call(
        "build_fire_map_link",
        {"center": {"longitude": -116.2, "latitude": 43.6}, "zoom": 2, "map": "us-canada"},
    )
    assert low_zoom["error_code"] == "invalid_request" and "zoom" in low_zoom["error_message"]
    both = await call(
        "build_fire_map_link",
        {"period": "7days", "start_date": "2025-01-07"},
    )
    assert both["error_code"] == "invalid_request"
    unknown_layer = await call("build_fire_map_link", {"extra_layers": ["no_such_layer"]})
    assert "unknown Fire Map layer" in unknown_layer["error_message"]


@pytest.mark.req("FR-DATA-011")
async def test_kml_footprint_links() -> None:
    europe = await call("get_fire_footprint_kml_links", {"region": "europe", "period": "7d"})
    sensors = [link["sensor"] for link in europe["links"]]
    assert "landsat" not in sensors and len(sensors) == 4  # Landsat: Canada and USA only
    canada = await call("get_fire_footprint_kml_links", {"region": "canada"})
    assert [link["sensor"] for link in canada["links"]][-1] == "landsat"
    query = parse_qs(urlsplit(canada["links"][0]["url"]).query)
    assert query == {"region": ["canada"], "date_span": ["24h"], "sensor": ["c6.1"]}
    landsat_europe = await call(
        "get_fire_footprint_kml_links", {"region": "europe", "sensors": ["landsat"]}
    )
    assert landsat_europe["error_code"] == "invalid_request"
    assert europe["knowledge_entries"][0]["id"] == "supplement.api.kml-fire-footprints"
