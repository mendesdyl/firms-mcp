---
id: faq.modis.what-size-fires-can-be-detected
title: What size fires can be detected?
kind: faq
section: modis
section_title: Questions About MODIS Active Fire Data
source: firms-faq
source_url: https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-124479-6
retrieved: '2026-10-09'
content_sha256: 07ca16b0c45e851d294687ca24f84ffdadee56310527846b14ee097931947fb5
order: 48
tags:
- modis
- resolution
related:
- faq.caveats.can-i-estimate-burned-area-from-active-fire-data
status: current
---

In any given scene the minimum detectable fire size is a function of many different variables (scan angle, biome, Sun position, land surface temperature, cloud cover, amount of smoke and wind direction, etc.), so the precise value will vary slightly with these conditions. MODIS routinely detects both flaming and smoldering fires 1000 m<sup>2</sup> in size. Under very good observing conditions (e.g., near nadir, little or no smoke, relatively homogeneous land surface, etc.) flaming fires one tenth this size can be detected. Under pristine (and extremely rare) observing conditions even smaller flaming fires 50 m<sup>2</sup> can be detected. It is not recommended to estimate burned area from the active fire data, see: [Can I estimate burned area using the active fire data](https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-124439-7)?.

Unlike most contextual fire detection algorithms designed for satellite sensors that were never intended for fire monitoring (e.g., AVHRR, VIIRS, ATSR), there is no upper limit to the largest and/or hottest fire that can be detected with MODIS.

![Example of the day and night relationship of fire size and fire temperature](https://earthdata.nasa.gov/s3fs-public/imported/firms_daynight.jpg?VersionId=EhXAI3z64VlRai9JY_clVSvQhMKZkZCB)

*Image caption:* The diagram shows the day and night relationship of fire size and fire temperature, in different biomes, to the probability of being detected by MODIS (Giglio, et al. (2003)).
