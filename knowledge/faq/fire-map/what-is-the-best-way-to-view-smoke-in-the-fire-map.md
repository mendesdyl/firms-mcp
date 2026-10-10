---
id: faq.fire-map.what-is-the-best-way-to-view-smoke-in-the-fire-map
title: What is the best way to view smoke in the Fire Map?
kind: faq
section: fire-map
section_title: FIRMS Fire Map
source: firms-faq
source_url: https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-124577-5
retrieved: '2026-10-09'
content_sha256: a3603b0ac6d3847c11fb189db00f704a33a03746f10018299c42c602a8cbb603
order: 90
tags:
- fire-map
- smoke
related: []
status: current
---

To view smoke, add one of the corrected reflectance layers from the MODIS or VIIRS from the "backgrounds" section of the menu on the right. In addition, you could add the OMPS Aerosol Index (AI) and OMPS Aerosol Index (PyroCumuloNimbus) from the "overlays" section.

OMPS AI detects and measures the density of smoke and suspended particles in the vertical air column in the atmosphere. FIRMS provides OMPS AI data from three satellites:

- Suomi-NPP (S-NPP) OMPS: Launched in 2011, spatial resolution of 50 km x 50 km (~31 x 31 miles)
- NOAA-20 OMPS: Launched in 2017, with improved spatial resolution of 17 km x 13 km (~10.5 x 8 miles)
- NOAA-21 OMPS: Launched in November 2022, with the best spatial resolution at 12 km x 10 km (~6 x 6 miles), available from April 28, 2025

These instruments provide complementary coverage, improving the temporal resolution and reliability of smoke detection globally.

For AI values significantly higher than 5, use the OMPS Aerosol Index (PyroCumuloNimbus) layer. Larger AI values between 5 and 10 usually indicate dense smoke from intensely burning fires that reach higher in the troposphere. Once the AI gets above 10, the smoke has likely been produced from a pyroCb event, with dense smoke lofted into the upper troposphere and, often, into the stratosphere.
