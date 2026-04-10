"""
agent.py — Core agent loop for ShopBot.

Implements the Plan → Act → Observe → Respond cycle:
  1. Send conversation history + system prompt to the LLM.
  2. If the LLM requests tool calls, dispatch them and feed results back.
  3. Repeat until the LLM produces a final text response or the safety
     cap on tool-call rounds is reached.

The agent is stateless per call — conversation history is managed
by the caller (CLI / API layer).
"""

from __future__ import annotations

import json
import logging

from groq import Groq

from app.core.config import Settings, PROMPTS_DIR
from app.prompts.tool_prompts import TOOL_SCHEMAS
from app.tools.dispatcher import dispatch_tool

logger = logging.getLogger(__name__)


class SupportAgent:
    """
    LLM-powered support agent with dynamic tool selection.

    Args:
        settings: application settings (injected for testability).
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = Groq(api_key=settings.groq_api_key)
        self._system_prompt = self._load_system_prompt()

    # ── private helpers ──────────────────────────────────────────────────

    @staticmethod
    def _load_system_prompt() -> str:
        """Read the system prompt from the prompts directory."""
        path = PROMPTS_DIR / "system_prompt.txt"
        with open(path, encoding="utf-8") as f:
            return f.read().strip()

    # ── public API ───────────────────────────────────────────────────────

    def respond(self, history: list[dict]) -> tuple[str, list[dict]]:
        """
        Given conversation history (list of role/content dicts),
        run the agent loop and return (assistant_reply, updated_history).

        The history must NOT include the system prompt — it is injected here.

        Cycle:
            PLAN   → LLM decides what to do next
            ACT    → dispatcher executes the chosen tool(s)
            OBSERVE → tool results are appended to context
            RESPOND → LLM synthesises a final answer
        """
        messages = [{"role": "system", "content": self._system_prompt}] + history

        for round_num in range(self._settings.max_tool_rounds):
            logger.debug("Agent loop — round %d", round_num + 1)

            response = self._client.chat.completions.create(
                model=self._settings.model_name,
                messages=messages,
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
            )

            choice = response.choices[0]
            message = choice.message

            # ── RESPOND: no tool call → final answer ─────────────────────
            if choice.finish_reason == "stop" or not message.tool_calls:
                reply = message.content or ""
                history = history + [{"role": "assistant", "content": reply}]
                logger.info("Agent responded (round %d).", round_num + 1)
                return reply, history

            # ── ACT + OBSERVE: execute requested tool(s) ─────────────────
            messages.append(message)

            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                try:
                    tool_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    tool_args = {}
                    logger.warning(
                        "Malformed tool arguments from LLM for '%s'", tool_name,
                    )

                logger.info(
                    "Dispatching tool '%s' with args: %s", tool_name, tool_args,
                )
                tool_result = dispatch_tool(tool_name, tool_args)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result,
                })

        # ── Safety fallback: exceeded max rounds ─────────────────────────
        logger.warning(
            "Agent exceeded max tool rounds (%d). Returning fallback.",
            self._settings.max_tool_rounds,
        )
        fallback = (
            "I'm having trouble resolving your request right now. "
            "Let me escalate this to a human agent who can help you further."
        )
        history = history + [{"role": "assistant", "content": fallback}]
        return fallback, history
