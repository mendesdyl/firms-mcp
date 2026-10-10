---
id: faq.experimental.what-is-the-spatial-resolution-of-the-viirs-modeled-fire
title: What is the spatial resolution of the VIIRS Modeled Fire Perimeter data?
kind: faq
section: experimental
section_title: Experimental Mode
source: firms-faq
source_url: https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-128897-3
retrieved: '2026-10-09'
content_sha256: 7e3957ef224757c1f8016ee0595e42cf876e6130940bc8ae82f7c2d065f21394
order: 127
tags:
- viirs
- resolution
- perimeter
related: []
status: current
---

Although the vector data in the VIIRS Modeled Fire Perimeter product has no defined spatial resolution, the product is derived from the VIIRS 375 m active fire detections, and therefore reflects the spatial resolution and geolocation accuracy of those products from the Suomi-NPP and NOAA-20 satellites. The FEDS algorithm uses an alpha hull approach to cluster new active fire detections and model the updated fire perimeter every 12 hours. The alpha hull approach groups individual fire detection points from the VIIRS sensors on two satellite platforms to model their combined spatial extent and distribution at each 12-hour time step. Compared to a convex hull, the alpha hull approach is better able to capture irregular shapes of active fire events and changes in shape over time. See Chen et al. (2022) for additional details.
