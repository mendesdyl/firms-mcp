---
id: faq.viirs.are-those-few-isolated-fire-pixels-in-the-middle-of-the-south
title: Are those few isolated fire pixels in the middle of the South Atlantic Ocean real?
kind: faq
section: viirs
section_title: Questions About VIIRS Active Fire Data
source: firms-faq
source_url: https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-124459-6
retrieved: '2026-10-09'
content_sha256: 42adcca611b29791e4d164606cadd70782c5b702d05b404253b2f4f140dede56
order: 39
tags:
- viirs
- resolution
related: []
status: current
---

Those occurrences are typically associated with spurious fire detections due to the South Atlantic Magnetic Anomaly. The 375 m active fire algorithm contains a specific filter to flag those occurrences as low confidence detections. However, in some cases (average 2-3 pixels every night) the spurious signal generated in the input Level 1 data is confused for a regular fire pixel and therefore assigned a nominal confidence flag. Note that verified true positives can be found over South Atlantic Ocean waters along the southeast coast of Brazil and the west coast of Africa where oil rigs normally operate.
