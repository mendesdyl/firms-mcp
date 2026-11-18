---
id: faq.getting-started.what-are-the-different-sources-of-modis-and-viirs-active-fire
title: What are the different sources of MODIS and VIIRS active fire data in FIRMS?
kind: faq
section: getting-started
section_title: Getting Started
source: firms-faq
source_url: https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-124369-6
retrieved: '2026-11-18'
content_sha256: 4139c433e7a48bae2423e012b82f8b00efca7889f8b1d4bcb48cd6cda1dcc231
order: 6
tags:
- modis
- viirs
related:
- faq.rt-urt.what-are-the-real-time-rt-and-ultra-real-time-urt-data-in-firms
status: current
---

- MODIS NRT C6.1 ([MCD14DL](https://www.earthdata.nasa.gov/node/13777)) are the NRT MODIS (Terra and Aqua) Collection 6.1 data processed by NASA FIRMS.
- [MCD14ML](https://modis-fire.umd.edu/files/MODIS_C6_Fire_User_Guide_C.pdf) Standard (science quality), which FIRMS provides as a GIS-friendly swath based monthly location "ML" proudct. These are a subset of the standard quality Level 2G raster products available through Earthdata Search. The ML files are processed by the [MODIS Fire Team Science](http://modis-fire.umd.edu/) Computing Facility at the University of Maryland. These are available with a 2-3 month lag through the [Archive Download Tool](https://firms.modaps.eosdis.nasa.gov/download/) and can be viewed and queried in [Fire Map](https://firms.modaps.eosdis.nasa.gov/map/).
- VIIRS 375 m NRT active fire data are available from NOAA-20 ([VJ114IMGTDL_NRT](https://www.earthdata.nasa.gov/node/13826)) and NOAA-21 ([VJ214IMGTDL_NRT](https://www.earthdata.nasa.gov/node/13865)). These are processed by NASA FIRMS.
- VIIRS standard (science quality) are available from S-NPP (VNP14IMGTML), NOAA-20 (VJ114MGTML) and NOAA-21 (VJ214IMGTML)
- Landsat Fire and Thermal Anomalies (LFTA) product is generated from all daytime Operational Land Imager (OLI) acquisitions and currently provided for most of North America (CONUS, southern Canada and northern Mexico). The LFTA is currently produced through a collaboration by USGS EROS Data Center, the USDA Forest Service, the University of Maryland and NASA. Daily Landsat 8 and Landsat 9 OLI observations are processed by EROS and use the NASA-developed algorithm to produce active fire detection data that is ingested into FIRMS.

Please note: A real-time (RT) and ultra real-time (URT) version of both MODIS and VIIRS active fire data are available for the US and Canada within minutes of satellite observation. See: [What are the real-time (RT) and ultra real-time (URT) data in FIRMS](https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-124500-1)?
