---
id: faq.caveats.are-there-ever-false-fire-detections-or-data-artifacts
title: Are there ever false fire detections or data artifacts?
kind: faq
section: caveats
section_title: Caveats to Consider When Using Active Fire Data from FIRMS
source: firms-faq
source_url: https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-124439-1
retrieved: '2026-10-09'
content_sha256: 55267b29a62eded391c4c5cdcfceaffdb7db4c34e572d6f0f0cd018b2b727a34
order: 24
tags:
- caveats
related: []
status: current
---

To minimize the occurrence of false alarms over bright/reflective surfaces (e.g., metallic factory rooftops), the VIIRS and MODIS algorithms use slightly more conservative tests to avoid the effects of Sun glint.

### Super-Heated Smoke Plumes

A few VIIRS active fire pixels are occasionally located outside the reported perimeter of a large wildfire. The parallax effect causes the tall/superheated plume detection pixel(s) to be displaced laterally when projected onto the surface. Displaced pixels will be located on the fire perimeter’s side further away from the image center and closer to the swath’s edge. If this happens, users may need to look for additional clues to see if it is a data artifact. There have been a few instances when tall, superheated plumes carrying large volumes of hot material into the air are formed over large and intense wildfires; when these occur the VIIRS instrument detects the surface fire along with part of the plume and categorizes them as active fires. Those occurrences typically share the following set of conditions:

(i) Nighttime detection. This is the period during which the VIIRS active fire product is particularly responsive to heat sources thereby favoring plume detection. However, this can also occur during the daytime with;

(ii) Very large wildfires undergoing explosive growth and accompanied by rapid/vertically elongated plume development. Enough hot material must entrain the plume creating a distinguishable thermal signal (i.e., one that significantly exceeds the fire-free surface background);

(iii) High scan angle. This is what will ultimately produce the detections extending beyond the actual fire perimeter.

If those conditions apply, look for alternative observations (previous/next observation) acquired closer to nadir, and try to prioritize the use of the fire detection data accordingly. Unfortunately, the VIIRS active fire algorithm isn’t currently able to distinguish nighttime surface fire pixels from the isolated plume detections due to strong similarities between their radiometric signatures.

Related FAQs:

- Is the VIIRS 375 m product still being refined?
- What is the detection confidence?

Related links:

- [False fires due to super heated smoke plume in nighttime detections](https://landweb.modaps.eosdis.nasa.gov/displayissue?id=339) (August 3, 2018)
- [Note on False Fires in VIIRS/NOAA-20](https://landweb.modaps.eosdis.nasa.gov/displayissue?id=271) (July 17, 2020)
