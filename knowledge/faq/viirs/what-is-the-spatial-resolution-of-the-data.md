---
id: faq.viirs.what-is-the-spatial-resolution-of-the-data
title: What is the spatial resolution of the data?
kind: faq
section: viirs
section_title: Questions About VIIRS Active Fire Data
source: firms-faq
source_url: https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-124459-3
retrieved: '2026-10-09'
content_sha256: c0abc3f12e0e7417fd8ec67cb60abe7265dcd5fe2cac644b203d6e83f2e9b058
order: 36
tags:
- viirs
- resolution
related: []
status: current
---

The 375 m data describe the nominal resolution after native data are spatially aggregated (see figure below).

![SpatialResVIIRSImagerData](https://earthdata.nasa.gov/s3fs-public/2022-02/SpatialResVIIRSImagerData.png?VersionId=A0FyhtLKRqM8ty8T4Tg6eIVz99Er0Byd)

*Image caption:* Spatial resolution of VIIRS imagery data as a function of scan angle. The three distinct regions represent unique data aggregation zones extending from nadir to the edge of swath.

The aggregation scheme changes across three distinct image regions. In the first region (nadir to 31.59° scan angle), three native pixels are aggregated in the along scan (cross-track) direction to form one data sample in the Level 1 image. In the second region (31.59° to 44.68° scan angle), two native pixels are aggregated to form one data sample. Finally in the third and last region (44.68° to 56.06° - edge of swath) one native pixel will result in one data sample. All five 375 m channels are aggregated onboard the spacecraft before the data are transmitted to the ground stations, whereas a subset of the VIIRS 750 m data (dual-gain channels only) are aggregated on the ground.
