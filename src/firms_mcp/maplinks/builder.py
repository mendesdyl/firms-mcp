"""Deterministic FIRMS Fire Map deep links (ADR-0006; FR-MAP-001 … FR-MAP-006).

The Fire Map keeps its state in the URL hash. The grammar below was derived from the map
application's own hash parser and serializer (map configuration 2.0.0, 2026-10-09) and
verified with cold page loads on both the global map (``/map/``) and the US/Canada map
(``/usfs/map/``)::

    #m:<mode>;d:<start>[..<end>];l:<layer>,<layer>,…;i:<w>,<s>,<e>,<n>
    #m:<mode>;d:<dates>;l:<layers>;@<lon>,<lat>,<zoom>z

* ``m:`` — map mode; omitted for the default Basic mode.
* ``d:`` — a preset (``today``, ``24hrs``, ``48hrs``, ``72hrs``, ``7days``), a date, or a
  range ``YYYY-MM-DD..YYYY-MM-DD`` (UTC days).
* ``l:`` — the visible layers. It **replaces** the defaults, so a basemap is always
  included. Per-satellite fire layers exist only in modes that list them (Advanced,
  Burned Area, Smoke, Experimental); Basic mode only knows ``fires_all``.
* ``i:`` — an area of interest; the map fits the view to it and draws the box.
* ``@lon,lat,zoomz`` — the view center (EPSG:4326) and zoom; must come last.
"""

from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from typing import Literal
from urllib.parse import urlencode

from pydantic import BaseModel, Field

from firms_mcp.firms.geo import BoundingBox, _fmt
from firms_mcp.firms.sources import get_source

BASE_URL = "https://firms.modaps.eosdis.nasa.gov"
REFERRAL = {"utm_source": "firms-mcp", "utm_medium": "mcp"}
PERIODS = ("today", "24hrs", "48hrs", "72hrs", "7days")
PERIOD_TEXT = {
    "today": "today (00:00 UTC to now)",
    "24hrs": "the last 24 hours (00:00 UTC yesterday to now)",
    "48hrs": "the last 48 hours",
    "72hrs": "the last 72 hours",
    "7days": "the last 7 days",
}
LINKABLE_MODES = ("basic", "advanced", "burned_area", "smoke", "experimental")
MapName = Literal["global", "us-canada"]
Period = Literal["today", "24hrs", "48hrs", "72hrs", "7days"]


@dataclass(frozen=True)
class MapCatalog:
    retrieved: str
    maps: dict[str, dict]
    modes: dict[str, dict]
    modules: dict[str, dict]
    layers: dict[str, dict]

    def allowed_layers(self, mode: str) -> frozenset[str]:
        """Layer IDs a mode can display: a module's explicit layer list, else its tag."""
        allowed: set[str] = set()
        for module_id in self.modes[mode].get("modules", []):
            module = self.modules.get(module_id, {})
            if module.get("layer_refs"):
                allowed.update(module["layer_refs"])
            elif module.get("tag"):
                allowed.update(
                    i for i, layer in self.layers.items() if layer["tag"] == module["tag"]
                )
        return frozenset(allowed & set(self.layers))

    def title(self, layer_id: str) -> str:
        return (self.layers.get(layer_id) or {}).get("title") or layer_id


@lru_cache(maxsize=1)
def load_catalog() -> MapCatalog:
    data = json.loads(
        resources.files("firms_mcp.maplinks").joinpath("catalog.json").read_text("utf-8")
    )
    return MapCatalog(
        retrieved=data["retrieved"],
        maps=data["maps"],
        modes={m["id"]: m for m in data["modes"]},
        modules={m["id"]: m for m in data["modules"]},
        layers={layer["id"]: layer for layer in data["layers"]},
    )


class FireMapLink(BaseModel):
    url: str
    map: MapName
    mode: str
    dates: str = Field(description="Value of the d: segment")
    layers: list[str]
    area: BoundingBox | None = None
    center: tuple[float, float] | None = Field(default=None, description="(longitude, latitude)")
    zoom: float | None = None
    description: str = Field(description="What the link will show, for the user")


class MapLinkError(ValueError):
    """Invalid link request; the message says what to change."""


def _dates_segment(
    period: str | None, start: dt.date | None, end: dt.date | None, today: dt.date
) -> tuple[str, str]:
    if period is not None and (start is not None or end is not None):
        raise MapLinkError("give either a period preset or start/end dates, not both")
    if start is None and end is None:
        chosen = period or "24hrs"
        if chosen not in PERIODS:
            raise MapLinkError(f"period must be one of {', '.join(PERIODS)}")
        return chosen, PERIOD_TEXT[chosen]
    start = start or end
    end = end or start
    assert start is not None and end is not None
    if start > end:
        raise MapLinkError("start date is after end date")
    if end > today:
        raise MapLinkError(f"end date {end.isoformat()} is in the future (today is {today} UTC)")
    if start == end:
        return start.isoformat(), f"{start.isoformat()} (UTC)"
    return (
        f"{start.isoformat()}..{end.isoformat()}",
        f"{start.isoformat()} to {end.isoformat()} (UTC)",
    )


def build_fire_map_link(
    *,
    area: BoundingBox | None = None,
    center: tuple[float, float] | None = None,
    zoom: float | None = None,
    period: str | None = None,
    start_date: dt.date | None = None,
    end_date: dt.date | None = None,
    sources: list[str] | None = None,
    extra_layers: list[str] | None = None,
    basemap: str = "earth",
    overlays: list[str] | None = None,
    mode: str | None = None,
    map_name: MapName = "global",
    referral: bool = True,
    today: dt.date | None = None,
) -> FireMapLink:
    """Build a Fire Map URL. ``sources`` are FIRMS API source IDs (shown per satellite)."""
    catalog = load_catalog()
    today = today or dt.datetime.now(dt.UTC).date()
    if map_name not in catalog.maps:
        raise MapLinkError(f"map must be one of {', '.join(catalog.maps)}")
    limits = catalog.maps[map_name]

    # Mode: per-satellite layers need a mode that lists them; Advanced is the general one.
    fire_layers: list[str] = []
    for source_id in sources or []:
        try:
            fire_layers.extend(get_source(source_id).map_layers)
        except ValueError as exc:
            raise MapLinkError(str(exc)) from exc
    chosen_mode = mode or ("advanced" if fire_layers else "basic")
    if chosen_mode not in LINKABLE_MODES:
        raise MapLinkError(f"mode must be one of {', '.join(LINKABLE_MODES)}")
    if not fire_layers and chosen_mode == "basic":
        fire_layers = ["fires_all"]

    overlays = ["country-outline"] if overlays is None else overlays
    layer_ids = list(dict.fromkeys([*fire_layers, *(extra_layers or []), *overlays, basemap]))
    allowed = catalog.allowed_layers(chosen_mode)
    unknown = [layer for layer in layer_ids if layer not in catalog.layers]
    if unknown:
        raise MapLinkError(f"unknown Fire Map layer(s): {', '.join(unknown)}")
    not_in_mode = [layer for layer in layer_ids if layer not in allowed]
    if not_in_mode:
        raise MapLinkError(
            f"layer(s) {', '.join(not_in_mode)} are not available in {chosen_mode} mode"
            + (
                " (per-satellite fire layers need mode 'advanced')"
                if chosen_mode == "basic"
                else ""
            )
        )
    if catalog.layers[basemap]["category"] != "basemap":
        raise MapLinkError(f"{basemap!r} is not a basemap")

    dates, dates_text = _dates_segment(period, start_date, end_date, today)
    segments = []
    if chosen_mode != "basic":
        segments.append(f"m:{chosen_mode}")
    segments.append(f"d:{dates}")
    segments.append("l:" + ",".join(layer_ids))

    if area is not None and center is not None:
        raise MapLinkError("give either an area or a center, not both")
    location = ""
    if area is not None:
        segments.append(
            "i:" + ",".join(_fmt(v) for v in (area.west, area.south, area.east, area.north))
        )
    else:
        lon, lat = center if center is not None else (0.0, 0.0)
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            raise MapLinkError("center must be (longitude, latitude) within valid ranges")
        zoom_value = zoom if zoom is not None else (3.0 if center is None else 8.0)
        if not limits["min_zoom"] <= zoom_value <= limits["max_zoom"]:
            raise MapLinkError(
                f"zoom must be between {limits['min_zoom']} and {limits['max_zoom']} for this map"
            )
        location = f"@{_fmt(round(lon, 4))},{_fmt(round(lat, 4))},{zoom_value:.1f}z"
        center, zoom = (lon, lat), zoom_value

    query = f"?{urlencode(REFERRAL)}" if referral else ""
    url = (
        f"{BASE_URL}{limits['path']}{query}#"
        + ";".join(segments)
        + (f";{location}" if location else "")
    )

    shown = [catalog.title(layer).strip() for layer in fire_layers] or ["no fire layers"]
    where = (
        f"the area west {_fmt(area.west)}, south {_fmt(area.south)}, east {_fmt(area.east)}, "
        f"north {_fmt(area.north)} (the map draws this box)"
        if area is not None
        else f"longitude {location[1:].split(',')[0]}, latitude {location.split(',')[1]} at zoom {zoom}"
    )
    description = (
        f"Opens the FIRMS {'US/Canada ' if map_name == 'us-canada' else ''}Fire Map "
        f"({catalog.modes[chosen_mode]['label']}) showing {', '.join(shown)} for {dates_text} "
        f"over {where}, on the {catalog.title(basemap)} basemap"
        + (f" with {', '.join(catalog.title(o) for o in overlays)}" if overlays else "")
        + ". The map, not this server, renders FIRMS data; times are UTC."
    )
    return FireMapLink(
        url=url,
        map=map_name,
        mode=chosen_mode,
        dates=dates,
        layers=layer_ids,
        area=area,
        center=center,
        zoom=zoom,
        description=description,
    )
