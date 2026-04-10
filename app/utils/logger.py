"""
logger.py — Centralised logging configuration.

Call ``setup_logging()`` once at application startup.  Every module then
obtains its own child logger via ``logging.getLogger(__name__)``.
"""

import logging
from pathlib import Path

from app.core.config import LOG_DIR


def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure root logger with console + file handlers.

    Args:
        level: minimum severity for the root logger.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    fmt = logging.Formatter(
        "%(asctime)s | %(name)-30s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ── Console handler (warnings+ only — keep terminal clean) ──────────
    console = logging.StreamHandler()
    console.setLevel(logging.WARNING)
    console.setFormatter(fmt)

    # ── File handler (all logs) ──────────────────────────────────────────
    file_handler = logging.FileHandler(LOG_DIR / "app.log", encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(fmt)

    # ── Root logger ──────────────────────────────────────────────────────
    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(console)
    root.addHandler(file_handler)


def get_escalation_logger() -> logging.Logger:
    """
    Return a dedicated logger that writes only to ``logs/escalations.log``.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("escalation")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(
            LOG_DIR / "escalations.log", encoding="utf-8",
        )
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(message)s"),
        )
        logger.addHandler(handler)

    return logger
