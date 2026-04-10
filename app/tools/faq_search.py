"""
faq_search.py — Tool wrapper for the FAQ search capability.

Validates input via Pydantic, delegates to FAQService,
and returns a serialised JSON string for the LLM.
"""

from __future__ import annotations

import json

from app.models.schemas import FAQSearchInput, ToolError
from app.services.faq_service import FAQService

_service = FAQService()


def search_faq(query: str) -> str:
    """
    Search the FAQ knowledge base using keyword matching.

    Args:
        query: The customer's question or topic.

    Returns:
        JSON string of FAQResult or ToolError.
    """
    inp = FAQSearchInput(query=query)
    result = _service.search(inp.query)

    if isinstance(result, ToolError):
        return json.dumps(result.model_dump())

    return json.dumps(result.model_dump())
