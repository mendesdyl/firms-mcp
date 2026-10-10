"""FIRMS KML fire-footprint download links (FR-DATA-011).

From the FIRMS ``kml_fire_footprints`` API page (2026-10-09): no MAP_KEY; regions,
periods, and sensors below; Landsat only for Canada and the contiguous US + Hawaii.
Footprint colors indicate time since detection (0-<6 h, 6-<12 h, 12-<24 h, 24 h+).
"""

from __future__ import annotations

from typing import Literal
from urllib.parse import urlencode

from pydantic import BaseModel

REGIONS: dict[str, str] = {
    "canada": "Canada",
    "alaska": "Alaska",
    "usa_contiguous_and_hawaii": "USA (Conterminous) and Hawaii",
    "central_america": "Central America",
    "south_america": "South America",
    "europe": "Europe",
    "northern_and_central_africa": "Northern and Central Africa",
    "southern_africa": "Southern Africa",
    "russia_asia": "Russia and Asia",
    "south_asia": "South Asia",
    "southeast_asia": "South East Asia",
    "australia_newzealand": "Australia and New Zealand",
}
PERIODS: dict[str, str] = {"24h": "24 hours", "48h": "48 hours", "72h": "72 hours", "7d": "7 days"}
SENSORS: dict[str, str] = {
    "c6.1": "MODIS (NRT, RT, URT)",
    "suomi-npp-viirs-c2": "VIIRS Suomi NPP",
    "noaa-20-viirs-c2": "VIIRS NOAA-20",
    "noaa-21-viirs-c2": "VIIRS NOAA-21",
    "landsat": "Landsat",
}
LANDSAT_REGIONS = frozenset({"canada", "usa_contiguous_and_hawaii"})

Region = Literal[
    "canada",
    "alaska",
    "usa_contiguous_and_hawaii",
    "central_america",
    "south_america",
    "europe",
    "northern_and_central_africa",
    "southern_africa",
    "russia_asia",
    "south_asia",
    "southeast_asia",
    "australia_newzealand",
]
Period = Literal["24h", "48h", "72h", "7d"]
Sensor = Literal["c6.1", "suomi-npp-viirs-c2", "noaa-20-viirs-c2", "noaa-21-viirs-c2", "landsat"]


class KmlLink(BaseModel):
    region: str
    region_label: str
    period: str
    period_label: str
    sensor: str
    sensor_label: str
    url: str


def kml_footprint_link(
    region: str, period: str, sensor: str, base_url: str = "https://firms.modaps.eosdis.nasa.gov"
) -> KmlLink:
    if region not in REGIONS:
        raise ValueError(f"unknown region {region!r}; valid: {', '.join(REGIONS)}")
    if period not in PERIODS:
        raise ValueError(f"unknown period {period!r}; valid: {', '.join(PERIODS)}")
    if sensor not in SENSORS:
        raise ValueError(f"unknown sensor {sensor!r}; valid: {', '.join(SENSORS)}")
    if sensor == "landsat" and region not in LANDSAT_REGIONS:
        raise ValueError(
            "Landsat footprints are only offered for 'canada' and 'usa_contiguous_and_hawaii'"
        )
    query = urlencode({"region": region, "date_span": period, "sensor": sensor})
    return KmlLink(
        region=region,
        region_label=REGIONS[region],
        period=period,
        period_label=PERIODS[period],
        sensor=sensor,
        sensor_label=SENSORS[sensor],
        url=f"{base_url.rstrip('/')}/api/kml_fire_footprints/?{query}",
    )
