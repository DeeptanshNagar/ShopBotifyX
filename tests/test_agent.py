"""
test_agent.py — Integration tests for the SupportAgent.

Uses unittest.mock to patch the Groq client so tests run without
an API key or network access.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.agent.agent import SupportAgent
from app.core.config import Settings


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_settings() -> Settings:
    """Create a Settings object with a dummy API key for testing."""
    return Settings(groq_api_key="test-key-not-real")


def _mock_stop_response(content: str):
    """Build a mock Groq response that immediately returns text (no tool call)."""
    message = MagicMock()
    message.content = content
    message.tool_calls = None

    choice = MagicMock()
    choice.finish_reason = "stop"
    choice.message = message

    response = MagicMock()
    response.choices = [choice]
    return response


def _mock_tool_call_response(tool_name: str, arguments: dict):
    """Build a mock Groq response that requests a single tool call."""
    tool_call = MagicMock()
    tool_call.id = "call_abc123"
    tool_call.function.name = tool_name
    tool_call.function.arguments = json.dumps(arguments)

    message = MagicMock()
    message.content = None
    message.tool_calls = [tool_call]

    choice = MagicMock()
    choice.finish_reason = "tool_calls"
    choice.message = message

    response = MagicMock()
    response.choices = [choice]
    return response


# ═══════════════════════════════════════════════════════════════════════════════
#  TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestSupportAgent:
    """Integration tests for the agent loop."""

    @patch("app.agent.agent.Groq")
    def test_direct_response_no_tool(self, mock_groq_cls):
        """When the LLM responds directly, no tool is invoked."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_stop_response(
            "Hello! How can I help you today?"
        )
        mock_groq_cls.return_value = mock_client

        agent = SupportAgent(_make_settings())
        reply, history = agent.respond([{"role": "user", "content": "hi"}])

        assert reply == "Hello! How can I help you today?"
        assert history[-1]["role"] == "assistant"
        assert history[-1]["content"] == reply

    @patch("app.agent.agent.Groq")
    def test_tool_call_then_response(self, mock_groq_cls):
        """When the LLM calls a tool, the dispatcher runs and the LLM responds."""
        mock_client = MagicMock()

        # First call: LLM requests tool
        tool_response = _mock_tool_call_response(
            "lookup_order", {"order_id": "ORD-1001"},
        )
        # Second call: LLM produces final answer
        final_response = _mock_stop_response(
            "Your order ORD-1001 has been shipped!"
        )

        mock_client.chat.completions.create.side_effect = [
            tool_response,
            final_response,
        ]
        mock_groq_cls.return_value = mock_client

        agent = SupportAgent(_make_settings())
        reply, history = agent.respond([
            {"role": "user", "content": "Where is my order ORD-1001?"},
        ])

        assert "ORD-1001" in reply
        assert mock_client.chat.completions.create.call_count == 2

    @patch("app.agent.agent.Groq")
    def test_max_rounds_fallback(self, mock_groq_cls):
        """If the LLM keeps requesting tools past the limit, a fallback fires."""
        mock_client = MagicMock()

        # Every call returns a tool request — never stops
        mock_client.chat.completions.create.return_value = (
            _mock_tool_call_response("search_faq", {"query": "loop"})
        )
        mock_groq_cls.return_value = mock_client

        settings = _make_settings()
        settings.max_tool_rounds = 2  # low cap for fast test

        agent = SupportAgent(settings)
        reply, history = agent.respond([
            {"role": "user", "content": "tell me about shipping"},
        ])

        assert "escalate" in reply.lower() or "trouble" in reply.lower()
        assert mock_client.chat.completions.create.call_count == 2

    @patch("app.agent.agent.Groq")
    def test_history_not_mutated_in_place(self, mock_groq_cls):
        """The original history list must not be mutated."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_stop_response("Sure!")
        mock_groq_cls.return_value = mock_client

        agent = SupportAgent(_make_settings())
        original = [{"role": "user", "content": "test"}]
        original_len = len(original)

        _, new_history = agent.respond(original)

        assert len(original) == original_len  # not mutated
        assert len(new_history) == original_len + 1
