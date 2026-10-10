"""Areas, the source catalog, and KML links (FR-DATA-002, FR-DATA-010, FR-DATA-011)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from firms_mcp.firms.geo import BoundingBox, parse_area
from firms_mcp.firms.kml import LANDSAT_REGIONS, REGIONS, kml_footprint_link
from firms_mcp.firms.sources import DEFAULT_SOURCES, SOURCES, get_source
from firms_mcp.knowledge import default_knowledge_dir, load_knowledge_base


@pytest.mark.req("FR-DATA-002")
@pytest.mark.parametrize(
    "box",
    [
        {"west": -181, "south": 0, "east": 0, "north": 1},
        {"west": 0, "south": -91, "east": 1, "north": 1},
        {"west": 10, "south": 0, "east": 5, "north": 1},  # west >= east (antimeridian)
        {"west": 0, "south": 5, "east": 1, "north": 5},
    ],
)
def test_invalid_boxes_are_rejected(box: dict) -> None:
    with pytest.raises(ValidationError):
        BoundingBox(**box)


@pytest.mark.req("FR-DATA-001", "FR-DATA-002")
def test_area_formats() -> None:
    assert BoundingBox.world().to_api() == "world"
    assert parse_area("World").is_world
    box = parse_area("-119.2, 33.8, -117.6, 34.6")
    assert box.to_api() == "-119.2,33.8,-117.6,34.6"
    assert (
        BoundingBox(west=-120.0, south=30.0, east=-110.0, north=40.0).to_api() == "-120,30,-110,40"
    )
    assert box.center == pytest.approx((-118.4, 34.2))
    with pytest.raises(ValueError):
        parse_area("north")
    with pytest.raises(ValueError):
        parse_area("a,b,c,d")


def test_box_around_points_and_zoom() -> None:
    assert BoundingBox.around([]) is None
    single = BoundingBox.around([(10.0, 20.0)])
    assert single is not None and single.contains(10.0, 20.0)
    small = BoundingBox(west=-119.2, south=33.8, east=-117.6, north=34.6)
    assert 7 <= small.approximate_zoom() <= 9
    assert BoundingBox.world().approximate_zoom() == 2.0


@pytest.mark.req("FR-DATA-010")
def test_catalog_matches_the_firms_area_api_source_list() -> None:
    # The eight SOURCE values listed on the FIRMS area-API page (2026-10-09).
    assert set(SOURCES) == {
        "LANDSAT_NRT",
        "MODIS_NRT",
        "MODIS_SP",
        "VIIRS_NOAA20_NRT",
        "VIIRS_NOAA20_SP",
        "VIIRS_NOAA21_NRT",
        "VIIRS_SNPP_NRT",
        "VIIRS_SNPP_SP",
    }
    assert set(DEFAULT_SOURCES) <= set(SOURCES)
    assert all(
        SOURCES[s].processing == "NRT" and SOURCES[s].coverage == "Global" for s in DEFAULT_SOURCES
    )
    assert get_source("viirs_snpp_nrt").id == "VIIRS_SNPP_NRT"
    with pytest.raises(ValueError, match="valid sources"):
        get_source("GOES_NRT")


@pytest.mark.req("FR-DATA-010")
def test_catalog_entries_are_consistent() -> None:
    kb = load_knowledge_base([default_knowledge_dir()])
    for source in SOURCES.values():
        assert source.map_layers and all(layer.startswith("fires_") for layer in source.map_layers)
        assert source.nominal_resolution_m in (30, 375, 1000)
        for entry_id in source.knowledge_entries:
            assert kb.get(entry_id) is not None, (source.id, entry_id)
    assert SOURCES["LANDSAT_NRT"].coverage.startswith("US/Canada")


@pytest.mark.req("FR-DATA-011")
def test_kml_links() -> None:
    link = kml_footprint_link("canada", "24h", "c6.1")
    assert link.url == (
        "https://firms.modaps.eosdis.nasa.gov/api/kml_fire_footprints/"
        "?region=canada&date_span=24h&sensor=c6.1"
    )
    assert link.region_label == "Canada" and link.period_label == "24 hours"
    assert len(REGIONS) == 12
    for region in LANDSAT_REGIONS:
        assert kml_footprint_link(region, "7d", "landsat").sensor == "landsat"


@pytest.mark.req("FR-DATA-011")
@pytest.mark.parametrize(
    ("region", "period", "sensor", "message"),
    [
        ("europe", "24h", "landsat", "Landsat"),
        ("mars", "24h", "c6.1", "region"),
        ("europe", "1y", "c6.1", "period"),
        ("europe", "24h", "goes", "sensor"),
    ],
)
def test_invalid_kml_requests(region: str, period: str, sensor: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        kml_footprint_link(region, period, sensor)
