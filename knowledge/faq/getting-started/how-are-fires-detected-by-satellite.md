---
id: faq.getting-started.how-are-fires-detected-by-satellite
title: How are fires detected by satellite?
kind: faq
section: getting-started
section_title: Getting Started
source: firms-faq
source_url: https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-124369-10
retrieved: '2026-10-09'
content_sha256: aafbf45561c74fef24266e5580062cc127f2f5a5e400aaf2d760c769a7ada3d2
order: 10
tags: []
related: []
status: current
---

Fire detection is performed using a contextual algorithm that exploits the strong emission of mid-infrared radiation from fires. The NASA MODIS algorithm examines each pixel of the MODIS swath, and ultimately assigns to each pixel one of the following classes: missing data, cloud, water, non-fire, fire, or unknown. More information can be found in: Giglio, L., Descloitres, J., Justice, C. O., & Kaufman, Y. (2003). An enhanced contextual fire detection algorithm for MODIS. *Remote Sensing of Environment,* 87: 273-282. [doi:10.1016/S0034-4257(03)00184-6](https://doi.org/10.1016/S0034-4257(03)00184-6)

In keeping with MODIS, the VIIRS algorithm is a hybrid thresholding and contextual algorithm using radiometric signals from 4 micron and 11 micron bands (M13 and M15, respectively) and additional bands and a suite of tests for internal cloud mask and rejection of false alarms. The product primarily contains latitude and longitude data for those pixels classified as thermal anomalies. More information can be found in: Schroeder, W., Oliva, P., Giglio, L., & Csiszar, I. A. (2014). The New VIIRS 375m active fire detection data product: algorithm description and initial assessment. *Remote Sensing of Environment*, 143: 85-96. [doi:10.1016/j.rse.2013.12.008](https://doi.org/10.1016/j.rse.2013.12.008)
