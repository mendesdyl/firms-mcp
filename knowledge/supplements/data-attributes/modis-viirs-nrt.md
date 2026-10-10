---
id: supplement.data-attributes.modis-viirs-nrt
title: Active Fire Data Attributes for MODIS and VIIRS
kind: supplement
section: data-attributes
section_title: Active fire data attributes
source: firms-attributes
source_url: https://www.earthdata.nasa.gov/data/tools/firms/active-fire-data-attributes-modis-viirs
retrieved: '2026-10-09'
content_sha256: d639ec6de7f23e2c79f72187a58eddeefa1eaa59624e6c1afd5790616689f66f
order: 0
tags:
- attributes
- modis
- viirs
- confidence
- frp
related: []
status: current
---

Below is a list of fire attribute fields for near real-time ([NRT](https://www.earthdata.nasa.gov/learn/earth-observation-data-basics/near-real-time-versus-standard-products)) active fire data from the Moderate Resolution Imaging Spectroradiometer (MODIS) and Visible Infrared Imaging Radiometer Suite (VIIRS). Learn more about [MODIS NRT](https://www.earthdata.nasa.gov/data/instruments/modis/near-real-time-data) data, [VIIRS-Atmosphere NRT data](https://www.earthdata.nasa.gov/data/instruments/viirs/atmosphere-near-real-time-data), and [VIIRS-Land NRT data](https://www.earthdata.nasa.gov/data/instruments/viirs/land-near-real-time-data).

NRT active fire data is distributed by NASA's Fire Information for Resource Management System ([FIRMS](https://www.earthdata.nasa.gov/data/tools/firms)).

## Attribute Fields for NRT MODIS Active Fire Data

| Attribute | Short Description | Long Description |
|---|---|---|
| Latitude | Latitude | Center of 1 km fire pixel, but not necessarily the actual location of the fire as one or more fires can be detected within the 1 km pixel. |
| Longitude | Longitude | Center of 1 km fire pixel, but not necessarily the actual location of the fire as one or more fires can be detected within the 1 km pixel. |
| Brightness | Brightness temperature 21 (Kelvin) | Channel 21/22 brightness temperature of the fire pixel measured in Kelvin. |
| Scan | Along Scan pixel size | The algorithm produces 1 km fire pixels, but MODIS pixels get bigger toward the edge of scan. Scan and track reflect actual pixel size. |
| Track | Along Track pixel size | The algorithm produces 1 km fire pixels, but MODIS pixels get bigger toward the edge of scan. Scan and track reflect actual pixel size. |
| Acq_Date | Acquisition Date | Data of MODIS acquisition. |
| Acq_Time | Acquisition Time | Time of acquisition/overpass of the satellite (in UTC). |
| Satellite | Satellite | A = Aqua and T = Terra. |
| Confidence | Confidence (0-100%) | This value is based on a collection of intermediate algorithm quantities used in the detection process. It is intended to help users gauge the quality of individual hotspot/fire pixels. Confidence estimates range between 0 and 100% and are assigned one of the three fire classes (low-confidence fire, nominal-confidence fire, or high-confidence fire). |
| Version | Version (Collection and source) | Version identifies the collection (e.g., MODIS Collection 6.1) and source of data processing (Ultra Real-Time (URT suffix added to collection), Real-Time (RT suffix), Near Real-Time (NRT suffix) or Standard Processing (collection only). For example:<br>"6.1URT" - Collection 6.1 Ultra Real-Time processing.<br>"6.1RT" - Collection 6.1 Real-Time processing.<br>"6.1NRT" - Collection 61 Near Real-Time processing.<br>"6.1" - Collection 61 Standard processing.<br>Find out more on collections and on the differences between FIRMS data sourced from LANCE FIRMS and the University of Maryland in the [FIRMS FAQ](https://www.earthdata.nasa.gov/data/tools/firms/faq). |
| Bright_T31 | Brightness temperature 31 (Kelvin) | Channel 31 brightness temperature of the fire pixel measured in Kelvin. |
| FRP | Fire Radiative Power (MW - megawatts) | Depicts the pixel-integrated fire radiative power in MW (megawatts). |
| Type* | Inferred hot spot type | 0 = presumed vegetation fire<br>1 = active volcano<br>2 = other static land source<br>3 = offshore |
| DayNight | Day or Night | D= Daytime fire, N= Nighttime fire |

*This attribute is only available for MCD14ML (standard quality) data

## Attribute Fields for NRT VIIRS 375m Active Fire Data

| Attribute | Short Description | Long Description |
|---|---|---|
| Latitude | Latitude | Center of nominal 375 m fire pixel |
| Longitude | Longitude | Center of nominal 375 m fire pixel |
| Bright_ti4 /<br>Brightness (in web services) | Brightness temperature I-4 | VIIRS I-4 channel brightness temperature of the fire pixel measured in Kelvin |
| Scan | Along Scan pixel size | The algorithm produces approximately 375 m pixels at nadir. Scan and track reflect actual pixel size |
| Track | Along Track pixel size | The algorithm produces approximately 375 m pixels at nadir. Scan and track reflect actual pixel size |
| Acq_Date | Acquisition Date | Date of VIIRS acquisition |
| Acq_Time | Acquisition Time | Time of acquisition/overpass of the satellite (in UTC) |
| Satellite | Satellite | N= Suomi National Polar-orbiting Partnership (Suomi NPP), N20=NOAA-20 (designated JPSS-1 prior to launch), N21=NOAA-21 (designated JPSS-2 prior to launch) |
| Confidence | Confidence | This value is based on a collection of intermediate algorithm quantities used in the detection process. It is intended to help users gauge the quality of individual hotspot/fire pixels. Confidence values are set to low, nominal and high. Low confidence daytime fire pixels are typically associated with areas of sun glint and lower relative temperature anomaly (<15K) in the mid-infrared channel I4. Nominal confidence pixels are those free of potential sun glint contamination during the day and marked by strong (>15K) temperature anomaly in either day or nighttime data. High confidence fire pixels are associated with day or nighttime saturated pixels.<br>Please note: Low confidence nighttime pixels occur only over the geographic area extending from 11deg E to 110 deg W and 7 deg N to 55 deg S. This area describes the region of influence of the South Atlantic Magnetic Anomaly which can cause spurious brightness temperatures in the mid-infrared channel I4 leading to potential false positive alarms. These have been removed from the NRT data distributed by FIRMS. |
| Version | Version (Collection and source) | Version identifies the collection (e.g. VIIRS Collection 1) and source of data processing: Near Real-Time (NRT suffix added to collection) or Standard Processing (collection only)<br>"1.0NRT" - Collection 1 NRT processing<br>"1.0" - Collection 1 Standard processing |
| Bright_ti5 /<br>Brightness_2 (in web services) | Brightness temperature I-5 | I-5 Channel brightness temperature of the fire pixel measured in Kelvin |
| FRP | Fire Radiative Power | FRP depicts the pixel-integrated fire radiative power in MW (megawatts). FRP depicts the pixel-integrated fire radiative power in MW (megawatts). Given the unique spatial and spectral resolution of the data, the VIIRS 375 m fire detection algorithm was customized and tuned in order to optimize its response over small fires while balancing the occurrence of false alarms. Frequent saturation of the mid-infrared I4 channel (3.55-3.93 µm) driving the detection of active fires requires additional tests and procedures to avoid pixel classification errors. As a result, sub-pixel fire characterization (e.g., fire radiative power [FRP] retrieval) is only viable across small and/or low-intensity fires. Systematic FRP retrievals are based on a hybrid approach combining 375 and 750 m data. In fact, starting in 2015 the algorithm incorporated additional VIIRS channel M13 (3.973-4.128 µm) 750 m data in both aggregated and unaggregated format. |
| DayNight | Day or Night | D= Daytime fire, N= Nighttime fire |
