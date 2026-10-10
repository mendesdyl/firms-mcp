---
id: faq.experimental.what-are-the-attributes-of-the-viirs-modeled-fire-perimeter
title: What are the attributes of the VIIRS Modeled Fire Perimeter data based on the FEDS algorithm?
kind: faq
section: experimental
section_title: Experimental Mode
source: firms-faq
source_url: https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-128897-8
retrieved: '2026-10-09'
content_sha256: 84f373888f86a9aec59d1be3676936c3b89b9392d59ee0dd94056c87bec017dd
order: 132
tags:
- viirs
- perimeter
- attributes
related: []
status: current
---

| Column | Description | Type/Unit |
|---|---|---|
| duration | Number of days since first observation of fire. Fires with a single observation have a duration of zero. | Days |
| farea | Area within estimated fire perimeter. | Km<sup>2</sup> |
| fireid | Fire ID. Unique for each fire. Matches fireid. | Numeric ID |
| flinelen | Length of active fire line, based on new pixels. If no new pixels are detected, flinelen is set to zero. | km |
| fperim | Length of estimated fire perimeter. | km |
| meanfrp | Mean fire radiative power. The weighted sum of the fire radiative power detected at each new pixel, divided by the number of pixels. If no new pixels are detected, meanfrp is set to zero. | Megawatts (MW)/(pixel area) |
| n_newpixels | Number of pixels newly detected since last overpass. | pixels |
| n_pixels | Number of pixel detections in history of fire. | pixels |
| pixden | Pixel density, the number of pixels divided by area of the estimated perimeter. | pixels/km<sup>2</sup> |
| Primarykey | ID Composed of identifying metadata. <region>\|<fireID>\|<am_or_pm> | String ID |
| Region | Region over which algorithm was run to generate fire. FireIDs are unique within region. |  |
| t | Time of VIIRS detection, corrected to noon and midnight. | Datetime. yyyy-mm-ddThh:mm:ss. Local time. |
| isactive | Have new fire pixels been detected in the last 5 days? | Boolean |
| ogc_fid | The ID used by the OGC API to sort perimeters. | Numeric ID |
| geometry | The shape of the estimated perimeter. | Geometry |
