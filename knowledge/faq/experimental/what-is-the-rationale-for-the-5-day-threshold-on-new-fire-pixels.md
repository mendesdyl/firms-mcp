---
id: faq.experimental.what-is-the-rationale-for-the-5-day-threshold-on-new-fire-pixels
title: What is the rationale for the 5-day threshold on new fire pixels?
kind: faq
section: experimental
section_title: Experimental Mode
source: firms-faq
source_url: https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-128897-9
retrieved: '2026-10-09'
content_sha256: bd790a74f6d170f3d6cdc16be5e0b01cbab7ca3f0bbbed6210022cc7a98685bb
order: 133
tags:
- resolution
related: []
status: current
---

The FEDS algorithm uses spatial and temporal search criteria to cluster VIIRS 375 m active fire detections into existing or new fire objects. The use of the 5-day threshold to associate new fire detections with an existing fire object reflects the nature of large fire behavior and periodic gaps in active fire detection data. Large fire events often exhibit episodic growth in response to changes in fire weather, suppression activity, and fuels. Periods with less intense fire activity may not generate active fire detections from VIIRS, leading to temporal gaps (12-hour, 24-hour, etc.) in fire detection information.

The 5-day threshold allows the FEDS algorithm to connect future fire detections to the same fire object, or event, rather than splitting a large fire into multiple objects. In addition to periods of lower fire intensity, gaps in fire detection can occur due to satellite outages or observing conditions such as clouds that impact the VIIRS fire detection algorithm. The 5-day threshold reduces the influence of these data gaps on the fragmentation of large fire events in the FEDS algorithm output.
