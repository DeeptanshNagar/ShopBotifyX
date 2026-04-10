"""
schemas.py — Pydantic models for tool inputs and outputs.

Every tool call is validated through these schemas before execution,
and every tool result is serialised from these schemas — guaranteeing
a consistent contract between the LLM, the dispatcher, and the services.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════════════
#  TOOL INPUT SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class OrderLookupInput(BaseModel):
    """Input for the order lookup tool."""
    order_id: str = Field(..., description="Order ID to look up, e.g. 'ORD-1001'.")


class FAQSearchInput(BaseModel):
    """Input for the FAQ search tool."""
    query: str = Field(..., description="The customer's question or topic to search for.")


class RequestReturnInput(BaseModel):
    """Input for the return/refund request tool."""
    order_id: str = Field(..., description="The order ID for the return, e.g. 'ORD-1003'.")
    reason: str = Field(..., description="The reason the customer wants to return the item.")


class EscalateInput(BaseModel):
    """Input for the escalate-to-human tool."""
    reason: str = Field(..., description="Brief reason for escalation.")
    customer_message: str = Field(..., description="The customer's original message.")


# ═══════════════════════════════════════════════════════════════════════════════
#  TOOL OUTPUT SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class OrderInfo(BaseModel):
    """Structured response for a successful order lookup."""
    order_id: str
    customer: str
    status: str
    items: list[str]
    total: str
    placed_on: str
    estimated_delivery: str
    tracking: str


class FAQResult(BaseModel):
    """Structured response for a successful FAQ lookup."""
    result: str              # "found" or "no_match"
    question: str = ""
    answer: str = ""
    confidence: str = ""     # "high" or "low"
    message: str = ""        # populated when result == "no_match"


class ReturnResult(BaseModel):
    """Structured response for a return request."""
    success: bool
    message: str
    ticket_id: str = ""
    reason_logged: str = ""


class EscalationResult(BaseModel):
    """Structured response for an escalation."""
    escalated: bool
    ticket_id: str
    message: str
    reason: str


class ToolError(BaseModel):
    """Standardised error envelope returned by any tool."""
    error: str
