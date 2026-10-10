---
id: faq.fire-map.why-is-the-spatial-resolution-of-the-viirs-active-fire-pixels
title: Why is the spatial resolution of the VIIRS active fire pixels 375m and the spatial resolution of the VIIRS imagery displayed in FIRMS 250m?
kind: faq
section: fire-map
section_title: FIRMS Fire Map
source: firms-faq
source_url: https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-124577-6
retrieved: '2026-10-09'
content_sha256: 26ac9d42e7030af6853504f0bc577b9cca7ed38bc86b4700c341687903b4cd43
order: 91
tags:
- viirs
- resolution
- fire-map
related: []
status: current
---

The VIIRS instrument has 22 spectral bands (5 bands have a spatial resolution of 375m and 17 bands have a spatial resolution of 750m). The VIIRS active fire product uses three bands (two bands (I3 and I4) with a spatial resolution of 375m and one band (M11) with a spatial resolution of 750m). M11 is co-located with the 375m pixels and the same value is assigned to both 375m pixels or the value is split between the pixels.

The OMPS AI layer is useful for identifying and tracking smoke from wildfires or biomass burning events as well as dust from desert dust storms and the long-range transport of volcanic ash from volcanic eruptions. Values of 5.0, or higher, indicate heavy concentrations of aerosols that could reduce visibility or impact human health.
