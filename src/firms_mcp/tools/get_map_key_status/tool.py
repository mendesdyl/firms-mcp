"""get_map_key_status: transactions used for the connected MAP_KEY (FR-DATA-009)."""

from __future__ import annotations

import json

from firms_mcp.redaction import redact
from firms_mcp.services import Services
from firms_mcp.tools.common import knowledge_refs
from firms_mcp.tools.get_map_key_status.models import (
    GetMapKeyStatusInput,
    GetMapKeyStatusOutput,
    ServerBudget,
)


async def get_map_key_status(
    params: GetMapKeyStatusInput, services: Services
) -> GetMapKeyStatusOutput:
    map_key = services.credentials.require()
    status = await services.firms.map_key_status(map_key)
    remaining = (
        status.transaction_limit - status.current_transactions
        if status.transaction_limit is not None and status.current_transactions is not None
        else None
    )
    budget = services.firms.budget
    return GetMapKeyStatusOutput(
        status="success",
        transaction_limit=status.transaction_limit,
        current_transactions=status.current_transactions,
        remaining=remaining,
        transaction_interval=status.transaction_interval,
        server_budget=ServerBudget(budget=budget.budget, estimated_used=budget.used(map_key)),
        firms_response=json.loads(redact(json.dumps(status.raw))),
        knowledge_entries=knowledge_refs(services.knowledge, ["supplement.api.map-key"]),
    )
