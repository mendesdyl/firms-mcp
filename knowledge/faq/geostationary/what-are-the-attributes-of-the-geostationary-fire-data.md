---
id: faq.geostationary.what-are-the-attributes-of-the-geostationary-fire-data
title: What are the attributes of the geostationary fire data?
kind: faq
section: geostationary
section_title: Geostationary Active Fire Data
source: firms-faq
source_url: https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-124520-3
retrieved: '2026-10-09'
content_sha256: ce63c56635a648cd4e007b685795c177cd1762656b76228b5d287c0ae8a1a66f
order: 62
tags:
- geostationary
- attributes
related:
- faq.geostationary.what-is-the-spatial-resolution-of-the-geostationary-satellite
status: current
---

The attributes are described in the following table:

| Attribute | Short Description | Long Description |
|---|---|---|
| Latitude | Latitude (decimal degrees) | Latitude of pixel center. Note: Pixel size/dimension is affected by satellite view geometry and curvature of Earth’s surface. Consequently, pixel size becomes more distorted (larger) with increasing distance from the point immediately below the satellite. The reported coordinate is the center of each pixel’s footprint. See: [What is the spatial resolution of the geostationary satellite observations](https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-124520-6)? |
| Longitude | Longitude (decimal degrees) | Longitude of pixel center. Note: Pixel size/dimension is affected by satellite view geometry and curvature of Earth’s surface. Consequently, pixel size becomes more distorted (larger) with increasing distance from the point immediately below the satellite. The reported coordinate is the center of each pixel’s footprint. See: [What is the spatial resolution of the geostationary satellite observations](https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-124520-6)? |
| Brightness | Brightness Temperature (BT) (kelvins) | Middle-infrared channel BT (kelvins)<br>No BT values are output from the FDC algorithm indicated by -999 |
| Pixel_Y | Pixel size (E-W direction) | These values reflect the approximate pixel size. |
| Pixel_X | Pixel size (N-S direction) | These values reflect the approximate pixel size. |
| Acquire_Time | Time and date of start of scan | Scan start time. The format is YYYY-MM-DD followed by HH:MM. For example, the time 12:14 |
| Confidence | Confidence | FRP-PIXEL: Value range 0-1. Higher values correspond to higher detection confidences.<br>FDC-HSC: class values range from 10-15 and 30- 35 and are indicative, but not a measure of fire confidence level. The former sub-group defines instantaneous (first/single) fire detections whereas the latter identifies temporally-filtered cases when two or more co-located detections are observed within a 12-hour interval.<br>FIRMS filters and displays only:<br>- 10 or 30: Good quality (highest confidence)<br>- 11 or 31: Saturated fire pixel |
| Version | Version (FIRMS reference only) | 1.0 NRT |
| Brightness2 | Brightness Temperature (kelvins) | Long-wave infrared channel brightness temperature (kelvins)<br>No BT values are output from the FDC algorithm indicated by -999 |
| FRP | Fire Radiative Power | FRP depicts the pixel-integrated fire radiative power in MW (megawatts). |
| Day/Night | Day or Night | D= Daytime fire, N= Nighttime fire |
| Satellite | Satellite | Him8 = Himawari-8 KCL/IPMA<br>Met9 = Meteosat-9 (MSG 0) KCL/LSA SAF<br>Met11 = Meteosat-11 (MSG IODC) KCL/LSA SAF<br>MTG0 = Meteosat-12 (MTG-0) KCL/LSA SAF<br>G16 = GOES-16 (GOES-East) NOAA FDC<br>G19 = GOES-19 (GOES-West) NOAA FDC<br>G16FRP = GOES-16 (GOES-East) KCL/IPMA<br>G19FRP = GOES-19 (GOES-West) KCL/IPMA |
