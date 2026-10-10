---
id: faq.getting-started.why-do-i-sometimes-see-linear-patterns-of-large-numbers-of
title: Why do I sometimes see linear patterns of large numbers of active fire detections?
kind: faq
section: getting-started
section_title: Getting Started
source: firms-faq
source_url: https://www.earthdata.nasa.gov/data/tools/firms/faq#heading-accordion-124369-19
retrieved: '2026-10-09'
content_sha256: abcb89e99ac7fc11d15b00f40d9269f650fbc7e77284ada9304df2666814f009
order: 19
tags: []
related: []
status: current
---

NASA and NOAA routinely conduct on-orbit mission calibration maneuvers for MODIS, VIIRS, etc. to maintain consistent geometric and radiometric performance for production of science data. Primarily for radiometric calibration purposes, on a near monthly basis the sensor's typical perspective of the Earth’s is changed to view the Moon. This is conducted by physically rolling the satellite/spacecraft over in orbit for a short period of time to observe the Moon.

The illumination of the Moon's surface by the Sun during these maneuvers is used to calibrate the reflective solar bands of the sensor. Upon completion of these maneuvers the satellite rolls back to point the sensor at Earth. At that instant, it is not uncommon for anomalous observation data to be collected by the reflective and thermal bands. This situation can result in linear patterns of large numbers of anomalous active fire detection data within a MODIS or VIIRS swath as show in the example below.

![Spurious fire detections](https://earthdata.nasa.gov/s3fs-public/2023-11/Spurious%20fires%20093023.png?VersionId=E56mhz.wyEpcaknnWku13OxYrLYAdrGT)

NASA FIRMS makes every effort to filter and remove these anomalous detections from the data stream in real-time when they are detected. However, on rare occasions it is possible for some of these detections to temporarily appear in the FIRMS data viewer and datasets before they are removed.
