"""FIRMS Fire Map deep links (FR-MAP-001 … FR-MAP-006; ADR-0006).

``parse_like_firms_map`` mirrors the map application's own hash parser (``parse()`` in
firms_map.927094f8.js, 2026-10-09): split on '@' for the location, split the rest on ';',
then 'key:value' segments. Links are checked against that rule set, and the expected
URLs below were each verified with a cold load in the real map (docs/research/REFERENCES.md §5).
"""

from __future__ import annotations

import datetime as dt
from urllib.parse import urlsplit

import pytest

from firms_mcp.firms.geo import BoundingBox
from firms_mcp.firms.sources import SOURCES
from firms_mcp.maplinks import MapLinkError, build_fire_map_link, load_catalog

TODAY = dt.date(2026, 10, 10)
LA = BoundingBox(west=-119.2, south=33.8, east=-117.6, north=34.6)


def parse_like_firms_map(url: str) -> dict:
    fragment = urlsplit(url).fragment
    head, _, location = fragment.partition("@")
    result: dict = {"location": None}
    if location:
        lon, lat, zoom = location.split(",")
        assert zoom.endswith("z")
        result["location"] = (float(lon), float(lat), float(zoom[:-1]))
    for segment in filter(None, head.split(";")):
        key, sep, value = segment.partition(":")
        assert sep, f"segment without ':' {segment!r}"
        result[key] = value
    return result


@pytest.mark.req("FR-MAP-001", "FR-MAP-003")
def test_detection_query_reproduced_as_a_link_verified_in_the_real_map() -> None:
    link = build_fire_map_link(
        area=LA,
        start_date=dt.date(2025, 1, 7),
        end_date=dt.date(2025, 1, 9),
        sources=["VIIRS_NOAA20_NRT", "VIIRS_SNPP_NRT"],
        basemap="street",
        today=TODAY,
    )
    assert link.url == (
        "https://firms.modaps.eosdis.nasa.gov/map/?utm_source=firms-mcp&utm_medium=mcp"
        "#m:advanced;d:2025-01-07..2025-01-09;"
        "l:fires_viirs_noaa20,fires_viirs_snpp,country-outline,street;"
        "i:-119.2,33.8,-117.6,34.6"
    )
    parsed = parse_like_firms_map(link.url)
    assert parsed["m"] == "advanced" and parsed["d"] == "2025-01-07..2025-01-09"
    assert parsed["i"] == "-119.2,33.8,-117.6,34.6" and parsed["location"] is None


@pytest.mark.req("FR-MAP-001")
def test_default_view_matches_the_maps_own_defaults() -> None:
    link = build_fire_map_link(center=(-118.5, 34.1), zoom=7, referral=False)
    assert link.url == (
        "https://firms.modaps.eosdis.nasa.gov/map/"
        "#d:24hrs;l:fires_all,country-outline,earth;@-118.5,34.1,7.0z"
    )
    assert link.mode == "basic" and "m" not in parse_like_firms_map(link.url)
    assert parse_like_firms_map(link.url)["location"] == (-118.5, 34.1, 7.0)


@pytest.mark.req("FR-MAP-001")
@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"period": "7days"}, "7days"),
        ({"period": "today"}, "today"),
        ({"start_date": dt.date(2025, 1, 8)}, "2025-01-08"),
        ({"end_date": dt.date(2025, 1, 8)}, "2025-01-08"),
        ({"start_date": dt.date(2025, 1, 8), "end_date": dt.date(2025, 1, 8)}, "2025-01-08"),
        ({}, "24hrs"),
    ],
)
def test_date_segments(kwargs: dict, expected: str) -> None:
    link = build_fire_map_link(today=TODAY, **kwargs)
    assert parse_like_firms_map(link.url)["d"] == expected == link.dates


@pytest.mark.req("FR-MAP-001")
@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"period": "30days"}, "period must be one of"),
        ({"period": "24hrs", "start_date": dt.date(2025, 1, 1)}, "not both"),
        ({"start_date": dt.date(2025, 1, 9), "end_date": dt.date(2025, 1, 7)}, "after end"),
        ({"start_date": dt.date(2026, 10, 11)}, "future"),
        ({"area": LA, "center": (0.0, 0.0)}, "not both"),
        ({"center": (200.0, 0.0)}, "valid ranges"),
        ({"center": (0.0, 0.0), "zoom": 17}, "zoom must be between 1 and 16"),
        ({"mode": "downloads"}, "mode must be one of"),
        ({"sources": ["GOES_NRT"]}, "unknown FIRMS source"),
    ],
)
def test_invalid_requests_are_explained(kwargs: dict, message: str) -> None:
    with pytest.raises(MapLinkError, match=message):
        build_fire_map_link(today=TODAY, **kwargs)


@pytest.mark.req("FR-MAP-002")
def test_layers_are_validated_against_the_mode() -> None:
    with pytest.raises(MapLinkError, match="need mode 'advanced'"):
        build_fire_map_link(mode="basic", extra_layers=["fires_viirs_snpp"])
    with pytest.raises(MapLinkError, match="unknown Fire Map layer"):
        build_fire_map_link(extra_layers=["fires_goes_g99"])
    with pytest.raises(MapLinkError, match="not a basemap"):
        build_fire_map_link(basemap="country-outline")
    smoke = build_fire_map_link(
        sources=["VIIRS_SNPP_NRT"], mode="smoke", extra_layers=["snpp_omps_aerosol"]
    )
    assert smoke.layers[:2] == ["fires_viirs_snpp", "snpp_omps_aerosol"]


@pytest.mark.req("FR-MAP-002")
def test_a_basemap_is_always_present() -> None:
    for kwargs in ({}, {"sources": ["MODIS_NRT"]}, {"overlays": []}):
        link = build_fire_map_link(**kwargs)
        assert any(load_catalog().layers[layer]["category"] == "basemap" for layer in link.layers)


@pytest.mark.req("FR-MAP-003")
def test_every_api_source_maps_to_layers_available_in_advanced_mode() -> None:
    advanced = load_catalog().allowed_layers("advanced")
    for source in SOURCES.values():
        assert set(source.map_layers) <= advanced, source.id
        link = build_fire_map_link(sources=[source.id])
        assert link.mode == "advanced"
        assert link.layers[: len(source.map_layers)] == list(source.map_layers)


@pytest.mark.req("FR-MAP-004")
def test_us_canada_map_uses_the_same_grammar_and_its_zoom_limits() -> None:
    link = build_fire_map_link(map_name="us-canada", area=LA, sources=["LANDSAT_NRT"])
    assert link.url.startswith("https://firms.modaps.eosdis.nasa.gov/usfs/map/?")
    assert "l:fires_landsat_landsat,country-outline,earth" in link.url
    assert "US/Canada Fire Map" in link.description
    with pytest.raises(MapLinkError, match="between 4 and 16"):
        build_fire_map_link(map_name="us-canada", center=(-100.0, 40.0), zoom=3)


@pytest.mark.req("FR-MAP-005")
def test_referral_parameters_are_optional() -> None:
    assert "?utm_source=firms-mcp&utm_medium=mcp#" in build_fire_map_link().url
    assert "utm_" not in build_fire_map_link(referral=False).url


@pytest.mark.req("FR-MAP-006")
def test_description_tells_the_user_what_they_will_see() -> None:
    link = build_fire_map_link(
        area=LA, sources=["MODIS_NRT"], start_date=dt.date(2025, 1, 8), today=TODAY
    )
    text = link.description
    assert "Advanced Mode" in text
    assert "MODIS / Terra [1km]" in text and "MODIS / Aqua [1km]" in text
    assert "2025-01-08 (UTC)" in text
    assert "west -119.2, south 33.8, east -117.6, north 34.6" in text
    assert "Blue Marble" in text and "UTC" in text


def test_catalog_snapshot_is_complete() -> None:
    catalog = load_catalog()
    assert catalog.retrieved == "2026-10-09"
    assert len(catalog.layers) == 267
    assert {"basic", "advanced", "burned_area", "smoke", "experimental"} <= set(catalog.modes)
    assert "fires_all" in catalog.allowed_layers("basic")
    assert "fires_viirs_noaa21" not in catalog.allowed_layers("basic")
