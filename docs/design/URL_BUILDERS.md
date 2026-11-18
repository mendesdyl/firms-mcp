# URL Builders — Design (iteration 2)

Implements [ADR-0011](../decisions/0011-keyless-scope-typescript-rewrite-standard-data-first.md)
§2, §4 and §7. Requirements: FR-URL-001 … FR-URL-004, FR-MAP-001 … FR-MAP-007,
FR-DATA-002, FR-DATA-008, FR-DATA-010, FR-DATA-011, FR-DATA-015. Running list: WK-22.

The builders are pure functions: they take the request, the date coverage, and today's
date, and return URLs with notes. They never fetch FIRMS data and never see a MAP_KEY. The
tools that call them (WK-23) fetch the coverage first.

| Module | Role |
|---|---|
| `src/sources/sources.json` | Language-neutral source catalog: sensors, SP and NRT sources, map layers, map-date keys, KML sensor names, knowledge entries, and the 2026-11-18 coverage snapshot |
| `src/sources/coverage.ts` | Coverage from the keyless map date service, with the snapshot as fallback |
| `src/sources/selection.ts` | Standard data first: per sensor and day, SP if it covers the day, else NRT, else nothing |
| `src/apiurls/area.ts` | Area API CSV URLs |
| `src/apiurls/kml.ts` | KML fire footprint links |
| `src/maplinks/` | Fire Map links and the layer catalog ([grammar](MAP_LINKS.md)) |
| `src/common/` | Dates, areas, the `[MAP_KEY]` placeholder, the limitations statement, related FIRMS pages |

## Coverage

`fetchCoverage` asks `https://firms.modaps.eosdis.nasa.gov/api/map_dates/` (keyless,
undocumented; LU-17) with a 10-second timeout. The result is presented as "the dates the
FIRMS Fire Map currently shows". On any failure (network, HTTP error, not JSON, unexpected
shape, nothing recognisable) it returns the snapshot from `sources.json` with
`checked: false` and a note that coverage could not be checked. If the service stops
listing one product, that product alone falls back to the snapshot, and the note names it.

## Standard data first

For each requested sensor, every day of the period gets one choice:

1. the sensor's standard-processing (SP) source, if SP coverage includes the day;
2. otherwise its NRT source, if NRT coverage includes the day;
3. otherwise nothing, reported in a note ("no data for … in the dates FIRMS lists").

Consecutive days with the same choice form a run. The notes say where SP ends and that
the NRT days after it are provisional, citing the FAQ entry
`faq.getting-started.what-are-the-key-differences-between-urt-rt-nrt-and-standard` by ID
rather than restating it. A user who explicitly asks for NRT gets NRT, with a note that SP
exists for those dates and is preferred. Landsat has no SP product and says so.

"The most recent N days" (API) and the map's period presets (`today` … `7days`) always use
NRT, with a note that SP cannot exist yet for those days.

## Area API URLs

```
/api/area/csv/[MAP_KEY]/<SOURCE>/<world | w,s,e,n>/<DAY_RANGE>[/<DATE>]
```

- `DAY_RANGE` is 1–5 (FIRMS limit), and `DATE … DATE+DAY_RANGE−1` is returned, so each run
  is cut into URLs of at most five days. A request may cover at most 31 days; longer
  periods are sent to the archive download page.
- Without dates, `recent_days` (1–5) builds the "most recent data" URL. A sensor whose NRT
  data stopped before that window (Suomi NPP after 2026-11-02) gets no URL and a note.
- Default sensors: VIIRS NOAA-20, VIIRS NOAA-21, VIIRS Suomi NPP, MODIS (Landsat is
  US/Canada only and must be asked for).
- Every result carries the MAP_KEY guidance (placeholder, sign-up page, where it goes), the
  fixed limitations statement, and the related pages: the `data_availability` URL, the
  missing-data page, the archive download page, and the MAP_KEY page.

## Fire Map links

Grammar and verification: [MAP_LINKS.md](MAP_LINKS.md). Without sensors or dates the link
is the map's own default (Basic mode, last 24 hours). With explicit dates the link uses
Advanced mode, where the SP layers live; each sensor shows its SP layer for days SP covers
and its NRT layer after that. Where any sensor's choice changes inside the period, the
period is split and one link is returned per stretch, so each link shows one consistent set
of layers.

## KML footprints

Keyless download links for 12 regions, four periods (24 h to 7 days), and five sensors;
Landsat only for Canada and the contiguous US + Hawaii (FIRMS page, checked 2026-11-18).
They are NRT only. Results say the link downloads a file for a GIS tool; the server
instructions (WK-23) offer KML only to users who work with such tools.
