"""Runtime services shared by tools, resources, and prompts.

One ``Services`` object is built per server. Tools receive it explicitly, so they can be
tested without an MCP session and every dependency (FIRMS client, knowledge base, clock)
can be replaced in tests.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable
from dataclasses import dataclass, field

from firms_mcp.config import Settings
from firms_mcp.credentials import CredentialMode, MapKeyResolver
from firms_mcp.firms.client import FirmsClient
from firms_mcp.knowledge import KnowledgeBase, configured_knowledge_dirs, load_knowledge_base


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


@dataclass
class Services:
    settings: Settings
    knowledge: KnowledgeBase
    firms: FirmsClient
    credentials: MapKeyResolver
    clock: Callable[[], dt.datetime] = field(default=utc_now)

    def now(self) -> dt.datetime:
        return self.clock()

    def today(self) -> dt.date:
        """The current UTC date (FIRMS days are UTC days)."""
        return self.clock().astimezone(dt.UTC).date()

    async def aclose(self) -> None:
        await self.firms.aclose()


def build_services(
    settings: Settings | None = None,
    *,
    mode: CredentialMode = CredentialMode.LOCAL,
    knowledge: KnowledgeBase | None = None,
    firms: FirmsClient | None = None,
    clock: Callable[[], dt.datetime] | None = None,
) -> Services:
    """Build services; the knowledge base is loaded and validated here (fail fast)."""
    settings = settings or Settings()
    return Services(
        settings=settings,
        knowledge=knowledge or load_knowledge_base(configured_knowledge_dirs(settings)),
        firms=firms or FirmsClient(settings),
        credentials=MapKeyResolver(settings, mode),
        clock=clock or utc_now,
    )
