---
id: faq.geostationary.can-you-provide-a-brief-description-of-the-two-algorithms-used
title: Can you provide a brief description of the two algorithms used to produce geostationary active fire products from GOES-16 and 19?
kind: faq
section: geostationary
section_title: Geostationary Active Fire Data
source: firms-faq
source_url: https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-124520-9
retrieved: '2026-10-09'
content_sha256: 168959490520ffd518e5645c5ac0ab421729fcd03dc1a549d168c880e188c07b
order: 68
tags:
- geostationary
related:
- faq.geostationary.what-is-the-spatial-resolution-of-the-geostationary-satellite
status: current
---

### FRP-PIXEL Product

The key outputs from the FRP-PIXEL algorithm are active fire pixel detections and fire characteristics including fire radiative power (FRP), FRP uncertainty, active fire temperature, and fire detection confidence levels. The detection algorithm used in the FRP-PIXEL product is based on the principles applied to generate active fire detections within the MODIS Fire Products (Giglio et al., 2003). The algorithm works on statistics derived primarily from middle-infrared (MIR) and thermal infrared (TIR1) brightness temperature imagery. On a first pass, a series of absolute thresholds applied to these data are used to detect “potential” fire pixels. These pixels are then further assessed as true or false fire detections based on a series of further contextual tests based on statistics derived from immediate neighboring non-fire background pixels. Further description of the algorithm can be found in (Govaerts et al., 2010; Wooster et al., 2015).

The FRP-PIXEL product is available every 15 minutes for the SEVIRI full-disk and every 10 minutes for the AHI and ABI disks. The spatial resolution of the product at the sub-satellite point is 3-km for the SEVIRI data and 2-km for the AHI and ABI, but the pixel size systematically grows with increasing view zenith angle (VZA) from the sub-satellite point towards the edge of the disk (See: [What is the spatial resolution of the geostationary satellite observations](https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-124520-6)?).

### FDC-HSC Product

The key outputs from the FDC-HSC algorithm include information on the fire pixel locations, sub-pixel fire characteristics (active fire area and temperature), and FRP. The current FDC-HSC algorithm is a multispectral contextual algorithm designed to identify fire pixels through a decision-tree approach comparing them with their neighboring non-fire background pixels. The FDC-HSC algorithm uses a two-step approach. The first step is designed to identify all potential fire pixels while the second step further confirms and then characterizes the sub-pixel fire activity. The FDC-HSC product is available every 10 minutes. The spatial resolution of the product at the sub-satellite point is 2km, and the pixel size systematically grows with increasing VZA from the sub-satellite point towards the edge of the disk.The FDC-HSC product is available every 10 minutes. The spatial resolution of the product at the sub-satellite point is 2km, and the pixel size systematically grows with increasing VZA from the sub-satellite point towards the edge of the disk.

### What are the Product Uncertainties and Limitations?

The FRP-PIXEL and FDC-HSC products are subject to several sources of uncertainties due to the characteristics of geostationary satellite full-disk data and associated image processing. Among these limitations:

- The spatial resolution of the data leads to missed smaller/less intense fires. Furthermore, the sensitivity to small/less intense fires decreases away from the sub-satellite point.
- The FRP-derived value is sensitive to the fire location within the pixel. This effect is due to the shape of the point spread function, i.e., its departure from an ideal rectangular box. A fire located at the center of the instrument’s instantaneous field-of-view will elevate the pixel temperature much more than a fire located far away from its center.
- Specific to the FRP, the non-linearity of the SEVIRI 3.9-μm channel above 310 K and the saturation of that band above 335 K can produce errors in the FRP estimate. Similarly, the saturation of the GOES-R ABI and AHI 3.9-μm channel above 400 K can produce errors in FRP.
