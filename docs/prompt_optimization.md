# Prompt Optimization — ShopBot System Prompt

## Overview

This document walks through a systematic iteration of ShopBot's system prompt — from an initial version that produced inconsistent results, to a refined version that behaves predictably and professionally.

---

## V1 — Initial Prompt

```
You are a helpful customer support chatbot for an online electronics store called TechNest. Help customers with their questions about orders, returns, shipping, and general store policies. You have tools available to look up orders and search FAQs. Be friendly and helpful.
```

### Example of underperformance

**User input:**
> "I want my money back for my order"

**V1 Output:**
> "I'd be happy to help you with a refund! Could you please provide me with your order ID so I can look into this for you? Once I have that, I'll check the status and see what we can do."

**Problem:** The agent only asks for the order ID but never calls any tool — it just stalls. On a follow-up like `"ORD-1003"`, the agent sometimes calls `lookup_order` but other times tries to call `request_return` without checking if the order is actually delivered first, leading to confusing or incorrect responses.

---

## Diagnosis — Why V1 Fails

### 1. No tool priority rules
The prompt says "you have tools" but gives no guidance on *when* to use which tool. The LLM guesses, and guesses inconsistently.

### 2. No decision boundary for escalation
The agent doesn't know when it's appropriate to give up and escalate vs. keep trying tools — so it sometimes loops or apologizes repeatedly.

### 3. Ambiguous intent handling missing
"I want my money back" could mean a policy question (`search_faq`) or an active return (`request_return`). V1 has no rule for resolving this ambiguity.

### 4. No output format guidance
The agent sometimes dumps raw-looking data in its response, which feels robotic, especially after tool results are returned.

### 5. No constraint against hallucination
Without an explicit rule, the LLM occasionally invents policy details (e.g., "refunds take 3 days") instead of using the FAQ tool.

---

## V2 — Improved Prompt

```
You are ShopBot, a friendly and efficient customer support agent for TechNest — an online electronics store.

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
```

---

## Side-by-Side Comparison — Same Input

### Input: `"I want my money back for my order"`

| Dimension | V1 Output | V2 Output |
|---|---|---|
| **Tool called** | None (just asks for order ID) | `search_faq("return refund policy")` first, then asks for order ID |
| **Information given** | Nothing — deferred entirely | Explains the 30-day return policy upfront, then asks for order ID to proceed |
| **Tone** | Fine, but vague | Warm, informative, and action-oriented |
| **Consistency** | Varies — sometimes calls wrong tool on follow-up | Consistent across runs |
| **Hallucination risk** | Medium — may invent policy details | Low — grounded in FAQ tool result |

### Follow-up Input: `"ORD-1003"`

| Dimension | V1 Output | V2 Output |
|---|---|---|
| **Tool called** | Sometimes `lookup_order`, sometimes `request_return` directly | Always `lookup_order` first (decision rule: order ID → lookup first) |
| **Status check** | Often skipped | Confirms order is "delivered", then calls `request_return` |
| **Result** | Inconsistent — may try to return a non-delivered order | Correctly initiates return, provides ticket ID |

---

## Why V2 Works

The key improvement isn't length — it's **specificity of decision rules**. V1 told the model *what* tools exist; V2 tells it *when* to use each one. This eliminates the ambiguity that causes inconsistent tool selection.

The explicit anti-hallucination rule (`Never make up order details... Always use tools`) directly addresses the most common failure mode seen in V1. And the response style section converts a raw data-dumping agent into one that communicates like a real support rep.

**V2 is better because every added line removes a choice the LLM previously had to make on its own — and was making incorrectly.**

---

## Key Takeaways

1. **Enumerated decision rules** beat vague instructions — they constrain the LLM's action space.
2. **Anti-hallucination guardrails** must be explicit; the model won't infer them.
3. **Output formatting directives** (no raw JSON, natural language only) dramatically improve UX.
4. **Tool ordering hints** (e.g., "use lookup_order *first*") create predictable multi-step workflows.
5. **Escalation as a defined exit** prevents the agent from looping on unresolvable queries.
