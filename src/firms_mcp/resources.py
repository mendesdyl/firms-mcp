"""Resources for hosts that let users attach context (FR-KB-010; ADR-0005).

* ``firms://knowledge/index`` — table of contents (JSON)
* ``firms://knowledge/{entry_id}`` — one entry: its title as a heading, FIRMS's text
  verbatim, then a provenance line (Markdown)
* ``firms://sources`` — the detection source catalog (JSON)

All three are static for a given server version, so list and read results carry a public
cache hint (set on the server).
"""

from __future__ import annotations

import json

from fastmcp import FastMCP
from fastmcp.exceptions import ResourceError

from firms_mcp.services import Services
from firms_mcp.tools.get_fire_data_sources.models import GetFireDataSourcesInput
from firms_mcp.tools.get_fire_data_sources.tool import get_fire_data_sources


def render_entry(services: Services, entry_id: str) -> str:
    entry = services.knowledge.get(entry_id)
    if entry is None:
        suggestions = services.knowledge.suggestions(entry_id)
        hint = f" Closest IDs: {', '.join(suggestions)}." if suggestions else ""
        raise ResourceError(f"No knowledge entry {entry_id!r}.{hint}")
    status = (
        " This entry is retired: FIRMS no longer publishes it." if entry.status == "retired" else ""
    )
    return (
        f"# {entry.title}\n\n{entry.body}\n\n---\n\n"
        f"Source: {entry.source_url} (retrieved {entry.retrieved.isoformat()}). "
        f"Knowledge entry `{entry.id}`, SHA-256 {entry.content_sha256}.{status}\n"
    )


def knowledge_index(services: Services) -> dict:
    knowledge = services.knowledge
    return {
        "sections": [
            {
                "id": section.id,
                "title": section.title,
                "entries": [
                    {"id": entry_id, "title": knowledge.get(entry_id).title}  # type: ignore[union-attr]
                    for entry_id in section.entry_ids
                ],
            }
            for section in knowledge.sections()
        ],
        "sources": [
            {"id": s.id, "title": s.title, "url": s.url, "retrieved": s.retrieved.isoformat()}
            for s in knowledge.sources.values()
        ],
        "entry_uri_template": "firms://knowledge/{entry_id}",
    }


def register_resources(mcp: FastMCP, services: Services) -> None:
    @mcp.resource(
        "firms://knowledge/index",
        name="knowledge_index",
        title="FIRMS knowledge base index",
        description="Sections and entries of the verbatim FIRMS knowledge base, with sources",
        mime_type="application/json",
    )
    def _index() -> str:
        return json.dumps(knowledge_index(services), ensure_ascii=False)

    @mcp.resource(
        "firms://knowledge/{entry_id}",
        name="knowledge_entry",
        title="FIRMS knowledge entry",
        description="One FIRMS documentation entry, verbatim, with its source",
        mime_type="text/markdown",
    )
    def _entry(entry_id: str) -> str:
        return render_entry(services, entry_id)

    @mcp.resource(
        "firms://sources",
        name="fire_data_sources",
        title="FIRMS detection sources",
        description="Catalog of FIRMS area-API detection sources (as get_fire_data_sources)",
        mime_type="application/json",
    )
    async def _sources() -> str:
        result = await get_fire_data_sources(GetFireDataSourcesInput(), services)
        return json.dumps(
            result.model_dump(mode="json", exclude_none=True, exclude={"status"}),
            ensure_ascii=False,
        )
