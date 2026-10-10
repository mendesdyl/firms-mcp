---
id: faq.getting-started.how-often-is-firms-updated
title: How often is FIRMS updated?
kind: faq
section: getting-started
section_title: Getting Started
source: firms-faq
source_url: https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-124369-7
retrieved: '2026-10-09'
content_sha256: eddc3790675d04ceaa3b338199deda096e2fc8455bd136bb694ea36933458d2a
order: 7
tags:
- latency
related:
- faq.getting-started.how-often-are-modis-and-viirs-active-fire-data-acquired
- faq.getting-started.what-time-does-the-satellite-pass-over-my-area
status: current
---

FIRMS is updated regularly as new data are ingested. However, it is important to note that the data are derived from instruments onboard polar orbiting satellites (MODIS aboard Terra and Aqua, and VIIRS aboard Suomi NPP and NOAA-20/21), and generally these have two overpasses a day (more towards the poles - see [How often are the active fire data acquired](https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-124369-6)). FIRMS makes the NRT data available within 3 hours of a satellite observation (on a best-effort basis); the RT data are available within 30 minutes of overpass and the URT within 5 minutes. See also: [What time does the satellite pass over my area](https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-124369-8)?

FIRMS fire maps are updated every 5 minutes, and the SHP, KML and CSV files (available for the last 24 hours, 48 hours, and 7 days) are updated every 60 minutes. The first place data are posted is on the updated [daily fires text files](https://nrt3.modaps.eosdis.nasa.gov/archive/FIRMS). As explained [on the FIRMS active fire page,](https://firms.modaps.eosdis.nasa.gov/active_fire/) you will need an Earthdata Login to download data from this folder. FIRMS web services are generated on the fly and use the most recently processed data.
