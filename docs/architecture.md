# Architecture — ShopBot

## Overview

ShopBot is a multi-tool AI customer support agent for **TechNest**, an online electronics store. It uses Groq's LLM inference API with native tool calling to dynamically select and execute tools based on customer queries — with **zero hardcoded routing**.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI / API Layer                      │
│                    (main.py / scripts/run.py)                │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Agent Layer                            │
│                  (app/agent/agent.py)                        │
│                                                             │
│   ┌──────────┐   ┌──────────┐   ┌───────────┐   ┌────────┐ │
│   │  PLAN    │──▶│   ACT    │──▶│  OBSERVE  │──▶│RESPOND │ │
│   │(LLM call)│   │(dispatch)│   │(feed back)│   │(answer)│ │
│   └──────────┘   └──────────┘   └───────────┘   └────────┘ │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Tools Layer                            │
│                   (app/tools/*.py)                           │
│                                                             │
│   ┌──────────────┐ ┌────────────┐ ┌──────────────┐         │
│   │ order_lookup  │ │ faq_search │ │request_return│  ...    │
│   └──────┬───────┘ └─────┬──────┘ └──────┬───────┘         │
└──────────┼───────────────┼───────────────┼──────────────────┘
           │               │               │
           ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────┐
│                    Services Layer                           │
│                  (app/services/*.py)                         │
│                                                             │
│   ┌──────────────┐ ┌────────────┐ ┌──────────────────────┐  │
│   │ OrderService │ │ FAQService │ │ EscalationService    │  │
│   └──────┬───────┘ └─────┬──────┘ └──────────┬───────────┘  │
└──────────┼───────────────┼───────────────────┼──────────────┘
           │               │                   │
           ▼               ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data / External Layer                     │
│            (data/*.json, logs/, Groq API)                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Layer Responsibilities

### 1. CLI / API Layer (`main.py`, `scripts/run.py`)
- User-facing I/O (terminal or future REST API)
- Manages conversation history
- Persists every session to `logs/conversations/` as timestamped JSON on exit
- Initialises logging and configuration

### 2. Agent Layer (`app/agent/agent.py`)
- Orchestrates the **Plan → Act → Observe → Respond** cycle
- Sends conversation context (including system prompt) to the LLM
- Delegates tool execution to the dispatcher — never runs business logic directly
- Enforces a safety cap on tool-call rounds to prevent infinite loops

### 3. Tools Layer (`app/tools/*.py`)
- Thin wrappers that **validate inputs** (via Pydantic) and **delegate** to services
- Each tool is a separate module — adding a new tool is a 3-step process:
  1. Create `app/tools/new_tool.py`
  2. Register it in `app/tools/dispatcher.py`
  3. Add its schema in `app/prompts/tool_prompts.py`

### 4. Services Layer (`app/services/*.py`)
- Contains **all business logic** (order eligibility, FAQ scoring, ticket generation)
- Has no knowledge of the LLM, prompts, or tool schemas
- Easily swappable — replace JSON file reads with database queries in production

### 5. Models Layer (`app/models/schemas.py`)
- Pydantic models for every tool input and output
- Ensures type safety and validation at every boundary
- Serves as living documentation of the tool contract

### 6. Core & Utils (`app/core/`, `app/utils/`)
- **`config.py`**: Single source of truth for all settings (API keys, paths, tunables)
- **`logger.py`**: Centralised logging configuration (console + file + escalation)
- **`conversation_logger.py`**: Saves each chat session as a timestamped JSON file for audit and debugging

---

## Design Principles

| Principle | How It's Applied |
|---|---|
| **Separation of Concerns** | Agent ≠ Tool ≠ Service ≠ Data |
| **Dependency Injection** | `SupportAgent` receives `Settings` — no global state |
| **Open/Closed** | Add tools without modifying the agent loop |
| **Single Responsibility** | Each service handles exactly one domain |
| **Fail Gracefully** | Every error path returns a structured `ToolError` |

---

## Data Flow (Example: "Where is ORD-1001?")

```
1. User types "Where is ORD-1001?"
2. CLI appends to history, calls agent.respond(history)
3. Agent sends history + system_prompt to Groq LLM
4. LLM returns tool_call: lookup_order(order_id="ORD-1001")
5. Agent calls dispatcher.dispatch_tool("lookup_order", {...})
6. Dispatcher → order_lookup.py → validates via Pydantic → OrderService.get_order()
7. OrderService reads data/orders.json, finds ORD-1001, returns OrderInfo
8. Tool serialises OrderInfo to JSON string
9. Agent feeds tool result back to LLM as a "tool" message
10. LLM synthesises a natural-language reply
11. Agent returns (reply, updated_history) to CLI
12. CLI prints: "ShopBot: Your order ORD-1001 has been shipped! ..."
13. On session exit, conversation_logger saves full history to logs/conversations/
```

---

## Scaling Considerations

| Area | Current (MVP) | Production Path |
|---|---|---|
| Data store | JSON files | PostgreSQL / DynamoDB |
| FAQ search | Keyword intersection | Vector embeddings (FAISS / Pinecone) |
| API layer | CLI | FastAPI with WebSocket support |
| Auth | None | OAuth2 / API keys |
| Deployment | Docker | Kubernetes / ECS |
| Observability | File logs | OpenTelemetry + Grafana |
| Rate limiting | None | Redis-based token bucket |
| Multi-tenancy | Single store | Tenant-scoped configs |
| Chat persistence | File-based JSON | PostgreSQL / Redis for multi-session |
