---
id: faq.hls.what-hls-products-are-available-in-firms
title: What HLS products are available in FIRMS?
kind: faq
section: hls
section_title: Harmonized Landsat Sentinel-2 (HLS) imagery in FIRMS
source: firms-faq
source_url: https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-4409166-3
retrieved: '2026-10-09'
content_sha256: 85d32257ff700fd4fcbdd3b815128f33be40028220f82c21c35355c23c0d7374
order: 82
tags:
- landsat
- hls
related: []
status: current
---

FIRMS offers several 30-meter resolution HLS products, including true-color and false-color reflectance images. In addition, FIRMS features four specific vegetation indices (VIs) for both Landsat 8/9 and Sentinel-2:

- NDVI: Normalized Difference Vegetation Index
- NDMI: Normalized Difference Moisture Index
- NBR: Normalized Burn Ratio
- NBR2: Normalized Burn Ratio 2

Additionally, the "Customize HLS Bands" option allows the user to assign their selected band to each RGB channel. See the FAQ “What are the bands used/available in HLS products?” for band for band references when configuring a composite HLS image when using the “Customize HLS Bands” option.

| Imagery / vegetation indices | Band Combination |
|---|---|
| True Color - Adjusted Reflectance BRDF | Bands B2, B3, B4 (Sentinel-2)<br>Bands B2, B3, B4 (Landsat 8/9) |
| False Color - Adjusted Reflectance BRDF | Bands B12, B8a, B4 (Sentinel-2)<br>Bands B7, B5, B4 (Landsat) |
| NDVI - Normalized Difference Vegetation Index<br><br>Uses the Red band and Near-Infrared (NIR) band. (Value range from -1 to 1) | Bands (B8A – B4) / (B8A + B4) (Sentinel-2)<br>Bands (B5 – B4) / (B5 + B4) (Landsat) |
| NDMI - Normalized Difference Moisture Index<br>Uses the Near-Infrared (NIR) band and the 1.6 µm Shortwave Infrared (SWIR) band. (Value range: -1 to 1). | Bands (B8A-B11) / (B8A + B11) (Sentinel-2)<br>(Band 5 - Band 6) / (Band 5 + Band 6) (Landsat) |
| NBR - Normalized Burn Ratio<br>Uses the Near-Infrared (NIR) band and the 2.1 µm Shortwave Infrared (SWIR) band. (Value range: -1 to 1) | Bands (B8A – B12) / (B8A + B12) (Sentinel-2)<br>Bands (B5 – B7) / (B5 + B7) (Landsat) |
| NBR2 - Normalized Burn Ratio 2<br>Uses the Near-Infrared (NIR) band and the 2.1 µm Shortwave Infrared (SWIR) band. (Value range: -1 to 1) | Bands (B11 – B12) / (B11 + B12) (Sentinel-2)<br>Bands (B6 – B7) / (B6 + B7) (Landsat) |
