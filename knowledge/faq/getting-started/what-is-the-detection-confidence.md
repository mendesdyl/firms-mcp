---
id: faq.getting-started.what-is-the-detection-confidence
title: What is the detection confidence?
kind: faq
section: getting-started
section_title: Getting Started
source: firms-faq
source_url: https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-124369-15
retrieved: '2026-10-09'
content_sha256: d6574428aea2b89d1a968bbe35cbcd9743e9c8cdc09c2f879114586080cfcebd
order: 15
tags:
- confidence
related: []
status: current
---

The confidence value was added to help users gauge the quality of individual fire pixels included in the Level 2 fire product. The confidence field should be used with caution as it is likely that it will vary in terms of meaning in different parts of the world. Nevertheless, some of our end users have found such a field to be useful in excluding false positive occurrences of fire. The confidence values are attributed differently for MODIS and VIIRS.

For MODIS, the confidence value ranges from 0% to 100% and can be used to assign one of the three fire classes (low-confidence fire, nominal-confidence fire, or high-confidence fire) to all fire pixels. For some uses or applications, errors of commission (or false alarms) are particularly undesirable, and for these applications a user may consider trading a lower detection rate to gain a lower false alarm rate.

Conversely, for other applications missing any fire might be especially undesirable, and a user may be willing to tolerate a higher false alarm rate to ensure that fewer true fires are missed. Users requiring fewer false alarms may wish to retain only nominal- and high-confidence fire pixels and treat low-confidence fire pixels as non-fire, land pixels. Users requiring maximum fire detectability who are able to tolerate a higher incidence of false alarms should consider all three classes of fire pixels.

For VIIRS, the confidence values are set to low, nominal, and high; they are based on a collection of intermediate algorithm quantities used in the detection process and are intended to help users gauge the quality of individual hotspot/fire pixels. Low confidence daytime fire pixels are typically associated with areas of Sun glint and lower relative temperature anomaly (<15 K) in the mid-infrared channel I4. Nominal confidence pixels are those that are free of potential Sun glint contamination during the day and marked by strong (>15 K) temperature anomaly in either day or nighttime data. High confidence fire pixels are associated with day or nighttime saturated pixels.

While the confidence value may not be very helpful for all users or applications, there is no way to establish an optimal cutoff a priori. Users have to adopt an empirical approach—what threshold works best for what I'm trying to do?
