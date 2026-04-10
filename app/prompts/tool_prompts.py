"""
tool_prompts.py — LLM-facing tool schema definitions.

These are the OpenAI-compatible function-calling schemas passed to the
Groq API so the model knows *what* tools exist and *when* to use them.

Keep descriptions detailed — they are the primary mechanism by which
the LLM decides which tool to invoke.
"""

TOOL_SCHEMAS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "lookup_order",
            "description": (
                "Look up the status and details of a customer's order by order ID. "
                "Use this when the customer asks about their order, shipping status, "
                "tracking number, or delivery estimate. Order IDs follow the format ORD-XXXX."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID to look up, e.g. 'ORD-1001'.",
                    }
                },
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_faq",
            "description": (
                "Search the knowledge base / FAQ for answers to general questions "
                "about store policies, shipping, payments, returns, account issues, "
                "or anything not tied to a specific order. Use this before escalating."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The customer's question or topic to search for.",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "request_return",
            "description": (
                "Initiate a return or refund request for a specific delivered order. "
                "Use this when the customer explicitly wants to return an item or "
                "request a refund and provides their order ID."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID for the return, e.g. 'ORD-1003'.",
                    },
                    "reason": {
                        "type": "string",
                        "description": "The reason the customer wants to return the item.",
                    },
                },
                "required": ["order_id", "reason"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_to_human",
            "description": (
                "Escalate the conversation to a human support agent. Use this when: "
                "(1) the customer explicitly asks to speak to a human, "
                "(2) the issue is complex or sensitive and cannot be resolved with other tools, "
                "(3) a tool returns no useful result after a reasonable attempt, or "
                "(4) the customer is clearly frustrated or upset."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Brief reason for escalation, e.g. 'unresolved billing dispute'.",
                    },
                    "customer_message": {
                        "type": "string",
                        "description": "The customer's original message that triggered escalation.",
                    },
                },
                "required": ["reason", "customer_message"],
            },
        },
    },
]
