/** West, south, east, north boxes in decimal degrees (WGS84), as the FIRMS API expects. */
import { UrlBuilderError } from "./errors.js";

export interface BoundingBox {
  west: number;
  south: number;
  east: number;
  north: number;
}

/** Compact decimal text without float noise: 10 → "10", 0.1 → "0.1", -0 → "0". */
export function formatNumber(value: number): string {
  const text = value.toFixed(6).replace(/\.?0+$/, "");
  return text === "-0" || text === "" ? "0" : text;
}

function checkCoordinate(value: number, field: string, limit: number): void {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new UrlBuilderError(`${field} must be a number`);
  }
  if (value < -limit || value > limit) {
    throw new UrlBuilderError(`${field} must be between -${limit} and ${limit} (got ${value})`);
  }
}

export function checkBox(box: BoundingBox): BoundingBox {
  checkCoordinate(box.west, "west", 180);
  checkCoordinate(box.south, "south", 90);
  checkCoordinate(box.east, "east", 180);
  checkCoordinate(box.north, "north", 90);
  if (box.west >= box.east) {
    throw new UrlBuilderError(
      "west must be less than east (an area that crosses the antimeridian must be split into two requests)",
    );
  }
  if (box.south >= box.north) throw new UrlBuilderError("south must be less than north");
  return box;
}

export function formatBox(box: BoundingBox): string {
  return [box.west, box.south, box.east, box.north].map(formatNumber).join(",");
}

/** FIRMS `AREA_COORDINATES`: `world`, or `west,south,east,north`. */
export function areaCoordinates(area: BoundingBox | "world"): string {
  if (area === "world") return "world";
  const box = checkBox(area);
  const isWorld = box.west === -180 && box.south === -90 && box.east === 180 && box.north === 90;
  return isWorld ? "world" : formatBox(box);
}
