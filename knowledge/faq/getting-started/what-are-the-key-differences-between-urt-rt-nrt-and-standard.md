---
id: faq.getting-started.what-are-the-key-differences-between-urt-rt-nrt-and-standard
title: What are the key differences between URT/RT/NRT and Standard quality fire data?
kind: faq
section: getting-started
section_title: Getting Started
source: firms-faq
source_url: https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-124369-3
retrieved: '2026-10-09'
content_sha256: 93b5a7a168ed382ab95ca1cb400d89e9742dfc8ef176c38d5f048fe3348c600b
order: 3
tags:
- latency
related: []
status: current
---

Standard (science quality) data products are an internally consistent, well-calibrated record of Earth’s geophysical properties to support science. The ultra real-time (URT), real-time (RT), and [near real-time (NRT)](https://www.earthdata.nasa.gov/learn/earth-observation-data-basics/near-real-time-versus-standard-products) fire products are generated more rapidly than standard processing allows to meet the needs of the applications community. To facilitate this, a number of changes have been made to the standard processing approach: for the URT and RT, direct broadcast data are used (see [Questions about Real-Time (RT) and Ultra Real-Time (URT) active fire data](https://www.earthdata.nasa.gov/data/tools/firms/faq#rt-urt) below) and for NRT, data downlinked from the satellite are sorted, processed, and delivered in an expedited manner (as Session-based Production Data Sets).

One key difference between the MODIS/Aqua NRT and MODIS/Aqua Standard (science quality) Fire Products is the accuracy of the fire locations (positions or geolocation). Unlike MODIS/Terra, VIIRS/Suomi NPP, VIIRS/NOAA-20 and VIIRS/NOAA-21, the position of the Aqua satellite is not as well known when the NRT Fire Product is produced. Most of the time, the additional error introduced in the reported fire location of the MODIS and VIIRS NRT products is small (< 100 m), but in some situations this position error may be large (several kilometers). In particular, the larger errors may occur after spacecraft maneuvers and during space weather events. The NRT Fire location accuracy is also degraded for MODIS/Terra, VIIRS/Suomi NPP, VIIRS/NOAA-20 and VIIRS/NOAA-21 after spacecraft maneuvers, but the time period is typically shorter than for MODIS/Aqua (< 2 hours for MODIS/Terra, VIIRS/Suomi NPP, and VIIRS/NOAA-20/21 vs. up to 12 hours for MODIS/Aqua). When the Standard Fire products are later processed, the best available satellite position data is used and the quality assurance team removes data degraded by spacecraft maneuvers. In addition, the Standard Fire products are typically later reprocessed at a later and the fire positions may be even more accurate in the reprocessed products.

The MODIS and VIIRS active fire and thermal anomalies products are Level 2 products. Unlike many other Level 2 products, the fire product does not make use of ancillary data, and so their codes are identical to the ones used in standard operations. However, please note:

- The data distributed via the FIRMS download tool does not attribute the static sources/inferred hotspot "type" (as outlined in table 10 of the [MODIS Active Fire User Guide](https://modis-fire.umd.edu/files/MODIS_C6_C6.1_Fire_User_Guide_1.0.pdf))
- The day/night column (also described on page 38 of the MODIS Active Fire User Guide) is currently calculated differently. The standard (science quality) processing algorithm uses the solar zenith angle (SZA) to threshold the day/night value; if the SZA exceeds 85 degrees it is assigned a night value. SZA values less than 85 degrees are assigned a day time value. For the NRT algorithm the day/night flag is assigned by ascending (day) vs descending (night) observation. It is expected that the NRT assignment of the day/night flag will be amended to be consistent with the standard processing.
