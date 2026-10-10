"""FIRMS knowledge base: verbatim FIRMS documentation with provenance (ADR-0005)."""

from firms_mcp.knowledge.loader import (
    KnowledgeBase,
    KnowledgeBaseError,
    Section,
    configured_knowledge_dirs,
    default_knowledge_dir,
    load_knowledge_base,
)
from firms_mcp.knowledge.models import KnowledgeEntry, KnowledgeSource, content_hash
from firms_mcp.knowledge.search import SearchHit

__all__ = [
    "KnowledgeBase",
    "KnowledgeBaseError",
    "KnowledgeEntry",
    "KnowledgeSource",
    "SearchHit",
    "Section",
    "configured_knowledge_dirs",
    "content_hash",
    "default_knowledge_dir",
    "load_knowledge_base",
]
