"""FIRMS Fire Map deep links (ADR-0006)."""

from firms_mcp.maplinks.builder import (
    FireMapLink,
    MapLinkError,
    build_fire_map_link,
    load_catalog,
)

__all__ = ["FireMapLink", "MapLinkError", "build_fire_map_link", "load_catalog"]
