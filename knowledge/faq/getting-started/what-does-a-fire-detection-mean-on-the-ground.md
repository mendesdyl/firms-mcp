---
id: faq.getting-started.what-does-a-fire-detection-mean-on-the-ground
title: What does a fire detection mean on the ground?
kind: faq
section: getting-started
section_title: Getting Started
source: firms-faq
source_url: https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-124369-4
retrieved: '2026-10-09'
content_sha256: c7e7ef4408aec0ff14fc24c6e470a6c4fdc687652c94127a40f48fb28b32a2ef
order: 4
tags: []
related:
- faq.modis.what-does-scan-and-track-mean
- faq.modis.what-size-fires-can-be-detected
status: current
---

Satellites take a ‘snapshot’ of events as they pass over Earth. Each hotspot/active fire detection represents the center of a pixel flagged as containing one or more fires or other thermal anomalies (such as volcanoes). For MODIS the pixel is approximately 1 km and for VIIRS the pixel is approximately 375 m. The “location” is the center point of the pixel (not necessarily the coordinates of the actual fire). The actual pixel size varies with the scan and track (see: [What does scan and track mean](https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-124479-3)?). The fire is often less than the size of the pixel (see: [What size fires can be detected](https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-124479-6)?). We are not able to determine the exact location or size of the fire; what we do know is that at least one fire is located within the flagged pixel. Sometimes you will see several active fires in a line. This generally represents a fire front.

![Figure explaining what a MODIS active fire/hotspot detection means on the ground](https://earthdata.nasa.gov/s3fs-public/imported/MODIS_fire_ground_observation.png?VersionId=yANOx2VrueVWXvaG2j6_NFZ8AOwrzGHg)

![Figure explaining what a VIIRS 375m active fire/hotspot detection means on the ground](https://earthdata.nasa.gov/s3fs-public/imported/VIIRS_375m_fire_ground_observation_.png?VersionId=uxxXvt.yA5Jj61utC.WfgNuwRnKWHYna)
