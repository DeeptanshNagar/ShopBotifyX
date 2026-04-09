"""
tools.py — Tool implementations for the ShopBot support agent.

Each tool is a plain Python function. Tool schemas are defined separately
and passed to the LLM for tool-calling decisions.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "Data"
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ── Logger for escalations ───────────────────────────────────────────────────

escalation_logger = logging.getLogger("escalation")
escalation_logger.setLevel(logging.INFO)
_handler = logging.FileHandler(LOG_DIR / "escalations.log")
_handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
escalation_logger.addHandler(_handler)


# ── Tool 1: Order Lookup ─────────────────────────────────────────────────────

def lookup_order(order_id: str) -> dict:
    """
    Look up order status and details by order ID.

    Returns order info dict, or an error dict if not found.
    """
    order_id = order_id.strip().upper()

    try:
        with open(DATA_DIR / "orders.json") as f:
            orders = json.load(f)
    except FileNotFoundError:
        return {"error": "Order database unavailable. Please try again later."}

    order = orders.get(order_id)

    if not order:
        return {
            "error": f"No order found with ID '{order_id}'. "
                     "Please double-check the order ID (format: ORD-XXXX)."
        }

    return {
        "order_id": order["id"],
        "customer": order["customer"],
        "status": order["status"],
        "items": order["items"],
        "total": f"${order['total']:.2f}",
        "placed_on": order["placed_on"],
        "estimated_delivery": order["estimated_delivery"] or "N/A",
        "tracking": order["tracking"] or "Not yet assigned",
    }


# ── Tool 2: FAQ / Knowledge Base Search ─────────────────────────────────────

def search_faq(query: str) -> dict:
    """
    Search the FAQ knowledge base using keyword matching.

    Returns the best matching FAQ entry, or a no-result response.
    """
    query_words = set(query.lower().split())

    try:
        with open(DATA_DIR / "faq.json") as f:
            faqs = json.load(f)
    except FileNotFoundError:
        return {"error": "Knowledge base unavailable. Please try again later."}

    best_match = None
    best_score = 0

    for entry in faqs:
        tag_set = set(entry["tags"])
        question_words = set(entry["question"].lower().split())
        score = len(query_words & tag_set) + len(query_words & question_words)

        if score > best_score:
            best_score = score
            best_match = entry

    if not best_match or best_score == 0:
        return {
            "result": "no_match",
            "message": (
                "I couldn't find a specific FAQ entry for your question. "
                "You may want to escalate to a human agent for further help."
            ),
        }

    return {
        "result": "found",
        "question": best_match["question"],
        "answer": best_match["answer"],
        "confidence": "high" if best_score >= 2 else "low",
    }


# ── Tool 3: Return / Refund Request ─────────────────────────────────────────

def request_return(order_id: str, reason: str) -> dict:
    """
    Initiate a return or refund request for a delivered order.

    Validates that the order exists and is eligible for return.
    """
    order_id = order_id.strip().upper()

    try:
        with open(DATA_DIR / "orders.json") as f:
            orders = json.load(f)
    except FileNotFoundError:
        return {"error": "Order database unavailable. Please try again later."}

    order = orders.get(order_id)

    if not order:
        return {"error": f"Order '{order_id}' not found. Cannot initiate return."}

    status = order["status"]

    if status == "delivered":
        ticket_id = f"RET-{order_id}-{datetime.now().strftime('%H%M%S')}"
        return {
            "success": True,
            "ticket_id": ticket_id,
            "message": (
                f"Return request created for order {order_id}. "
                f"Ticket ID: {ticket_id}. "
                "You'll receive a prepaid return label via email within 24 hours. "
                "Refunds are processed in 5–7 business days after we receive the item."
            ),
            "reason_logged": reason,
        }

    elif status in ("processing", "shipped"):
        return {
            "success": False,
            "message": (
                f"Order {order_id} is currently '{status}' and cannot be returned yet. "
                "Please wait for delivery, then initiate a return."
            ),
        }

    elif status == "cancelled":
        return {
            "success": False,
            "message": (
                f"Order {order_id} was already cancelled. "
                "If you were charged, please allow 5–7 business days for a refund, "
                "or escalate to a human agent."
            ),
        }

    else:
        return {
            "success": False,
            "message": f"Order {order_id} has status '{status}', which is not eligible for a return at this time.",
        }


# ── Tool 4: Escalate to Human ────────────────────────────────────────────────

def escalate_to_human(reason: str, customer_message: str) -> dict:
    """
    Escalate the conversation to a human support agent.

    Logs the escalation and returns a structured acknowledgment.
    """
    ticket_id = f"ESC-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    escalation_logger.info(
        "ticket=%s | reason=%s | message=%s",
        ticket_id,
        reason,
        customer_message,
    )

    return {
        "escalated": True,
        "ticket_id": ticket_id,
        "message": (
            f"Your request has been escalated to our human support team. "
            f"Ticket ID: {ticket_id}. "
            "A support agent will reach out within 2–4 business hours. "
            "Please keep this ticket ID for reference."
        ),
        "reason": reason,
    }


# ── Tool Schema Definitions (for Groq tool-calling API) ─────────────────────

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_order",
            "description": (
                "Look up the status and details of a customer's order by order ID. "
                "Use this when the customer asks about their order, shipping status, "
                "tracking number, or delivery estimate. Order IDs follow the format ORD-XXXX."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID to look up, e.g. 'ORD-1001'.",
                    }
                },
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_faq",
            "description": (
                "Search the knowledge base / FAQ for answers to general questions "
                "about store policies, shipping, payments, returns, account issues, "
                "or anything not tied to a specific order. Use this before escalating."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The customer's question or topic to search for.",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "request_return",
            "description": (
                "Initiate a return or refund request for a specific delivered order. "
                "Use this when the customer explicitly wants to return an item or "
                "request a refund and provides their order ID."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID for the return, e.g. 'ORD-1003'.",
                    },
                    "reason": {
                        "type": "string",
                        "description": "The reason the customer wants to return the item.",
                    },
                },
                "required": ["order_id", "reason"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_to_human",
            "description": (
                "Escalate the conversation to a human support agent. Use this when: "
                "(1) the customer explicitly asks to speak to a human, "
                "(2) the issue is complex or sensitive and cannot be resolved with other tools, "
                "(3) a tool returns no useful result after a reasonable attempt, or "
                "(4) the customer is clearly frustrated or upset."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Brief reason for escalation, e.g. 'unresolved billing dispute'.",
                    },
                    "customer_message": {
                        "type": "string",
                        "description": "The customer's original message that triggered escalation.",
                    },
                },
                "required": ["reason", "customer_message"],
            },
        },
    },
]


# ── Tool Dispatcher ───────────────────────────────────────────────────────────

TOOL_REGISTRY = {
    "lookup_order": lookup_order,
    "search_faq": search_faq,
    "request_return": request_return,
    "escalate_to_human": escalate_to_human,
}


def dispatch_tool(name: str, arguments: dict) -> str:
    """
    Call the named tool with given arguments and return JSON string result.
    Handles unknown tool names gracefully.
    """
    fn = TOOL_REGISTRY.get(name)

    if fn is None:
        result = {"error": f"Unknown tool '{name}'. This is an internal error."}
    else:
        try:
            result = fn(**arguments)
        except TypeError as e:
            result = {"error": f"Tool '{name}' called with invalid arguments: {e}"}
        except Exception as e:
            result = {"error": f"Tool '{name}' encountered an unexpected error: {e}"}

    return json.dumps(result)
