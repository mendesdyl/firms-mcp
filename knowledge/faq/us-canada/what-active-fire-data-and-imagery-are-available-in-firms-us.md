---
id: faq.us-canada.what-active-fire-data-and-imagery-are-available-in-firms-us
title: What active fire data and imagery are available in FIRMS US/Canada?
kind: faq
section: us-canada
section_title: FIRMS US/Canada
source: firms-faq
source_url: https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-124627-2
retrieved: '2026-10-09'
content_sha256: 8fada8957d7c4339c82df60be1d54366822dd18a54610410d798878dbbcb6bf8
order: 109
tags: []
related:
- faq.getting-started.what-active-fire-data-and-imagery-are-available-in-firms-global
- faq.acronyms.overview
status: current
---

*Other data and imagery sources are available for global coverage. See the [FIRMS Global table](https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-124369-1) .

| Product | Sensor (Platform) | Source | Spatial Resolution | Latency<sup>4</sup> |
|---|---|---|---|---|
| Polar orbiting Active Fire Detections | MODIS (Terra/Aqua) | [SSEC Univ of Wisconsin](https://www.ssec.wisc.edu/) | 1km | <1-30 mins |
| Polar orbiting Active Fire Detections | VIIRS (Suomi NPP/NOAA-20/NOAA-21) | [SSEC Univ of Wisconsin](https://www.ssec.wisc.edu/) | 375m | <1-30 mins |
| Polar orbiting Active Fire Detections | MODIS (Terra/Aqua) | [NASA LANCE](https://www.earthdata.nasa.gov/data/instruments/modis/near-real-time-data) | 1km | <3 hours |
| Polar orbiting Active Fire Detections | VIIRS (Suomi NPP/NOAA-20/NOAA-21) | [NASA LANCE](https://www.earthdata.nasa.gov/data/instruments/viirs/atmosphere-near-real-time-data) | 375m | <3 hours |
| Polar orbiting Active Fire Detections | OLI (Landsat 8 & 9) | [USGS EROS](https://www.usgs.gov/centers/eros)<sup>5</sup> | 30m | 30-60 mins |
| Provisional Geostationary Active Fire Detections | ABI (GOES-16 & 18)<sup>1</sup> | [NOAA](https://www.class.noaa.gov/) | 2km sub-satellite<sup>2</sup> | ~20-30 mins |
| Provisional Geostationary Active Fire Detections | ABI (GOES-16 & 18)<sup>3</sup> | [CAMS](https://atmosphere.copernicus.eu/)/[IPMA](https://www.ipma.pt/en/index.html) | 2km sub-satellite<sup>2</sup> | ~20-30 mins |
| True/False Color Composite Imagery | ABI (GOES-16 & 18) | [NASA GIBS](https://www.earthdata.nasa.gov/engage/open-data-services-software/earthdata-developer-portal/gibs-api) | 1km | 40 mins |
| True/False Color Composite Imagery | MODIS (Terra/Aqua) | [NASA GIBS](https://www.earthdata.nasa.gov/node/10125) | 250m | <3 hours |
| True/False Color Composite Imagery | VIIRS (Suomi NPP/NOAA-20) | [NASA GIBS](https://www.earthdata.nasa.gov/engage/open-data-services-software/earthdata-developer-portal/gibs-api) | 250m | <3 hours |
| True/False Color Composite Imagery | OLI (Landsat 8 & 9) | [NASA IMPACT](https://www.earthdata.nasa.gov/about/impact)/[HLS](https://hls.gsfc.nasa.gov/) | 30m | 2-4 days |
| True/False Color Composite Imagery | MSI (Sentinel 2A & 2B) | [NASA IMPACT](https://www.earthdata.nasa.gov/about/impact)/[HLS](https://hls.gsfc.nasa.gov/) | 30m | 2-4 days |
| Aerosol Index | OMPS (Suomi NPP) | [NASA LANCE](https://www.earthdata.nasa.gov/data/projects/lance)/[GIBS](https://www.earthdata.nasa.gov/engage/open-data-services-software/earthdata-developer-portal/gibs-api) | ~50km | <3 hours |
| Aerosol Index PyroCumuloNimbus | OMPS (Suomi NPP) | [NASA LANCE](https://www.earthdata.nasa.gov/data/projects/lance)/[GIBS](https://www.earthdata.nasa.gov/engage/open-data-services-software/earthdata-developer-portal/gibs-api) | ~50km | <3 hours |
| Burned Area | MODIS (Terra/Aqua) | [NASA](https://modis-fire.umd.edu/ba.html) | 500m | ~3 months |

<sup>1</sup>FDC: Fire Detection and Characterization algorithm\
<sup>2</sup>The pixel size systematically grows from sub-satellite towards the edge of the disk\
<sup>3</sup>FRPPIXEL: Fire Radiative Power algorithm\
<sup>4</sup>Latency refers to the estimated time from satellite observation to availability in FIRMS\
<sup>5</sup>Currently curated for FIRMS US/Canada

See [Acronyms](https://www.earthdata.nasa.gov/data/tools/firms/faq#acronyms) section for definitions.
