"""
order_lookup.py — Tool wrapper for the order lookup capability.

Validates input via Pydantic, delegates to OrderService,
and returns a serialised JSON string for the LLM.
"""

from __future__ import annotations

import json

from app.models.schemas import OrderLookupInput, ToolError
from app.services.order_service import OrderService

_service = OrderService()


def lookup_order(order_id: str) -> str:
    """
    Look up order status and details by order ID.

    Args:
        order_id: e.g. "ORD-1001"

    Returns:
        JSON string of OrderInfo or ToolError.
    """
    inp = OrderLookupInput(order_id=order_id)
    result = _service.get_order(inp.order_id)

    if isinstance(result, ToolError):
        return json.dumps(result.model_dump())

    return json.dumps(result.model_dump())
