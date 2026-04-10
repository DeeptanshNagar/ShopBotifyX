"""
order_service.py — Business logic for order operations.

Reads the orders data source and provides pure-logic functions
that know nothing about LLMs or tool schemas.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.core.config import DATA_DIR
from app.models.schemas import OrderInfo, ReturnResult, ToolError

logger = logging.getLogger(__name__)


class OrderService:
    """
    Encapsulates all order-related operations.

    In production this would talk to a database or REST API;
    here it reads from a static JSON file.
    """

    def __init__(self, data_dir: Path = DATA_DIR) -> None:
        self._data_dir = data_dir

    # ── helpers ──────────────────────────────────────────────────────────

    def _load_orders(self) -> dict:
        """Load and return the raw orders dictionary."""
        path = self._data_dir / "orders.json"
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error("Orders database not found at %s", path)
            raise

    # ── public API ───────────────────────────────────────────────────────

    def get_order(self, order_id: str) -> OrderInfo | ToolError:
        """
        Retrieve order details by ID.

        Returns:
            OrderInfo on success, ToolError on failure.
        """
        order_id = order_id.strip().upper()

        try:
            orders = self._load_orders()
        except FileNotFoundError:
            return ToolError(error="Order database unavailable. Please try again later.")

        order = orders.get(order_id)
        if not order:
            return ToolError(
                error=f"No order found with ID '{order_id}'. "
                      "Please double-check the order ID (format: ORD-XXXX)."
            )

        return OrderInfo(
            order_id=order["id"],
            customer=order["customer"],
            status=order["status"],
            items=order["items"],
            total=f"${order['total']:.2f}",
            placed_on=order["placed_on"],
            estimated_delivery=order.get("estimated_delivery") or "N/A",
            tracking=order.get("tracking") or "Not yet assigned",
        )

    def request_return(self, order_id: str, reason: str) -> ReturnResult | ToolError:
        """
        Attempt to create a return/refund for an order.

        Business rules:
        - Only *delivered* orders are eligible.
        - Processing / shipped orders must wait.
        - Cancelled orders are rejected.
        """
        order_id = order_id.strip().upper()

        try:
            orders = self._load_orders()
        except FileNotFoundError:
            return ToolError(error="Order database unavailable. Please try again later.")

        order = orders.get(order_id)
        if not order:
            return ToolError(error=f"Order '{order_id}' not found. Cannot initiate return.")

        status = order["status"]

        if status == "delivered":
            ticket_id = f"RET-{order_id}-{datetime.now().strftime('%H%M%S')}"
            return ReturnResult(
                success=True,
                ticket_id=ticket_id,
                message=(
                    f"Return request created for order {order_id}. "
                    f"Ticket ID: {ticket_id}. "
                    "You'll receive a prepaid return label via email within 24 hours. "
                    "Refunds are processed in 5–7 business days after we receive the item."
                ),
                reason_logged=reason,
            )

        if status in ("processing", "shipped"):
            return ReturnResult(
                success=False,
                message=(
                    f"Order {order_id} is currently '{status}' and cannot be returned yet. "
                    "Please wait for delivery, then initiate a return."
                ),
            )

        if status == "cancelled":
            return ReturnResult(
                success=False,
                message=(
                    f"Order {order_id} was already cancelled. "
                    "If you were charged, please allow 5–7 business days for a refund, "
                    "or escalate to a human agent."
                ),
            )

        return ReturnResult(
            success=False,
            message=f"Order {order_id} has status '{status}', which is not eligible for a return at this time.",
        )
