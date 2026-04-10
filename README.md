# ShopBot — AI Customer Support Agent

A production-grade, multi-tool AI agent for **TechNest**, a fictional electronics e-commerce store. Built with Python and powered by [Groq](https://console.groq.com) (`meta-llama/llama-4-scout-17b-16e-instruct`) using native tool calling — no heavy frameworks.

---

## Architecture

```
app/
  agent/              → LLM agent loop (plan → act → observe → respond)
  tools/              → each tool in its own module + dispatcher
  prompts/            → system prompt + tool schemas (separated from code)
  services/           → pure business logic (orders, FAQ, escalation)
  models/             → Pydantic schemas for all inputs/outputs
  core/               → centralised config (pydantic-settings)
  utils/              → logging setup + conversation persistence

data/                 → mock databases (orders.json, faq.json)
logs/                 → runtime logs (auto-created, gitignored)
tests/                → unit + integration tests
docs/                 → architecture guide + prompt optimization
scripts/              → CLI runner
```

> See [`docs/architecture.md`](docs/architecture.md) for the full design rationale and data-flow diagrams.

---

## Features

- **4 tools** the agent autonomously selects based on user input:
  - `lookup_order` — retrieves order status, tracking, and delivery info
  - `search_faq` — searches a static knowledge base for policy questions
  - `request_return` — initiates a return/refund for delivered orders
  - `escalate_to_human` — logs escalations and returns a structured ticket
- **Dynamic tool routing** — the LLM decides which tool to call; zero hardcoded routing
- **Pydantic validation** on every tool input and output
- **Clean architecture** — Agent → Tools → Services → Data (no business logic in the agent loop)
- **Dependency injection** — agent receives config; services are swappable
- **Comprehensive error handling** — unknown tools, bad arguments, missing data, LLM failures
- **Structured logging** — console + file + dedicated escalation log
- **Conversation persistence** — every session saved as timestamped JSON for audit/debugging
- **Docker support** — `Dockerfile` + `docker-compose.yml` included

---

## Quick Start

### Prerequisites

- Python 3.11+
- A free Groq API key ([console.groq.com](https://console.groq.com))

### 1. Clone & install

```bash
git clone <your-repo-url>
cd ShopBotifyX
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env and paste your GROQ_API_KEY
```

### 3. Run

```bash
python main.py
```

### 4. Run with Docker

```bash
docker compose up --build
```

---

## Run Tests

```bash
pytest tests/ -v
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
| Return on cancelled order | Informs cancellation, suggests waiting for auto-refund |
| FAQ query with no match | Acknowledges the gap, offers escalation |
| Ambiguous intent (no order ID) | Searches FAQ first, asks for order ID if needed |
| Tool argument parsing error | Caught in dispatcher, returns structured error to LLM |
| Unknown tool requested by LLM | Logged as warning, returns error envelope |
| LLM stuck in tool-call loop | Safety cap (`MAX_TOOL_ROUNDS=5`) triggers fallback |

---

## Project Structure

```
ShopBotifyX/
├── app/
│   ├── agent/
│   │   ├── __init__.py
│   │   └── agent.py              # core LLM loop + tool orchestration
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py             # pydantic-settings configuration
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py            # Pydantic input/output schemas
│   ├── prompts/
│   │   ├── system_prompt.txt     # system prompt (plain text)
│   │   └── tool_prompts.py       # LLM tool schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── order_service.py      # order lookup + return business logic
│   │   ├── faq_service.py        # FAQ keyword search
│   │   └── escalation_service.py # ticket generation + logging
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── dispatcher.py         # dynamic tool registry + dispatch
│   │   ├── order_lookup.py       # tool: lookup_order
│   │   ├── faq_search.py         # tool: search_faq
│   │   ├── request_return.py     # tool: request_return
│   │   └── escalate.py           # tool: escalate_to_human
│   └── utils/
│       ├── __init__.py
│       ├── logger.py             # centralised logging config
│       └── conversation_logger.py # session persistence to JSON
├── data/
│   ├── orders.json               # mock order database (4 orders)
│   └── faq.json                  # knowledge base (8 entries)
├── docs/
│   ├── architecture.md           # design rationale + diagrams
│   └── prompt_optimization.md    # V1→V2 prompt evolution
├── logs/                         # auto-created at runtime (gitignored)
│   ├── app.log                   # application debug logs
│   ├── escalations.log           # human escalation audit trail
│   └── conversations/            # saved chat sessions (timestamped JSON)
├── scripts/
│   └── run.py                    # CLI runner
├── tests/
│   ├── __init__.py
│   ├── test_tools.py             # unit tests for services + dispatcher
│   └── test_agent.py             # integration tests (mocked LLM)
├── .env                          # secrets (gitignored)
├── .env.example                  # template for .env
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── main.py                       # entrypoint
├── requirements.txt
└── README.md
```

---

## Assumptions & Trade-offs

- Order data and FAQ are static (mocked). In production these would be real DB / API calls.
- FAQ search uses keyword intersection. Production would use embeddings for semantic recall.
- A single Groq API key is used. Production would add key rotation and rate limiting.
- The CLI is single-user. Production would wrap this in a REST API (e.g. FastAPI).

---

## What I'd Add With More Time

- **FastAPI wrapper** — expose `/chat` endpoint so this can power a web UI
- **Semantic FAQ search** — replace keyword matching with vector embeddings (FAISS / Pinecone)
- **Database-backed persistence** — migrate file-based conversation logs to Redis / PostgreSQL for multi-session continuity
- **Observability** — OpenTelemetry traces for every tool call
- **CI/CD pipeline** — GitHub Actions for lint + test + Docker push
- **Multi-tenant support** — tenant-scoped configs and data isolation
