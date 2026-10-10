---
id: faq.us-canada.how-do-i-interpret-use-wildfire-perimeter-data-in-the-context
title: How do I interpret/use wildfire perimeter data in the context of satellite active fire detection data?
kind: faq
section: us-canada
section_title: FIRMS US/Canada
source: firms-faq
source_url: https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-124627-13
retrieved: '2026-10-09'
content_sha256: 352aa7bef8c8c843087e2a77b0cbf69d8ad3c3291a24bae0f0607b962d00fee0
order: 120
tags:
- perimeter
related: []
status: current
---

Wildfire perimeters for individual fires are typically updated once daily using relatively large scale data (airborne infrared flights, airborne or terrestrial GPS, etc.), but may be updated more or less frequently in particular circumstances. MODIS and VIIRS active fire detection data introduce additional factors that can contribute spatial and temporal alignment between these data and perimeters for ongoing wildfire incidents. These factors include:

- Timing of satellite observations: MODIS and VIIRS are onboard polar-orbiting satellite platforms that do not provide persistent observations. They only detect the location and extent of active fires at the time of a satellite overpass. This may result in gaps in active fire detection data within perimeters.
- Properties of fire activity and active fire detection data resolution: The size and intensity of fires at the time of a satellite overpass, including small, very hot fires and larger, smoldering fires, can both trigger fire detection algorithms. In both conditions, the detected fire activity will be indicated at the spatial resolution of the thermal bands (375 m for VIIRS and 1 km for MODIS). In other words, a small, intense fire occupying a fraction of the pixel or a broader, cooler-burning fire occupying most of the pixel will both be represented as a fire at the spatial resolution of the data. This typically results in cumulative active fire detection data overestimating the size of a wildfire and not aligning with the perimeter boundaries.
- Satellite observation conditions: Atmospheric conditions, including clouds and heavy smoke, can partially or fully obscure fire activity at the time of a satellite overpass and hinder its detection. This omission of potentially detected fire activity can result in gaps in active fire detection data within perimeters. Additionally, the view geometry becomes more distorted with increasing distance from the nadir of the satellite observation. As a result, active fire detections in pixels towards the outer edges of the satellite view swath will be shifted/displaced outwards and fall outside the wildfire perimeter.
