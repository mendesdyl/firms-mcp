---
id: faq.viirs.will-the-viirs-375-m-fire-detection-algorithm-always-outperform
title: Will the VIIRS 375 m fire detection algorithm always outperform the 750 m one?
kind: faq
section: viirs
section_title: Questions About VIIRS Active Fire Data
source: firms-faq
source_url: https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-124459-5
retrieved: '2026-10-09'
content_sha256: c4d3e1dabb8d6b67e004b7ccc1a854000d69ef7112887bef1c07f1b812513a8e
order: 38
tags:
- viirs
related: []
status: current
---

Generally, the higher resolution product will achieve a higher probability of fire detection in both day and nighttime scenes. However, areas subject to strong solar reflectance associated with sun glint, such as metallic rooftops or highly reflective desert, could see a few 750 m fire pixels without a corresponding 375 m fire detection. This is attributed to the relatively shorter wavelength of the 375 m mid-infrared channel used in the fire algorithm, which will experience greater influence of the solar component. To minimize the associated consequences, namely the occurrence of false alarms over bright/reflective surfaces (e.g., metallic factory rooftops), the 375 m algorithm uses slightly more conservative tests to avoid the effects of Sun glint over those areas.
