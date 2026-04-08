"""
agent.py — Core agent loop for ShopBot.

Handles the conversation with Groq's LLM, processes tool calls,
and returns final responses. The agent is stateless per call —
conversation history is managed by the caller (main.py).
"""

import json
import os

from dotenv import load_dotenv
load_dotenv()

from groq import Groq

from tools import TOOL_SCHEMAS, dispatch_tool

# ── Constants ────────────────────────────────────────────────────────────────

MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
MAX_TOOL_ROUNDS = 5  # prevent infinite tool-call loops

SYSTEM_PROMPT = """You are ShopBot, a friendly and efficient customer support agent for TechNest — an online electronics store.

Your job is to help customers with order issues, store policies, returns, and general questions.

You have access to four tools:
- lookup_order: retrieve order status and tracking details
- search_faq: search the store's knowledge base for policy/general questions
- request_return: initiate a return or refund for a delivered order
- escalate_to_human: escalate complex or unresolved issues to a human agent

## Decision rules:
- If the customer mentions an order ID (format: ORD-XXXX), use lookup_order first.
- If the question is general (shipping, returns policy, payments), use search_faq first.
- If the customer wants to return a specific delivered order and gives an order ID, use request_return.
- If you cannot resolve the issue after using the appropriate tools, or the customer asks for a human, use escalate_to_human.
- Never make up order details, policies, or ticket IDs. Always use tools to get real data.

## Response style:
- Be concise, warm, and professional.
- After a tool call, summarize the result clearly in plain language — do not dump raw JSON.
- If a tool returns an error or no result, acknowledge it honestly and offer next steps (try escalation or ask for clarification).
- Never tell the customer which tool you are calling — just respond naturally.
"""


# ── Agent ────────────────────────────────────────────────────────────────────

class SupportAgent:
    """
    Stateless support agent. Takes a conversation history and returns
    the next assistant message plus the updated history.
    """

    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GROQ_API_KEY environment variable is not set. "
                "Get a free key at https://console.groq.com"
            )
        self.client = Groq(api_key=api_key)

    def respond(self, history: list[dict]) -> tuple[str, list[dict]]:
        """
        Given conversation history (list of role/content dicts),
        run the agent loop and return (assistant_reply, updated_history).

        The history must NOT include the system prompt — that is injected here.
        """
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

        for round_num in range(MAX_TOOL_ROUNDS):
            response = self.client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
            )

            choice = response.choices[0]
            message = choice.message

            # ── No tool call: final response ─────────────────────────────────
            if choice.finish_reason == "stop" or not message.tool_calls:
                reply = message.content or ""
                history = history + [{"role": "assistant", "content": reply}]
                return reply, history

            # ── Tool call(s) requested ───────────────────────────────────────
            # Append the assistant's tool-call message to context
            messages.append(message)

            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                try:
                    tool_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    tool_args = {}

                tool_result = dispatch_tool(tool_name, tool_args)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result,
                })

        # ── Safety: exceeded max rounds ───────────────────────────────────────
        fallback = (
            "I'm having trouble resolving your request right now. "
            "Let me escalate this to a human agent who can help you further."
        )
        history = history + [{"role": "assistant", "content": fallback}]
        return fallback, history
