"""
test_tools.py — Unit tests for every tool and underlying service.

Covers:
  - Successful lookups / searches
  - Edge cases (not found, invalid input, ineligible returns)
  - Error envelopes
"""

import json

from app.services.order_service import OrderService
from app.services.faq_service import FAQService
from app.services.escalation_service import EscalationService


# ═══════════════════════════════════════════════════════════════════════════════
#  ORDER SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class TestOrderService:
    """Tests for OrderService.get_order and request_return."""

    def setup_method(self):
        self.svc = OrderService()

    # ── get_order ────────────────────────────────────────────────────────

    def test_get_order_success(self):
        result = self.svc.get_order("ORD-1001")
        assert result.order_id == "ORD-1001"
        assert result.customer == "Alice Johnson"
        assert result.status == "shipped"
        assert "Wireless Headphones" in result.items

    def test_get_order_case_insensitive(self):
        result = self.svc.get_order("  ord-1001  ")
        assert result.order_id == "ORD-1001"

    def test_get_order_not_found(self):
        result = self.svc.get_order("ORD-9999")
        assert hasattr(result, "error")
        assert "No order found" in result.error

    # ── request_return ───────────────────────────────────────────────────

    def test_return_delivered_order(self):
        result = self.svc.request_return("ORD-1003", "Item arrived damaged")
        assert result.success is True
        assert result.ticket_id.startswith("RET-ORD-1003")
        assert "damaged" in result.reason_logged

    def test_return_processing_order_rejected(self):
        result = self.svc.request_return("ORD-1002", "Changed my mind")
        assert result.success is False
        assert "processing" in result.message

    def test_return_cancelled_order_rejected(self):
        result = self.svc.request_return("ORD-1004", "Want it back")
        assert result.success is False
        assert "cancelled" in result.message

    def test_return_nonexistent_order(self):
        result = self.svc.request_return("ORD-0000", "test")
        assert hasattr(result, "error")
        assert "not found" in result.error.lower()


# ═══════════════════════════════════════════════════════════════════════════════
#  FAQ SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class TestFAQService:
    """Tests for FAQService.search."""

    def setup_method(self):
        self.svc = FAQService()

    def test_search_returns_policy(self):
        result = self.svc.search("return refund policy")
        assert result.result == "found"
        assert "30 days" in result.answer

    def test_search_shipping(self):
        result = self.svc.search("how long does shipping take delivery time")
        assert result.result == "found"
        assert "shipping" in result.question.lower()

    def test_search_no_match(self):
        result = self.svc.search("xyzzy foobar nonsense")
        assert result.result == "no_match"
        assert result.message != ""

    def test_search_payment(self):
        result = self.svc.search("what payment methods credit card paypal")
        assert result.result == "found"
        assert "Visa" in result.answer or "PayPal" in result.answer


# ═══════════════════════════════════════════════════════════════════════════════
#  ESCALATION SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class TestEscalationService:
    """Tests for EscalationService.escalate."""

    def setup_method(self):
        self.svc = EscalationService()

    def test_escalation_returns_ticket(self):
        result = self.svc.escalate("billing dispute", "I was double charged!")
        assert result.escalated is True
        assert result.ticket_id.startswith("ESC-")
        assert "billing dispute" in result.reason

    def test_escalation_message_professional(self):
        result = self.svc.escalate("frustrated customer", "This is ridiculous")
        assert "2–4 business hours" in result.message


# ═══════════════════════════════════════════════════════════════════════════════
#  TOOL DISPATCHER
# ═══════════════════════════════════════════════════════════════════════════════

class TestDispatcher:
    """Tests for the tool dispatcher."""

    def test_dispatch_known_tool(self):
        from app.tools.dispatcher import dispatch_tool
        result = json.loads(dispatch_tool("lookup_order", {"order_id": "ORD-1001"}))
        assert result["order_id"] == "ORD-1001"

    def test_dispatch_unknown_tool(self):
        from app.tools.dispatcher import dispatch_tool
        result = json.loads(dispatch_tool("nonexistent_tool", {}))
        assert "error" in result
        assert "Unknown tool" in result["error"]

    def test_dispatch_bad_arguments(self):
        from app.tools.dispatcher import dispatch_tool
        result = json.loads(dispatch_tool("lookup_order", {"wrong_arg": "value"}))
        assert "error" in result
