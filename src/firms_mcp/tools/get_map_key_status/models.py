"""Input and output models for get_map_key_status."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from firms_mcp.tools.common import InputModel, KnowledgeRef, ToolOutput


class GetMapKeyStatusInput(InputModel):
    """No arguments: the status is for the MAP_KEY connected to this session."""


class ServerBudget(BaseModel):
    budget: int = Field(description="This server's ceiling per key per 10 minutes")
    estimated_used: int = Field(
        description="Transactions this server estimates it used in the window"
    )


class GetMapKeyStatusOutput(ToolOutput):
    transaction_limit: int | None = Field(default=None, description="As reported by FIRMS")
    current_transactions: int | None = Field(default=None, description="As reported by FIRMS")
    remaining: int | None = None
    transaction_interval: str | None = None
    server_budget: ServerBudget | None = None
    firms_response: dict[str, Any] | None = Field(
        default=None, description="FIRMS's full status response (any key redacted)"
    )
    knowledge_entries: list[KnowledgeRef] = Field(default_factory=list)
