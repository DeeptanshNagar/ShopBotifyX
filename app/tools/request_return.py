"""
request_return.py — Tool wrapper for the return/refund capability.

Validates input via Pydantic, delegates to OrderService,
and returns a serialised JSON string for the LLM.
"""

from __future__ import annotations

import json

from app.models.schemas import RequestReturnInput, ToolError
from app.services.order_service import OrderService

_service = OrderService()


def request_return(order_id: str, reason: str) -> str:
    """
    Initiate a return or refund request for a delivered order.

    Args:
        order_id: e.g. "ORD-1003"
        reason:   customer-provided reason.

    Returns:
        JSON string of ReturnResult or ToolError.
    """
    inp = RequestReturnInput(order_id=order_id, reason=reason)
    result = _service.request_return(inp.order_id, inp.reason)

    if isinstance(result, ToolError):
        return json.dumps(result.model_dump())

    return json.dumps(result.model_dump())
