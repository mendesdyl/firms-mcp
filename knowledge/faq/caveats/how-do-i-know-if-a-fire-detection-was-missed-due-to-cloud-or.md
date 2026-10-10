---
id: faq.caveats.how-do-i-know-if-a-fire-detection-was-missed-due-to-cloud-or
title: How do I know if a fire detection was missed due to cloud or missing data?
kind: faq
section: caveats
section_title: Caveats to Consider When Using Active Fire Data from FIRMS
source: firms-faq
source_url: https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-124439-2
retrieved: '2026-10-09'
content_sha256: 8344d333e699e670aa4e1d263a67508e77993aaac6793f52f76b419b0805c4d3
order: 25
tags:
- caveats
related: []
status: current
---

An indication of cloud cover or missing data can be obtained by viewing the co-incident MODIS or VIIRS imagery in [FIRMS Fire Map](https://firms.modaps.eosdis.nasa.gov/map/) or [Worldview](http://worldview.earthdata.nasa.gov/). To take cloud and missing data in to account, it may be more appropriate to use one of the 1 km Level 3 or Climate Modeling Grid (CMG) fire products (see the discussion in the [MODIS Fire User Guide](https://modis-fire.umd.edu/files/MODIS_C6_C6.1_Fire_User_Guide_1.0.pdf)).

To check if there are any days where data is missing, please refer to the [FIRMS missing data table](https://firms.modaps.eosdis.nasa.gov/api/missing_data/). This page shows the days in which there are no data for a particular satellite and instrument combination. This information is provided for both standard quality data and near real-time (NRT) data. Note: this will only show the days where there is no data for the satellite/sensor combination.
