---
id: faq.getting-started.what-active-fire-data-and-imagery-are-available-in-firms-global
title: What active fire data and imagery are available in FIRMS Global?
kind: faq
section: getting-started
section_title: Getting Started
source: firms-faq
source_url: https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-124369-1
retrieved: '2026-10-09'
content_sha256: 53eb1717195fd773172a3f7b9ecedbd8105576888e5bd492e6876d30ea5d6a9d
order: 1
tags: []
related:
- faq.acronyms.overview
status: current
---

*Additional higher spatial and temporal resolution data and imagery are available for the USA and Canada. See the table in the [FIRMS US/Canada FAQ](https://www.earthdata.nasa.gov/data/tools/firms/faq#us-canada) section below.

| Product | Instrument (Platform) | Source | Spatial Resolution | Latency<sup>4</sup> (Coverage) |
|---|---|---|---|---|
| Polar orbiting Active Fire Detections | MODIS (Terra/Aqua) | [NASA LANCE](https://www.earthdata.nasa.gov/data/projects/lance) | 1km | <3 hours (Global) |
| Polar orbiting Active Fire Detections | VIIRS (Suomi NPP/NOAA-20/NOAA-21) | [NASA LANCE](https://www.earthdata.nasa.gov/data/projects/lance) | 375m | <3 hours (Global) |
| Polar orbiting Active Fire Detections | MODIS (Terra/Aqua) | [SSEC Univ of Wisconsin](https://www.ssec.wisc.edu/) | 1km | <1-30 mins (US-Canada) |
| Polar orbiting Active Fire Detections | VIIRS (Suomi NPP/NOAA-20/NOAA-21) | [SSEC Univ of Wisconsin](https://www.ssec.wisc.edu/) | 375m | <1-30 mins (US-Canada) |
| Polar orbiting Active Fire Detections | OLI (Landsat 8 & 9) | [USGS EROS](https://www.usgs.gov/centers/eros)<sup>5</sup> | 30m | 30-60 mins (US-Canada) |
| Provisional Geostationary Active Fire Detections | ABI (GOES-16 & 19)<sup>1</sup> | [NOAA](https://www.class.noaa.gov/) | 2km sub-satellite<sup>2</sup> | ~20-30 mins (Americas) |
| Provisional Geostationary Active Fire Detections | ABI (GOES-16 & 19)<sup>3</sup> | [CAMS](https://atmosphere.copernicus.eu/)/[IPMA](https://www.ipma.pt/en/index.html) | 2km sub-satellite<sup>2</sup> | ~20-30 mins (Americas) |
| Provisional Geostationary Active Fire Detections | SEVIRI (Meteosat 9 & 11)<sup>3</sup> | [EUMETSAT/LSA SAF](https://landsaf.ipma.pt/en/) | 2km sub-satellite<sup>2</sup> | ~30 mins (Europe-Africa-India) |
| Provisional Geostationary Active Fire Detections | AHI (Himawari-9)<sup>3</sup> | [CAMS](https://atmosphere.copernicus.eu/)/[IPMA](https://www.ipma.pt/en/index.html) | 2km sub-satellite<sup>2</sup> | ~30 mins (Australia-Asia) |
| True/False Color Composite Imagery | ABI (GOES-16 & 19) | [NASA GIBS](https://www.earthdata.nasa.gov/engage/open-data-services-software/earthdata-developer-portal/gibs-api) | 1km | 40 mins (Americas) |
| True/False Color Composite Imagery | MODIS (Terra/Aqua) | [NASA GIBS](https://www.earthdata.nasa.gov/engage/open-data-services-software/earthdata-developer-portal/gibs-api) | 250m | <3 hours (Global) |
| True/False Color Composite Imagery | VIIRS (Suomi NPP/NOAA-20) | [NASA GIBS](https://www.earthdata.nasa.gov/engage/open-data-services-software/earthdata-developer-portal/gibs-api) | 250m | <3 hours (Global) |
| True/False Color Composite Imagery | OLI (Landsat 8 & 9) / MSI (Sentinel 2A, 2B & 2C) | [NASA/IMPACT](https://www.earthdata.nasa.gov/about/impact)/[HLS](https://hls.gsfc.nasa.gov/) | 30m | 2-4 days (Global) |
| HLS Vegetation Indices: Normalized Difference Vegetation Index (NDVI), Normalized Difference Moisture Index (NDMI), Normalized Burn Ratio (NBR) & Normalized Burn Ratio 2 (NBR2) | OLI (Landsat 8 & 9) / MSI (Sentinel 2A, 2B & 2C) | [NASA IMPACT](https://www.earthdata.nasa.gov/node/12593)/[HLS](https://hls.gsfc.nasa.gov/) | 30m | 2-4 days (Global) |
| Aerosol Index | OMPS (Suomi NPP) | [NASA LANCE](https://www.earthdata.nasa.gov/data/projects/lance)/[GIBS](https://www.earthdata.nasa.gov/engage/open-data-services-software/earthdata-developer-portal/gibs-api) | ~50km | <3 hours (Global) |
| Aerosol Index PyroCumuloNimbus | OMPS (Suomi NPP) | [NASA LANCE](https://www.earthdata.nasa.gov/data/projects/lance)/[GIBS](https://www.earthdata.nasa.gov/engage/open-data-services-software/earthdata-developer-portal/gibs-api) | ~50km | <3 hours (Global) |
| Burned Area | MODIS (Terra/Aqua) | [NASA](https://modis-fire.umd.edu/ba.html) | 500m | ~3 months (Global) |

<sup>1</sup>FDC: Fire Detection and Characterization algorithm\
<sup>2</sup>The pixel size systematically grows from sub-satellite towards the edge of the disk\
<sup>3</sup>FRPPIXEL: Fire Radiative Power algorithm\
<sup>4</sup>Latency refers to the estimated time from satellite observation to availability in FIRMS\
<sup>5</sup>Currently curated for FIRMS US/Canada

See the [Acronyms section](https://www.earthdata.nasa.gov/data/tools/firms/faq#acronyms) at the bottom of this page for definitions.
