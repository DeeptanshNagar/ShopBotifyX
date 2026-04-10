"""
escalation_service.py — Business logic for human-agent escalation.

Generates a ticket ID and persists the escalation to a dedicated log file.
"""

from __future__ import annotations

import logging
from datetime import datetime

from app.models.schemas import EscalationResult
from app.utils.logger import get_escalation_logger

logger = logging.getLogger(__name__)


class EscalationService:
    """
    Handles creation and logging of human-escalation tickets.

    In production this would create a ticket in Zendesk / Jira / etc.
    """

    def __init__(self) -> None:
        self._esc_logger = get_escalation_logger()

    def escalate(self, reason: str, customer_message: str) -> EscalationResult:
        """
        Log an escalation and return a structured ticket.
        """
        ticket_id = f"ESC-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        self._esc_logger.info(
            "ticket=%s | reason=%s | message=%s",
            ticket_id,
            reason,
            customer_message,
        )

        logger.info("Escalation created: %s", ticket_id)

        return EscalationResult(
            escalated=True,
            ticket_id=ticket_id,
            message=(
                f"Your request has been escalated to our human support team. "
                f"Ticket ID: {ticket_id}. "
                "A support agent will reach out within 2–4 business hours. "
                "Please keep this ticket ID for reference."
            ),
            reason=reason,
        )
