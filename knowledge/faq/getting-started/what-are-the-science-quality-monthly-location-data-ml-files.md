---
id: faq.getting-started.what-are-the-science-quality-monthly-location-data-ml-files
title: What are the science-quality Monthly Location data (ML files) delivered through FiRMS?
kind: faq
section: getting-started
section_title: Getting Started
source: firms-faq
source_url: https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-124369-4
retrieved: '2026-11-18'
content_sha256: e2f0acb04483fcec3077fd0d438a1c72040ed1125c9aaa407f910421dd604c41
order: 4
tags: []
related: []
status: current
---

Instead of distributing the standard Level 2 files, FIRMS ingests the monthly fire location ASCII files (short file names ending in "ML", e.g., VNP14IMGML, VJ114IMGML for NOAA-20 and VJ214IMGML for NOAA-21) from the Fire Science Computing Facility at the University of Maryland (UMD).

These summary files carry essential fire detection information in a comma-separated format that can be easily displayed on a map using common GIS software. They have an additional layer of Quality Control provided by the Principal Investigator and are available through FIRMS with a 2-3 month lag.

For many scientific studies, the standard Level 2G products are better suited to quantitative analysis because they retain pixel-level quality information, including cloud cover and other quality flags, and account for overlapping satellite orbits to avoid double-counting fire detections. These characteristics are particularly important for analyses of fire occurrence, temporal trends, and regional comparisons, where data quality and consistent counting of detections are essential.
