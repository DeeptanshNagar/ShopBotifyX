# ShopBot — AI Customer Support Agent

A production-minded multi-tool AI agent for **TechNest**, a fictional electronics e-commerce store. Built with Python and powered by [Groq](https://console.groq.com) (`llama-3.3-70b-versatile`) using native tool calling — no heavy frameworks.

---

## Features

- **4 tools** the agent autonomously selects based on user input:
  - `lookup_order` — retrieves order status, tracking, and delivery info
  - `search_faq` — searches a static knowledge base for policy questions
  - `request_return` — initiates a return/refund for delivered orders
  - `escalate_to_human` — logs escalations and returns a structured ticket
- Dynamic tool routing — no hardcoded intent classification
- Graceful edge case handling (order not found, non-eligible returns, ambiguous queries)
- Clean conversation history maintained across turns

---

## Project Structure

```
ai-support-agent/
├── agent/
│   ├── __init__.py
│   ├── agent.py          # core LLM loop + tool orchestration
│   └── tools.py          # tool implementations + schemas + dispatcher
├── data/
│   ├── orders.json       # mock order database
│   └── faq.json          # knowledge base (8 entries)
├── logs/
│   └── escalations.log   # auto-created; human escalation log
├── main.py               # CLI entrypoint
├── PROMPT_OPTIMIZATION.md
├── requirements.txt
└── README.md
```

---

## Setup

**Prerequisites:** Python 3.11+

### 1. Clone the repo

```bash
git clone <your-repo-url>
cd ai-support-agent
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set your Groq API key

Get a free key at [https://console.groq.com](https://console.groq.com).

```bash
# macOS / Linux
export GROQ_API_KEY=your_key_here

# Windows (Command Prompt)
set GROQ_API_KEY=your_key_here

# Windows (PowerShell)
$env:GROQ_API_KEY="your_key_here"
```

### 4. Run

```bash
python main.py
```

---

## Example Interactions

```
You: Where is my order ORD-1001?
ShopBot: Your order ORD-1001 has been shipped! It contains Wireless Headphones and a
         USB-C Cable, totalling $89.99. Estimated delivery is April 9, 2025.
         Your tracking number is TRK-88291.

You: What's your return policy?
ShopBot: We accept returns within 30 days of delivery. Items must be unused and in
         original packaging. Refunds are processed within 5–7 business days.

You: I want to return ORD-1003, it arrived damaged.
ShopBot: I've initiated a return for order ORD-1003. Your return ticket ID is
         RET-ORD-1003-142301. You'll receive a prepaid return label via email
         within 24 hours.

You: I need to speak to a real person.
ShopBot: I've escalated your request to our human support team. Ticket ID: ESC-20250408142305.
         A support agent will reach out within 2–4 business hours.
```

---

## Edge Cases Handled

| Scenario | Behavior |
|---|---|
| Order ID not found | Returns clear error, suggests verifying the ID |
| Return on non-delivered order | Explains current status, tells customer to wait |
| FAQ query with no match | Acknowledges the gap, offers escalation |
| Ambiguous intent (no order ID) | Searches FAQ first, asks for order ID if needed |
| Tool argument error | Caught in dispatcher, returns structured error to LLM |

---

## Assumptions

- Order data and FAQ are static (mocked). In production these would be real DB/API calls.
- A single Groq API key is used. Production would add rate limiting and key rotation.
- The CLI is single-user. Production would wrap this in a REST API (e.g. FastAPI).

---

## What I'd Add With More Time

- **FastAPI wrapper** — expose `/chat` endpoint so this can power a web UI
- **Semantic FAQ search** — replace keyword matching with embeddings for better recall
- **Order ID extraction** — auto-parse order IDs from natural language ("my order 1001")
- **Conversation memory** — persist history to Redis for multi-session continuity
- **Evaluation harness** — automated test suite covering all edge cases
