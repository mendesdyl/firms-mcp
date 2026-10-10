---
id: faq.swaths.do-geostationary-satellites-like-goes-also-image-the-earth-in
title: Do geostationary satellites (like GOES) also image the Earth in swaths?
kind: faq
section: swaths
section_title: Satellite Swaths and Coverage
source: firms-faq
source_url: https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-4409182-7
retrieved: '2026-10-09'
content_sha256: 54e96a55cca79f207a32d65a118aa79e13674c549e804cb9177285cad0f8a44d
order: 99
tags:
- geostationary
related: []
status: current
---

No, geostationary satellites operate very differently.

Satellites with MODIS and VIIRS instruments are in low-earth orbit (LEO) and fly from pole to pole, sweeping out "swaths" as the Earth rotates beneath them. In contrast, geostationary satellites (like the GOES network in the US, Meteosat in Europe, or Himawari in Japan) orbit much higher up — about 36,000 km (22,000 miles) above the equator. At this altitude, their orbital speed exactly matches Earth's rotation, meaning they effectively "stare" at the same hemisphere continuously.

Instead of imaging in swaths, geostationary instruments scan their entire field of view to create "full disk" images, or they can zoom in to rapidly scan smaller regional sectors. Similar to the viewing distortion at the edge of MODIS swaths, geostationary satellite imagery becomes increasingly distorted in all directions from the center of their view (nadir). Because they are constantly looking at the same area, geostationary satellites can provide new imagery every 1 to 10 minutes. While their spatial resolution (pixel size) is generally coarser than LEO swath data, this constant "staring" capability makes geostationary satellites incredibly valuable for FIRMS, as they can detect the exact moment a fire ignites and track its spread in real-time.
