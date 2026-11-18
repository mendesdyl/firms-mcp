---
id: faq.getting-started.what-are-the-key-differences-between-urt-rt-nrt-and-standard
title: What are the key differences between URT/RT/NRT and Standard quality fire data?
kind: faq
section: getting-started
section_title: Getting Started
source: firms-faq
source_url: https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-124369-3
retrieved: '2026-11-18'
content_sha256: b970557b0f5f8f137ba51a7a8df56d3f5022b6eac8d2fd925ed7b8988085d40d
order: 3
tags:
- latency
related: []
status: current
---

The primary difference between these products comes down to speed versus accuracy.

- **Standard (science quality) data—which FIRMS provides as a GIS-friendly swath-based monthly location "ML" product, but is also available as Level 2G raster products from the Earthdata Search - delivers an internally consistent, well-calibrated record of Earth’s geophysical properties designed to support long-term scientific research.
- Ultra Real-Time (URT), Real-Time (RT), and Near Real-Time (NRT) data are generated much more rapidly to meet the immediate needs of emergency responders and the applications community.

To achieve faster processing times, the URT, RT, and NRT products use modified processing approaches. While the core algorithms for MODIS and VIIRS active fire products (Level 2) remain identical to standard operations, there are a few key differences you should be aware of:

1. Data Source and Processing Speed

- URT and RT: Use Direct Broadcast data to provide the fastest possible detections (see *Questions about Real-Time and Ultra Real-Time active fire data* below).
- NRT: Uses data downlinked from the satellite that is sorted, processed, and delivered in an expedited manner (as Session-based Production Data Sets).
- Standard / ML Product: Uses fully processed satellite position data. Please note: FIRMS uses the monthly summary "ML" files instead of the standard Level 2 products. These are usually available with a 2-3 month lag.

2. Geolocation Accuracy (Fire Locations) and Missing Granules

Because NRT products are generated before precise satellite positioning data is finalized, there can be differences in spatial accuracy:

- General NRT Accuracy: Most of the time, the additional error introduced in the reported fire location for MODIS and VIIRS NRT products is very small (< 100 meters).
- Errors After Spacecraft Maneuvers: In some situations—such as after spacecraft maneuvers or during severe space weather events—positioning errors can reach several kilometers.
  - For MODIS/Terra, VIIRS/NOAA-20, and VIIRS/NOAA-21, this degraded period is typically short (< 2 hours).
  - For MODIS/Aqua, the satellite's position is not as well known during NRT production, and the degraded period can last much longer (up to 12 hours).
- Standard / ML Accuracy: When the science-quality products are processed, the best available satellite position data is used, any missing granules are ingested, and the quality assurance team removes any data degraded by spacecraft maneuvers. Reprocessed versions may offer even higher accuracy.

3. Product Attributes and Metadata

Because NRT data does not utilize ancillary data, there are slight differences in the metadata provided:

- Hotspot "Type" Attribution: NRT data distributed via the FIRMS download tool does not attribute the static sources or inferred hotspot "type" (outlined in Table 10 of the MODIS Active Fire User Guide). However, this data *is* available in the ML version of the product (see [Active Fire Data Attributes](https://www.earthdata.nasa.gov/data/tools/firms/active-fire-data-attributes-modis-viirs)).
- Day/Night Calculation:
  - *The Standard / ML processing algorithm* uses the Solar Zenith Angle (SZA). If the SZA exceeds 85 degrees, it is assigned a "night" value; under 85 degrees is "day."
  - *NRT Data* currently assigns the day/night flag based simply on the satellite's orbit: ascending (day) vs. descending (night). *(Note: It is expected that the NRT assignment will be amended in the future to match standard processing).*
