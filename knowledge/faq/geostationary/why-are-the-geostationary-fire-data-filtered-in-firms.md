---
id: faq.geostationary.why-are-the-geostationary-fire-data-filtered-in-firms
title: Why are the geostationary fire data filtered in FIRMS?
kind: faq
section: geostationary
section_title: Geostationary Active Fire Data
source: firms-faq
source_url: https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-124520-7
retrieved: '2026-10-09'
content_sha256: 97daa9b8a839aef83f692711967514edc37cf37f49d3732a77f34b6df7bc6cfe
order: 66
tags:
- geostationary
related: []
status: current
---

While geostationary active fire data provide a much enhanced temporal frequency compared to active fire data from polar-orbiting satellites, data from geostationary satellites can yield spurious fire detections. These can result from sunglint, bright water, bright deserts/soils, coastlines, and navigation inconsistencies resulting in positioning error. The Meteosat SEVIRI and Himawari AHI data, made available from EUMETSAT and CAM, have a 65-degree view zenith angle cut-off due to the large pixel size at high latitudes. MTG FCI data have a 60-degree view zenith angle cut-off.

The following images provide examples of where spurious fire detections from Meteosat SEVIRI have been noted.

![FIRMS screenshot showing active fire in orange on a green background; key on right](https://earthdata.nasa.gov/s3fs-public/2023-09/fires-in-estrela-np_1_basic.png?VersionId=gAeDD867nUiGee60zNKVIzlWI4tSIDes)

*Image caption:* This series (1 of 3) of FIRMS screenshots, from August 11, 2022, show fires detected in the Serra da Estrela National Park, Portugal. This first screenshot shows a MODIS/Terra 7,2,1 Corrected Reflectance image with burned area in reddish-brown and an active fire front in orange (note: no active fires have been overlayed).

![FIRMS fire map image of orange fire on a green background; key on right](https://earthdata.nasa.gov/s3fs-public/2023-09/fires-in-estrela-np_2_basic.png?VersionId=miYF5h2RTQxMrSvO7i9jrMUnfxVJ4boA)

*Image caption:* This second image in the series of FIRMS screenshots from August 11, 2022, shows fires detected in the Serra da Estrela National Park, Portugal. This screenshot shows a MODIS/Terra 7,2,1 Corrected Reflectance image, overlain with VIIRS active fire detections shown as red pixels.

![FIRMS example with fire indicated by dots and key on right](https://earthdata.nasa.gov/s3fs-public/2023-09/fires-in-estrela-np-3_basic.png?VersionId=nJ0_6oc4Lyu5m9mVdIAqWqPDtihet5h5)

*Image caption:* This third image in the series of FIRMS screenshots from August 11, 2022, shows fires detected in the Serra da Estrela National Park, Portugal. This third screenshot shows a MODIS/Terra 7,2,1 Corrected Reflectance image, overlain with VIIRS active fire detections shown as red pixels and Meteosat-11 SEVIRI FRP pixels shown as orange pixels. Some spurious SEVIRI fire detections are evident.

The Filtered Fire Detection and Characterization (FDC-HSC) algorithm used to produce the GOES-16 and GOES-19 active fire data from NOAA, is still under development. To limit false detections, the data shown in FIRMS are filtered to show only fire detections with higher confidence values; these are classes 10 and 30, and 11 and 31. These criteria are driven by the validation analysis (See Hall et al 2019) and a qualitative review of the current algorithm output. The full list of classes available is outlined in the table below:

| Class | Description |
|---|---|
| 10 or 30 | Good quality (highest confidence) fire detections** |
| 11 or 31 | Saturated fire pixel** |
| 12 or 32 | Cloud contaminated fire pixel |
| 13 or 33 | High probability fire pixels that do not satisfy requirements to be categorized as good quality fire detections |
| 14 or 34 | High probability fire pixels that do not satisfy requirements to be categorized as good quality fire detections |
| 15 or 35 | Low probability fire pixels that do not satisfy requirements to be categorized as good quality fire detections |

**indicates the classes shown in FIRMS

Our qualitative assessment indicates some spurious fire detections are showing (see example below). This could be due to sun glint, bright water, bright deserts/soil, coastlines and lake edges etc so users are requested to use the data with caution. If in doubt, we recommend users look for coincident fire detections from MODIS or VIIRS in the vicinity. If they are present, the user can have more confidence in the geostationary data.

![Fire false positives shown on map due to issue with GOES FDC](https://earthdata.nasa.gov/s3fs-public/2022-09/FIRMS_GOESFDC_falsepositives.png?VersionId=wJ4EoA9UgW1A68eJ.GnFKjl59jhCSMKI)

*Image caption:* In this screenshot from FIRMS, on 15 July 2022, the GOES FDC data from NOAA (shown in pink) along the lake edge are thought to be false positives / spurious fire detections. Users should exercise caution when using the data.
