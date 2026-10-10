---
id: faq.landsat.why-does-the-latency-differ-between-the-landsat-active-fire
title: Why does the latency differ between the Landsat active fire detection data and the HLS Landsat imagery?
kind: faq
section: landsat
section_title: Landsat Fire Data
source: firms-faq
source_url: https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-124563-11
retrieved: '2026-10-09'
content_sha256: 397822bde8b5cf71b813449dcfc05780c0e81d190bca1babdb63c76f698ee37c
order: 79
tags:
- landsat
- hls
- latency
related: []
status: current
---

Landsat active fire detection data are produced in collaboration with the USGS EROS Data Center in Sioux Falls, South Dakota. Daily Landsat 8 and Landsat 9 OLI imagery for the continental United States, southern Canada, and northern Mexico are captured via the Landsat ground station at EROS. This imagery is formatted and pre-processed in near real-time by the USGS and further processed onsite at EROS using NASA algorithms to extract 30-meter active fire detection data and made available for ingest into FIRMS approximately 30 minutes after a satellite overpass.

Landsat imagery in FIRMS is processed as part of the [Harmonized Landsat-Sentinel-2 (HLS) project](https://lpdaac.usgs.gov/data/get-started-data/collection-overview/missions/harmonized-landsat-sentinel-2-hls-overview/) to create BRDF-adjusted, 30-meter Landsat and Sentinel-2 surface reflectance products. Generated separately as provisional/research NASA products, HLS currently has a latency requirement of < 7 days. Consequently, FIRMS users desiring to view Landsat active fire detection data in the context of HLS Landsat true and false color composite imagery are required to wait until the processing of the HLS imagery is complete and made available in FIRMS.

The HLS imagery is currently processed and available in FIRMS 2-4 days after acquisition, which is less than the current HLS processing latency requirement. Opportunities to reduce the latency of HLS imagery processing and its availability in FIRMS will continue to be assessed by NASA and implemented if possible.
