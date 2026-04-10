"""
faq_service.py — Business logic for FAQ / knowledge-base search.

Uses keyword-intersection scoring against a static JSON file.
In production this would be replaced with an embeddings-based
semantic search (e.g. FAISS, Pinecone).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from app.core.config import DATA_DIR
from app.models.schemas import FAQResult, ToolError

logger = logging.getLogger(__name__)


class FAQService:
    """
    Knowledge-base search service.

    Scores entries by overlap between user query tokens and
    each FAQ entry's tags + question words.
    """

    def __init__(self, data_dir: Path = DATA_DIR) -> None:
        self._data_dir = data_dir

    def _load_faqs(self) -> list[dict]:
        path = self._data_dir / "faq.json"
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error("FAQ database not found at %s", path)
            raise

    def search(self, query: str) -> FAQResult | ToolError:
        """
        Search the FAQ for the best-matching entry.

        Returns:
            FAQResult with result="found" or result="no_match",
            or ToolError if the data source is unavailable.
        """
        try:
            faqs = self._load_faqs()
        except FileNotFoundError:
            return ToolError(error="Knowledge base unavailable. Please try again later.")

        query_words = set(query.lower().split())
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
            return FAQResult(
                result="no_match",
                message=(
                    "I couldn't find a specific FAQ entry for your question. "
                    "You may want to escalate to a human agent for further help."
                ),
            )

        return FAQResult(
            result="found",
            question=best_match["question"],
            answer=best_match["answer"],
            confidence="high" if best_score >= 2 else "low",
        )
