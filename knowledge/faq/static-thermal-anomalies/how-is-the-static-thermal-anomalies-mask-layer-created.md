---
id: faq.static-thermal-anomalies.how-is-the-static-thermal-anomalies-mask-layer-created
title: How is the Static Thermal Anomalies - Mask layer created?
kind: faq
section: static-thermal-anomalies
section_title: Static Thermal Anomalies
source: firms-faq
source_url: https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-133308-2
retrieved: '2026-10-09'
content_sha256: 5b82d158642f359e7ade1a0f7eb3fe6a4771492c43995adb848d95ce49a781af
order: 136
tags: []
related: []
status: current
---

This layer is derived from the global analysis of 375m S-NPP VIIRS active fire detection data for calendar year 2023. The centroids of active fire detections are summarized on a 400m grid. Each grid cell containing 5 or more active fire detection counts over the course of the year are extracted to create a mask of frequently observed or static thermal activity. The resulting mask is spatially filtered using multiple industrial/power plant location datasets in an effort to limit the mask to areas not associated with vegetation fires.
