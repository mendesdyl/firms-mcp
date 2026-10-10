# FIRMS Data Products — Scientific Baseline

This document is the project's technical baseline of the FIRMS products the server
exposes (ARL1-M2, "baseline support research identified and documented"). It is written
for developers and reviewers. **It is not served to agents**: agents receive FIRMS's own
wording through the [knowledge base](../../knowledge/README.md). Each statement below cites
the FIRMS FAQ question (by title, in quotation marks) or service it was taken from; see
[References](../research/REFERENCES.md) for URLs and retrieval dates. Where two FIRMS
sources disagree, both are recorded rather than reconciled.

## 1. What a detection is

- Each detection "represents the center of a pixel flagged as containing one or more
  fires or other thermal anomalies (such as volcanoes)". The reported location is the pixel
  center, "not necessarily the coordinates of the actual fire"; the fire is often smaller
  than the pixel; FIRMS "[is] not able to determine the exact location or size of the
  fire". Several detections in a line generally represent a fire front. — "What does a
  fire detection mean on the ground?"
- Not all detections are vegetation fires: volcanoes, gas flares, and industrial sources
  also trigger detections, and the type is not attributed in NRT MODIS or VIIRS data. —
  "Are all active fire hotspots vegetation fires?"; "What is a Static Thermal Anomaly (STA)?"
- The FIRMS Fire Map's disclaimer: *"Do not use for the preservation of life or
  property. Satellite-derived active fire / thermal anomalies have limited accuracy."*
  — FIRMS Fire Map dialog (captured 2026-10-09).

Implication for the server: the server never describes a detection as "a fire of size X
at location Y"; it reports pixel-center detections with their sensor, footprint
(`scan`/`track`), time, confidence, and caveats.

## 2. Detection sources available through the FIRMS area API

| API `SOURCE` | Instrument / platform | Nominal pixel | Coverage | Record start (per FAQ) | Record start (per map date service, 2026-10-09) | Processing |
|---|---|---|---|---|---|---|
| `VIIRS_SNPP_NRT` | VIIRS / Suomi NPP | 375 m | Global | — | 2019-09-01 (NRT) | URT+NRT |
| `VIIRS_SNPP_SP` | VIIRS / Suomi NPP | 375 m | Global | 2012-01-20 | 2012-01-20 → 2026-06-30 | Standard |
| `VIIRS_NOAA20_NRT` | VIIRS / NOAA-20 (JPSS-1) | 375 m | Global | — | 2019-12-04 (NRT) | URT+NRT |
| `VIIRS_NOAA20_SP` | VIIRS / NOAA-20 | 375 m | Global | 2020-01-01 | 2018-04-01 → 2026-06-30 | Standard |
| `VIIRS_NOAA21_NRT` | VIIRS / NOAA-21 (JPSS-2) | 375 m | Global | 2024-01-17 | 2024-01-17 (NRT) | URT+NRT |
| `MODIS_NRT` | MODIS / Terra + Aqua, Collection 6.1 (MCD14DL) | 1 km | Global | — | 2020-11-01 (NRT) | URT+NRT |
| `MODIS_SP` | MODIS / Terra + Aqua, MCD14ML (University of Maryland) | 1 km | Global | Terra Nov 2000; Aqua Jul 2002 | 2000-11-01 → 2026-07-31 | Standard, 2–3 month lag |
| `LANDSAT_NRT` | OLI / Landsat 8 + 9 | 30 m | US/Canada ("most of North America (CONUS, southern Canada and northern Mexico)") | June 2022 | 2022-06-20 | NRT |

Sources: FIRMS area API page; "For what dates are the fire data available?"; "What are the
different sources of MODIS and VIIRS active fire data in FIRMS?"; "What is the temporal
extent of Landsat Active Fire and Thermal Anomalies product in FIRMS?"; `/api/map_dates/`.

**Recorded discrepancy:** the FAQ gives 1 January 2020 as the start of NOAA-20 VIIRS data,
while the map date service and the Fire Map layer configuration (`minDate: 2018-04-01`)
indicate standard-processing NOAA-20 data from 2018-04-01. The server reports live
availability from FIRMS rather than either constant (running-list item LU-10).

Geostationary detections (GOES-East/West NOAA FDC and KCL/IPMA FRP-PIXEL, Meteosat
SEVIRI and MTG FCI, Himawari AHI) are present in FIRMS maps as *provisional* products but
are not listed as area-API sources on 2026-10-09 (running-list item LU-07).

## 3. Timing, revisit, and latency

| Sensor | Revisit | Equator crossing (mean local time) | Source |
|---|---|---|---|
| MODIS (2,330 km swath) | Global every 1–2 days; ≥4 observations per day near the equator, more toward the poles | Terra ~10:30 / 22:30; Aqua ~13:30 / 01:30 | "How often are MODIS and VIIRS active fire data acquired?" |
| VIIRS (3,040 km swath) | Global every 12 hours; mid-latitudes 3–4 looks per day | Suomi NPP ~13:30 / 01:30; NOAA-20/21 ~50 min ahead (~12:40 / 00:40) | same |
| Landsat 8 / 9 OLI | Each satellite 16 days; combined 8 days | Daytime (night by request) | "What is the temporal frequency of Landsat observations…?" |

| Product tier | Availability after observation | Coverage | Source |
|---|---|---|---|
| NRT (LANCE) | within 3 hours (best effort) | Global | "How often is FIRMS updated?" |
| RT (direct broadcast) | within 30 minutes (EOSDIS RT definition: within 60 minutes) | US/Canada | "What are the real-time (RT) and ultra real-time (URT) data in FIRMS?" |
| URT (direct readout, SSEC) | within ~1–5 minutes | Most of conterminous US, S. Canada, N. Mexico | same; "Are URT data provided for all FIRMS products?" |
| Landsat NRT | 30–60 minutes | US/Canada | FIRMS Global table |
| Standard (science quality) | months (MODIS 2–3 months) | Global | "I only see fire data available for the last 7 days…" |

NRT replaces URT/RT as it arrives; "RT and URT data are removed when corresponding NRT
detections are processed or RT/URT is older than 6 hours" (area API page). The `version`
attribute distinguishes them (e.g. `6.1URT`, `6.1RT`, `6.1NRT`, `6.1`).

All dates and times in FIRMS data are **UTC** ("What is UTC?"; attribute pages). The Fire
Map's "Today" means 00:00 UTC to now and "24 hours" means 00:00 UTC yesterday to now
("What does today vs 24 hours mean?").

## 4. Attributes

From the attribute page for NRT MODIS and VIIRS data and the Landsat attribute table in the
FAQ. Field names are as delivered in CSV (lower-case).

| Field | MODIS | VIIRS 375 m | Landsat | Meaning |
|---|---|---|---|---|
| `latitude`, `longitude` | ✓ | ✓ | ✓ | Pixel center (decimal degrees, WGS84) |
| `brightness` / `bright_ti4` | channel 21/22 BT (K) | I-4 BT (K) | — | Brightness temperature |
| `bright_t31` / `bright_ti5` | channel 31 BT (K) | I-5 BT (K) | — | Second brightness temperature |
| `scan`, `track` | ✓ | ✓ | ✓ (OLI line-of-sight pixel location) | Actual pixel size along scan / track (MODIS, VIIRS) |
| `acq_date`, `acq_time` | ✓ | ✓ | ✓ | Acquisition date and time, UTC (`acq_time` as HHMM) |
| `satellite` | `A` = Aqua, `T` = Terra (attribute page) † | `N` = Suomi NPP, `N20` = NOAA-20, `N21` = NOAA-21 (attribute page) † | `L8` / `L9` | Platform |
| `confidence` | 0–100 % | low / nominal / high † | `H` / `M` / `L` | See §5 |
| `version` | e.g. `6.1NRT`, `6.1URT`, `6.1` | collection + source suffix † | e.g. `1.0.7 NRT` | Collection and processing source |

† Values as documented on the attribute pages. The literal encodings in area-API CSV
responses (for example full platform names versus codes, or `l`/`n`/`h` versus words) are
to be confirmed against live responses (running-list item LU-03); the parser accepts both
forms.
| `frp` | ✓ MW | ✓ MW | — | Fire radiative power, pixel-integrated |
| `daynight` | ✓ | ✓ | ✓ | `D` / `N` |
| `type` | SP only | — | — | 0 vegetation, 1 volcano, 2 other static land source, 3 offshore |
| `path`, `row` | — | — | ✓ | WRS-2 path and row |

The exact CSV headers for each API source are to be confirmed against live responses
(running-list item LU-03). The server's parser tolerates missing optional columns and
records unknown columns rather than dropping them.

**Day/night caveat (MODIS):** standard processing assigns night when solar zenith angle
exceeds 85°; NRT assigns day/night by ascending vs descending orbit. — "What are the key
differences between URT/RT/NRT and Standard quality fire data?"

**Geolocation caveat (NRT):** NRT positions are usually within ~100 m of standard
positions but can be off by several kilometres after spacecraft maneuvers or space-weather
events (up to 12 hours for MODIS/Aqua; under 2 hours for the others). — same question.

## 5. Confidence

- MODIS: 0–100 %, mapped to low / nominal / high classes; FIRMS notes the field "should be
  used with caution" and that there is "no way to establish an optimal cutoff a priori". —
  "What is the detection confidence?" The class thresholds are given in the MODIS
  Collection 6 and 6.1 Active Fire Product User's Guide v1.0 (Giglio, Schroeder, Hall,
  Justice; May 2021), §8.4.3, Table 11: **low 0 % ≤ C < 30 %, nominal 30 % ≤ C < 80 %,
  high 80 % ≤ C ≤ 100 %** (verified against the PDF 2026-10-09).
- VIIRS: low / nominal / high. Low (daytime) is associated with sun glint and weak (<15 K)
  I4 anomalies; nominal is free of sun glint with >15 K anomaly; high is associated with
  saturated pixels. — same question and attribute page; the VIIRS Collection 2 375 m Active
  Fire Product User's Guide v1.2 encodes these as fire-mask classes 7, 8, 9.
- Landsat: H / M / L. — Landsat attribute table.
- Geostationary FDC: classes 10–15 / 30–35; FIRMS shows only 10/30 and 11/31. — "Why are
  the geostationary fire data filtered in FIRMS?"

The server therefore exposes confidence as delivered, offers optional filtering that the
caller must request explicitly, and never applies a threshold silently.

## 6. Known false detections and gaps

| Phenomenon | Effect | FAQ question |
|---|---|---|
| Super-heated smoke plumes (night, very large fires, high scan angle) | VIIRS detections displaced outside the fire perimeter (parallax) | "Are there ever false fire detections or data artifacts?" |
| Sun glint, bright surfaces | Conservative tests reduce false alarms; some residual | same; "Will the VIIRS 375 m … always outperform the 750 m one?" |
| South Atlantic Magnetic Anomaly | Isolated spurious VIIRS night pixels (2–3 per night); low-confidence night pixels removed from FIRMS NRT | "Are those few isolated fire pixels in the middle of the South Atlantic Ocean real?"; attribute page |
| Calibration maneuvers | Linear patterns of spurious detections, normally filtered | "Why do I sometimes see linear patterns…?" |
| Clouds, heavy smoke, canopy | Fires missed | "Why was a particular fire not detected?"; "Can active fires be detected below the forest canopy?" |
| Timing between overpasses | Short fires missed | same |
| Instrument outages | Missing days | "How do I know if a fire detection was missed due to cloud or missing data?"; FIRMS missing-data table |
| Swath edges | Larger pixels, less precise location (MODIS bow-tie); VIIRS limits growth | "Does the location of a fire within the swath affect the detection?" |
| Geostationary products | Spurious detections from sun glint, water, deserts, coastlines; filtered and provisional | "Why are the geostationary fire data filtered in FIRMS?" |

## 7. Minimum detectable fire size

- MODIS: routinely ~1,000 m²; ~100 m² under very good conditions; ~50 m² under pristine
  conditions. — "What size fires can be detected?"
- Landsat: ~4 m² (>50 % detection probability, day); ~1 m² at night. — "What size of fires
  can be detected with Landsat?"
- GOES: ~4,000 m² theoretical at nadir, 800 K; Meteosat: ~900 m². — "What size fires can
  be detected with geostationary satellite observations?"

## 8. Uses FIRMS advises against

- Estimating burned area from active fire detections ("Can I estimate burned area from
  active fire data?").
- Treating detections as fire perimeters; cumulative detections tend to overestimate fire
  size and may fall outside official perimeters ("How do I interpret/use wildfire perimeter
  data in the context of satellite active fire detection data?").
- Life-safety decisions (Fire Map disclaimer).

## 9. Attribution

FIRMS asks that imagery be credited "NASA FIRMS", and that scientific publications use:
*"We acknowledge the use of imagery from the NASA LANCE FIRMS
(https://earthdata.nasa.gov/firms), part of the NASA Earth Science Data and Information
System (ESDIS)."* — "Are there any restrictions on using data or imagery from FIRMS?"
The server returns this text with every data response.
