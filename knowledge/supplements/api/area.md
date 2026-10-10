---
id: supplement.api.area
title: 'FIRMS API: area'
kind: supplement
section: api
section_title: FIRMS API
source: firms-api
source_url: https://firms.modaps.eosdis.nasa.gov/api/area/
retrieved: '2026-10-09'
content_sha256: 52acc91ae4238b0d858b131693856b7c857ea770ccf1c09ba3fd56344bbc2014
order: 0
tags:
- api
- area
- latency
related: []
status: current
---

- /api/area/csv/[MAP_KEY]/[SOURCE]/[AREA_COORDINATES]/[DAY_RANGE]

- Get most recent data, from TODAY to TODAY - (DAY_RANGE-1)

- /api/area/csv/[MAP_KEY]/[SOURCE]/[AREA_COORDINATES]/[DAY_RANGE]/[DATE]

- Returns data for [DATE] .. [DATE + DAY_RANGE-1]

[Attribute table for LANDSAT](https://www.earthdata.nasa.gov/data/tools/firms/faq)\
[Attribute table for MODIS](https://go.nasa.gov/3JSgbdb)\
[Attribute table for VIIRS S-NPP](https://go.nasa.gov/3sf3ALb)\
[Attribute table for VIIRS NOAA-20](https://www.earthdata.nasa.gov/learn/find-data/near-real-time/firms/vj114imgtdlnrt)\
[Attribute table for VIIRS NOAA-21](https://www.earthdata.nasa.gov/learn/find-data/near-real-time/firms/vj214imgtdlnrt)

**SOURCE:**

- LANDSAT_NRT [US/Canada only] (LANDSAT Near Real-Time, Real-Time and Ultra Real-Time *)
- MODIS_NRT (MODIS Near Real-Time, Real-Time and Ultra Real-Time *)
- MODIS_SP (MODIS Standard Processing)
- VIIRS_NOAA20_NRT (VIIRS NOAA-20 Near Real-Time, Real-Time and Ultra Real-Time *)
- VIIRS_NOAA20_SP (VIIRS NOAA-20 Standard Processing)
- VIIRS_NOAA21_NRT (VIIRS NOAA-21 Near Real-Time, Real-Time and Ultra Real-Time *)
- VIIRS_SNPP_NRT (VIIRS Suomi-NPP Near Real-Time, Real-Time and Ultra Real-Time *)
- VIIRS_SNPP_SP (VIIRS Suomi-NPP Standard Processing)

* RT and URT data are removed when corresponding NRT detections are processed or RT/URT is older than 6 hours.\
\
NASA EOSDIS defines Real-Time as data that is made available within 60 minutes of satellite overpass. URT is much quicker than that. FIRMS makes URT data available in less than 60 seconds of satellite fly over for much of the US and Canada\
[Learn more about Ultra Real-Time data.](https://wiki.earthdata.nasa.gov/display/FIRMS/2022/07/14/Wildfire+detection+in+the+US+and+Canada+within+a+minute+of+satellite+observation)

**AREA_COORDINATES:**

- west,south,east,north - ex. (South America): -85,-57,-32,14\
  NOTE: The Area API expects a bounding box or 'world', and NOT 'north', 'south', 'east', or 'west.'
- world - [-180,-90,180,90]

Maximum boundary: -180, -90, 180, 90

**DAY_RANGE:**

- 1 .. 5 - number of days to query at one time

**DATE:**

- YYYY-MM-DD - [Optional] If not provided it will return the most recent data
- [/api/data_availability/](https://firms.modaps.eosdis.nasa.gov/api/data_availability/) - check for product date availability

Map Key

To use FIRMS web services, request **free** MAP_KEY

Get MAP_KEY

To check number of available map transactions

Check status
