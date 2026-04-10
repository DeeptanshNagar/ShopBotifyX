"""
conversation_logger.py — Persists chat sessions to disk.

Each conversation is saved as a timestamped JSON file under
``logs/conversations/``, creating an audit trail of all interactions.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from app.core.config import LOG_DIR

logger = logging.getLogger(__name__)

CONVERSATIONS_DIR = LOG_DIR / "conversations"


def save_conversation(history: list[dict]) -> Path | None:
    """
    Write the conversation history to a timestamped JSON file.

    Args:
        history: list of role/content message dicts.

    Returns:
        Path to the saved file, or None if history was empty.
    """
    if not history:
        return None

    CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filepath = CONVERSATIONS_DIR / f"{timestamp}.json"

    record = {
        "session_start": timestamp,
        "total_messages": len(history),
        "messages": history,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)

    logger.info("Conversation saved to %s", filepath)
    return filepath
