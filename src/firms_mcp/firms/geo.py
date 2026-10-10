"""Geographic areas for FIRMS queries and map links."""

from __future__ import annotations

import math

from pydantic import BaseModel, ConfigDict, Field, model_validator


def _fmt(value: float) -> str:
    """Compact decimal formatting without float noise (e.g. 10.0 -> '10', 0.1 -> '0.1')."""
    text = f"{value:.6f}".rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


class BoundingBox(BaseModel):
    """A west, south, east, north box in decimal degrees (WGS84), as the FIRMS API expects."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    west: float = Field(ge=-180, le=180)
    south: float = Field(ge=-90, le=90)
    east: float = Field(ge=-180, le=180)
    north: float = Field(ge=-90, le=90)

    @model_validator(mode="after")
    def _ordered(self) -> BoundingBox:
        if self.west >= self.east:
            raise ValueError(
                "west must be less than east (boxes that cross the antimeridian must be "
                "split into two queries)"
            )
        if self.south >= self.north:
            raise ValueError("south must be less than north")
        return self

    @classmethod
    def world(cls) -> BoundingBox:
        return cls(west=-180, south=-90, east=180, north=90)

    @property
    def is_world(self) -> bool:
        return (self.west, self.south, self.east, self.north) == (-180, -90, 180, 90)

    def to_api(self) -> str:
        """FIRMS ``AREA_COORDINATES``: ``world`` or ``west,south,east,north``."""
        if self.is_world:
            return "world"
        return ",".join(_fmt(v) for v in (self.west, self.south, self.east, self.north))

    @property
    def center(self) -> tuple[float, float]:
        """(longitude, latitude) of the box center."""
        return ((self.west + self.east) / 2, (self.south + self.north) / 2)

    @property
    def width_degrees(self) -> float:
        return self.east - self.west

    @property
    def height_degrees(self) -> float:
        return self.north - self.south

    def contains(self, longitude: float, latitude: float) -> bool:
        return self.west <= longitude <= self.east and self.south <= latitude <= self.north

    def approximate_zoom(self) -> float:
        """A Fire Map zoom level that shows the whole box (EPSG:4326 map, 256-px tiles)."""
        span = max(self.width_degrees, self.height_degrees * 2)
        zoom = math.log2(360 / max(span, 1e-6)) + 1
        return round(min(max(zoom, 2.0), 15.0), 1)

    @classmethod
    def around(cls, data: list[tuple[float, float]]) -> BoundingBox | None:
        """Smallest box containing (longitude, latitude) points, or None for no points."""
        if not data:
            return None
        lons = [p[0] for p in data]
        lats = [p[1] for p in data]
        west, east = min(lons), max(lons)
        south, north = min(lats), max(lats)
        # A single point has zero size; widen minimally so the box stays valid.
        if west == east:
            west, east = max(west - 0.001, -180), min(east + 0.001, 180)
        if south == north:
            south, north = max(south - 0.001, -90), min(north + 0.001, 90)
        return cls(west=west, south=south, east=east, north=north)


def parse_area(value: str) -> BoundingBox:
    """Parse ``world`` or ``west,south,east,north``."""
    text = value.strip().lower()
    if text == "world":
        return BoundingBox.world()
    parts = [p.strip() for p in text.split(",")]
    if len(parts) != 4:
        raise ValueError("area must be 'world' or 'west,south,east,north'")
    try:
        west, south, east, north = (float(p) for p in parts)
    except ValueError as exc:
        raise ValueError("area coordinates must be numbers") from exc
    return BoundingBox(west=west, south=south, east=east, north=north)
