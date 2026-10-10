---
id: faq.experimental.what-is-the-viirs-modeled-fire-perimeter-product
title: What is the VIIRS Modeled Fire Perimeter product?
kind: faq
section: experimental
section_title: Experimental Mode
source: firms-faq
source_url: https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-128876-1
retrieved: '2026-10-09'
content_sha256: 74a0617373db9b2a142ee03a5a67fae582b889cab9ac8522820ef8ee3d1657aa
order: 124
tags:
- viirs
- perimeter
related: []
status: current
---

The VIIRS Modeled Fire Perimeter Product uses the Fire Event Database Suite (FEDS) algorithm ([Chen et al., 2022](https://doi.org/10.1038/s41597-022-01343-0)) to cluster VIIRS 375 m active fire detection data into individual fire events and track fire spread and behavior every 12 hours (see Figure 1). The FEDS algorithm uses an alpha shape approach to model the fire perimeter, estimate the active portion of the fire perimeter, and quantify metrics of fire behavior for each 12-hour time step. The FEDS algorithm currently uses the 375 m active fire detections from the VIIRS sensors onboard the Suomi-NPP and NOAA-20 satellites to model the fire perimeter.

![Two fire data visualizations appear side by side, each overlaid with colored and grey dots, which represent newly detected and previously detected VIIRS 375 m active fire pixels.](https://earthdata.nasa.gov/s3fs-public/2024-12/feds-fire-tracking-diagram-firms.png?VersionId=7Eib4PyD9kYk8RmDyNEIGDNntwM_FuSP)

*Image caption:* Figure 1. A schematic diagram of the FEDS fire tracking algorithm (Chen et al., 2022). (a) Two idealized fire objects (Fire 1, Fire 2) at the time step t. Colored and grey dots represent newly detected and previously detected VIIRS 375 m active fire pixels, respectively. The brown segments along the fire perimeter are the modeled estimate of the active portions of the fire perimeter. (b) At the next time step t+1, new fire pixels (in red) are clustered (C1, C2, C3), and are used for forming a new fire object (C1 for Fire 3), or for the growth of an existing fire object (C2 for Fire 1). Expanded fire objects (Fire 2) are merged with an existing active fire object (Fire 1) if they grow close enough (due to the addition of C3). Vector shapes of the modeled fire perimeter and active fire line segments for each fire object are updated at each 12-hour time step.

The VIIRS Modeled Fire Perimeter data based on the FEDS algorithm includes three different types of information about each ongoing fire event in the Continental United States (CONUS) and Canada, updated approximately four hours after each VIIRS overpass: 1) the modeled perimeter of each large fire event, 2) the active portion of the modeled fire perimeter (i.e., the active fire line or “hot edge” of the modeled fire perimeter), and 3) the instantaneous fire radiative power (FRP) from all active fire detections associated with a given fire event during each overpass time, including fire detections at the hot edge and residual flaming or smoldering activity within the modeled fire perimeter (see Figure 1a).

By clustering and tracking fire detections into individual fire events, the FEDS algorithm provides a consistent assessment of the change in fire behavior and intensity with each successive VIIRS overpass (nominally at 01:30 and 13:30 local time).

For additional information, please see the [Wildfire Tracking Lab GitHub project page](https://earth-information-system.github.io/fireatlas/docs/) and the [UC-I/NASA Fire Tracking Page](https://www.ess.uci.edu/~uci-nasa-firetracking/).
