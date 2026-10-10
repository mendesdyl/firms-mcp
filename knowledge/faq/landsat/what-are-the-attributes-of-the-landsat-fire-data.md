---
id: faq.landsat.what-are-the-attributes-of-the-landsat-fire-data
title: What are the attributes of the Landsat fire data?
kind: faq
section: landsat
section_title: Landsat Fire Data
source: firms-faq
source_url: https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-124563-7
retrieved: '2026-10-09'
content_sha256: 1f55d64c0a50706add3e847d6f70e5d2c4c7bf66c4828e288d7b6983824b3709
order: 75
tags:
- landsat
- attributes
related: []
status: current
---

The attributes are described in the following table:

| Attribute | Short Description | Long Description |
|---|---|---|
| Satellite | Satellite | L8 = Landsat 8; L9 = Landsat 9 |
| Latitude | Latitude (decimal degrees) | Latitude of pixel center |
| Longitude | Longitude (decimal degrees) | Longitude of pixel center |
| Path | Path | Path number as identified in the World Reference System-2 (WRS-2) |
| Row | Row | Row number as identified in the World Reference System-2 (WRS-2) |
| Track | Track | The pixel location in the along-track dimension of the Landsat path based on the OLI Line-of-Sight (LOS) coordinate system. Generally increases in value from north to south for daytime and nighttime overpasses. |
| Scan | Scan | The pixel location in the cross-track dimension of the Landsat path based on the OLI Line-of-Sight (LOS) coordinate system. Generally increases in value from west to east for daytime and nighttime overpasses. |
| Acquire_Time | Date and time of start of scan | Date and time of acquisition/overpass of the satellite (in UTC). The format is YYYY-MM-DD followed by HH:MM-SS. For example, 2022-07-23 10:09:00. |
| Confidence | Confidence | Value domain: H, M, and L:<br>- H: Higher confidence<br>- M: Medium confidence<br>- L: Lower confidence |
| Version | Version (FIRMS reference only) | 1.0.7 NRT |
| DayNight | Day or Night | D= Daytime fire, N= Nighttime fire |
