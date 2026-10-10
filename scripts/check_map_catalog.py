"""Check the shipped Fire Map catalog against the live FIRMS map (ADR-0006, risk R2).

    uv run python scripts/check_map_catalog.py

Downloads the Fire Map page, finds its application bundle, extracts the embedded map
configuration (layers, modes, modules), and reports layer IDs and modes that were added or
removed since src/firms_mcp/maplinks/catalog.json was captured. Exit status 1 if any layer
used by the link builder (fire layers, basemaps, default overlays) has disappeared.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "src" / "firms_mcp" / "maplinks" / "catalog.json"
MAP_URL = "https://firms.modaps.eosdis.nasa.gov/map/"
CRITICAL_PREFIXES = ("fires_",)
CRITICAL_IDS = {"earth", "street", "topo", "firefly", "country-outline"}


def _json_blobs(bundle: str) -> list:
    blobs = []
    for match in re.finditer(r"JSON\.parse\('((?:[^'\\]|\\.)*)'\)", bundle):
        text = match.group(1)
        for candidate in (text, text.replace("\\'", "'")):
            try:
                blobs.append(json.loads(candidate))
                break
            except json.JSONDecodeError:
                continue
    return blobs


def main() -> int:
    with httpx.Client(timeout=60, follow_redirects=True) as http:
        page = http.get(MAP_URL).text
        bundle_path = re.search(r"/dist/firms_map\.[0-9a-f]+\.js", page)
        if not bundle_path:
            print("could not find the map bundle in the page", file=sys.stderr)
            return 2
        bundle = http.get("https://firms.modaps.eosdis.nasa.gov" + bundle_path.group(0)).text
    blobs = _json_blobs(bundle)
    live_layers = {
        layer["id"]
        for blob in blobs
        if isinstance(blob, dict) and "properties" in blob
        for layer in blob.get("layers", [])
        if layer.get("id")
    }
    live_modes = {
        mode["id"]
        for blob in blobs
        if isinstance(blob, list) and blob and isinstance(blob[0], dict)
        for mode in blob
        if "modules" in mode or "urlRedirect" in mode
    }
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    shipped = {layer["id"] for layer in catalog["layers"]}
    shipped_modes = {mode["id"] for mode in catalog["modes"]}
    # Runtime-only layers (drawing tools, virtual groups) are not in the bundle config.
    missing = sorted(i for i in shipped - live_layers if not i.startswith(("_vl_", "draw")))
    added = sorted(live_layers - shipped)
    critical = [i for i in missing if i.startswith(CRITICAL_PREFIXES) or i in CRITICAL_IDS]
    print(f"bundle: {bundle_path.group(0)}")
    print(f"layers in live config: {len(live_layers)}; in shipped catalog: {len(shipped)}")
    print(f"added layers: {added or 'none'}")
    print(f"layers no longer configured: {missing or 'none'}")
    print(
        f"modes added: {sorted(live_modes - shipped_modes) or 'none'}; "
        f"removed: {sorted(shipped_modes - live_modes) or 'none'}"
    )
    if critical:
        print(f"CRITICAL: link-builder layers missing from the live map: {critical}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
