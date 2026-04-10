"""
dispatcher.py — Dynamic tool dispatcher.

Maps LLM-generated tool names to their implementations and handles
argument validation, unknown tools, and runtime errors uniformly.
"""

from __future__ import annotations

import json
import logging
from typing import Callable

from app.tools.order_lookup import lookup_order
from app.tools.faq_search import search_faq
from app.tools.request_return import request_return
from app.tools.escalate import escalate_to_human

logger = logging.getLogger(__name__)

# ── Registry ─────────────────────────────────────────────────────────────────
# Add new tools here — nothing else needs to change.

TOOL_REGISTRY: dict[str, Callable[..., str]] = {
    "lookup_order": lookup_order,
    "search_faq": search_faq,
    "request_return": request_return,
    "escalate_to_human": escalate_to_human,
}


def dispatch_tool(name: str, arguments: dict) -> str:
    """
    Call a registered tool by name with the given arguments.

    Args:
        name:      tool function name (as chosen by the LLM).
        arguments: keyword arguments parsed from the LLM response.

    Returns:
        JSON-serialised result string (always valid JSON).
    """
    fn = TOOL_REGISTRY.get(name)

    if fn is None:
        logger.warning("LLM requested unknown tool: %s", name)
        return json.dumps({"error": f"Unknown tool '{name}'. This is an internal error."})

    try:
        result = fn(**arguments)
        logger.info("Tool '%s' executed successfully.", name)
        return result
    except TypeError as exc:
        logger.error("Bad arguments for tool '%s': %s", name, exc)
        return json.dumps({"error": f"Tool '{name}' called with invalid arguments: {exc}"})
    except Exception as exc:
        logger.exception("Unexpected error in tool '%s'", name)
        return json.dumps({"error": f"Tool '{name}' encountered an unexpected error: {exc}"})
