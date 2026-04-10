"""
escalate.py — Tool wrapper for the human escalation capability.

Validates input via Pydantic, delegates to EscalationService,
and returns a serialised JSON string for the LLM.
"""

from __future__ import annotations

import json

from app.models.schemas import EscalateInput
from app.services.escalation_service import EscalationService

_service = EscalationService()


def escalate_to_human(reason: str, customer_message: str) -> str:
    """
    Escalate the conversation to a human support agent.

    Args:
        reason:            brief reason for the escalation.
        customer_message:  the customer's original text.

    Returns:
        JSON string of EscalationResult.
    """
    inp = EscalateInput(reason=reason, customer_message=customer_message)
    result = _service.escalate(inp.reason, inp.customer_message)
    return json.dumps(result.model_dump())
