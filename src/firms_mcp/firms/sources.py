"""Catalog of FIRMS active-fire detection sources (FR-DATA-010).

Facts come from the FIRMS area-API page, the FIRMS FAQ, the attribute pages, and the
FIRMS Fire Map configuration, all retrieved 2026-10-09 (docs/science/DATA_PRODUCTS.md).
Knowledge-base entry IDs point the agent to FIRMS's own wording for each source.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Family = Literal["viirs", "modis", "landsat"]
Processing = Literal["NRT", "SP"]


@dataclass(frozen=True)
class FireSource:
    id: str
    """FIRMS area-API ``SOURCE`` value."""
    label: str
    """FIRMS's own display name on the area-API page."""
    family: Family
    instrument: str
    platforms: tuple[str, ...]
    processing: Processing
    processing_note: str
    nominal_resolution_m: int
    coverage: str
    map_layers: tuple[str, ...]
    """FIRMS Fire Map layer IDs (Advanced mode) that display this source."""
    map_dates_key: str
    """Key in FIRMS's public map date service (/api/map_dates/)."""
    kml_sensor: str | None
    """``sensor`` value of the KML fire-footprint service, if offered."""
    record_start_per_faq: str | None
    knowledge_entries: tuple[str, ...]


_VIIRS_KNOWLEDGE = (
    "faq.viirs.what-is-the-viirs-375-m-active-fire-product",
    "faq.getting-started.what-does-a-fire-detection-mean-on-the-ground",
    "faq.getting-started.what-is-the-detection-confidence",
    "supplement.data-attributes.modis-viirs-nrt",
)
_MODIS_KNOWLEDGE = (
    "faq.modis.what-does-a-modis-active-fire-detection-mean-on-the-ground",
    "faq.getting-started.what-is-the-detection-confidence",
    "faq.modis.what-size-fires-can-be-detected",
    "supplement.data-attributes.modis-viirs-nrt",
)
_LANDSAT_KNOWLEDGE = (
    "faq.landsat.what-is-the-landsat-fire-and-thermal-anomalies-product",
    "faq.landsat.what-are-the-attributes-of-the-landsat-fire-data",
    "faq.landsat.why-are-landsat-fire-data-only-available-for-north-america",
)
_NRT_NOTE = (
    "Near real-time, including real-time (RT) and ultra real-time (URT) detections that "
    "are replaced when NRT arrives (RT/URT removed after NRT processing or after 6 hours)"
)
_SP_NOTE = "Standard (science-quality) processing, available months after observation"

SOURCES: dict[str, FireSource] = {
    s.id: s
    for s in (
        FireSource(
            id="VIIRS_SNPP_NRT",
            label="VIIRS S-NPP (URT+NRT)",
            family="viirs",
            instrument="VIIRS",
            platforms=("Suomi NPP",),
            processing="NRT",
            processing_note=_NRT_NOTE,
            nominal_resolution_m=375,
            coverage="Global",
            map_layers=("fires_viirs_snpp",),
            map_dates_key="suomi_viirs_c2_nrt",
            kml_sensor="suomi-npp-viirs-c2",
            record_start_per_faq="2012-01-20 (VIIRS S-NPP, all processing levels)",
            knowledge_entries=_VIIRS_KNOWLEDGE,
        ),
        FireSource(
            id="VIIRS_NOAA20_NRT",
            label="VIIRS NOAA-20 (URT+NRT)",
            family="viirs",
            instrument="VIIRS",
            platforms=("NOAA-20",),
            processing="NRT",
            processing_note=_NRT_NOTE,
            nominal_resolution_m=375,
            coverage="Global",
            map_layers=("fires_viirs_noaa20",),
            map_dates_key="jpss1_viirs_c2_nrt",
            kml_sensor="noaa-20-viirs-c2",
            record_start_per_faq="2020-01-01 (VIIRS NOAA-20)",
            knowledge_entries=_VIIRS_KNOWLEDGE,
        ),
        FireSource(
            id="VIIRS_NOAA21_NRT",
            label="VIIRS NOAA-21 (URT+NRT)",
            family="viirs",
            instrument="VIIRS",
            platforms=("NOAA-21",),
            processing="NRT",
            processing_note=_NRT_NOTE,
            nominal_resolution_m=375,
            coverage="Global",
            map_layers=("fires_viirs_noaa21",),
            map_dates_key="jpss2_viirs_c2_nrt",
            kml_sensor="noaa-21-viirs-c2",
            record_start_per_faq="2024-01-17 (VIIRS NOAA-21)",
            knowledge_entries=_VIIRS_KNOWLEDGE,
        ),
        FireSource(
            id="MODIS_NRT",
            label="MODIS (URT+NRT)",
            family="modis",
            instrument="MODIS",
            platforms=("Terra", "Aqua"),
            processing="NRT",
            processing_note=_NRT_NOTE,
            nominal_resolution_m=1000,
            coverage="Global",
            map_layers=("fires_modis_terra", "fires_modis_aqua"),
            map_dates_key="modis_nrt",
            kml_sensor="c6.1",
            record_start_per_faq="Terra November 2000; Aqua July 2002 (all processing levels)",
            knowledge_entries=_MODIS_KNOWLEDGE,
        ),
        FireSource(
            id="LANDSAT_NRT",
            label="LANDSAT (NRT) [US/Canada only]",
            family="landsat",
            instrument="OLI",
            platforms=("Landsat 8", "Landsat 9"),
            processing="NRT",
            processing_note=_NRT_NOTE,
            nominal_resolution_m=30,
            coverage=(
                "US/Canada only (most of North America: CONUS, southern Canada, northern Mexico)"
            ),
            map_layers=("fires_landsat_landsat",),
            map_dates_key="landsat_nrt",
            kml_sensor="landsat",
            record_start_per_faq="June 2022",
            knowledge_entries=_LANDSAT_KNOWLEDGE,
        ),
        FireSource(
            id="VIIRS_SNPP_SP",
            label="VIIRS S-NPP (SP)",
            family="viirs",
            instrument="VIIRS",
            platforms=("Suomi NPP",),
            processing="SP",
            processing_note=_SP_NOTE,
            nominal_resolution_m=375,
            coverage="Global",
            map_layers=("fires_viirs_snpp_sp",),
            map_dates_key="suomi_viirs_c2_sp",
            kml_sensor=None,
            record_start_per_faq="2012-01-20",
            knowledge_entries=(
                *_VIIRS_KNOWLEDGE,
                "faq.getting-started.what-are-the-key-differences-between-urt-rt-nrt-and-standard",
            ),
        ),
        FireSource(
            id="VIIRS_NOAA20_SP",
            label="VIIRS NOAA-20 (SP)",
            family="viirs",
            instrument="VIIRS",
            platforms=("NOAA-20",),
            processing="SP",
            processing_note=_SP_NOTE,
            nominal_resolution_m=375,
            coverage="Global",
            map_layers=("fires_viirs_noaa20_sp",),
            map_dates_key="jpss1_viirs_c2",
            kml_sensor=None,
            record_start_per_faq="2020-01-01 (map date service reports 2018-04-01)",
            knowledge_entries=(
                *_VIIRS_KNOWLEDGE,
                "faq.getting-started.what-are-the-key-differences-between-urt-rt-nrt-and-standard",
            ),
        ),
        FireSource(
            id="MODIS_SP",
            label="MODIS (SP)",
            family="modis",
            instrument="MODIS",
            platforms=("Terra", "Aqua"),
            processing="SP",
            processing_note=_SP_NOTE + " (MCD14ML, University of Maryland; 2-3 month lag)",
            nominal_resolution_m=1000,
            coverage="Global",
            map_layers=("fires_modis_terra_sp", "fires_modis_aqua_sp"),
            map_dates_key="modis_v6",
            kml_sensor=None,
            record_start_per_faq="Terra November 2000; Aqua July 2002",
            knowledge_entries=(
                *_MODIS_KNOWLEDGE,
                "faq.getting-started.what-are-the-different-sources-of-modis-and-viirs-active-fire",
            ),
        ),
    )
}

DEFAULT_SOURCES: tuple[str, ...] = (
    "VIIRS_NOAA20_NRT",
    "VIIRS_NOAA21_NRT",
    "VIIRS_SNPP_NRT",
    "MODIS_NRT",
)
"""Global near-real-time sources queried when the caller does not choose (ADR-0007)."""

AVAILABILITY_SENSORS: tuple[str, ...] = ("ALL", *SOURCES)


def get_source(source_id: str) -> FireSource:
    try:
        return SOURCES[source_id.upper()]
    except KeyError as exc:
        valid = ", ".join(SOURCES)
        raise ValueError(f"unknown FIRMS source {source_id!r}; valid sources: {valid}") from exc
