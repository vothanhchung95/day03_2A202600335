# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: X1
- **Team Members**: Nguyen Ho Bao Thien - 2A202600163, Hoang Thi Thanh Tuyen - 2A202600074, Duong Khoa Diem - 2A202600366, Do The Anh - 2A202600040, Vo Thanh Chung - 2A202600335, Le Minh Khang - 2A202600102
- **Deployment Date**: 2026-04-06

---

## 1. Executive Summary

This lab implemented an English Vocabulary Learning Agent using the ReAct (Reason + Act) loop pattern on top of GPT-4o. The agent manages flashcard sets — creating sets, adding vocabulary cards, looking up definitions via the Oxford Dictionary API, and fetching synonyms. It was compared against a plain chatbot baseline (GPT-4o and Gemini 1.5 Flash) across 22 interaction sessions.

- **Success Rate**: 86% (19/22 agent sessions completed with a Final Answer)
- **Key Outcome**: The ReAct agent correctly handled multi-step tasks such as "look up a word and add it to a set" by chaining `get_oxford_definition` → `add_card_to_set`, which the stateless chatbot could not do. However, two code-level bugs caused repeated failures in the initial version (v1), documented in Section 4.

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation

```
User Input
    │
    ▼
┌─────────────────────────────────────────────────────┐
│  ReActAgent.run()                                   │
│                                                     │
│  history = "User: {input}\n"                        │
│                                                     │
│  while steps < max_steps (6):                       │
│    ┌──────────────────────────────────────────────┐ │
│    │  LLM generates:                              │ │
│    │    Thought: <reasoning>                      │ │
│    │    Action: tool_name(arg1, arg2, ...)        │ │
│    └──────────────────────────────────────────────┘ │
│           │                                         │
│    ┌──────▼───────────────────────────────────────┐ │
│    │  Parse Action with regex                     │ │
│    │  Execute _execute_tool(name, args)           │ │
│    └──────────────────────────────────────────────┘ │
│           │                                         │
│    ┌──────▼───────────────────────────────────────┐ │
│    │  Append "Observation: {result}" to history  │ │
│    └──────────────────────────────────────────────┘ │
│           │                                         │
│    ┌──────▼───────────────────────────────────────┐ │
│    │  If "Final Answer:" in content → return     │ │
│    └──────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

Each LLM response is truncated at any `Observation:` line before being appended to history, preventing the model from contaminating the context with hallucinated observations.

### 2.2 Tool Definitions (Inventory)

| Tool Name               | Input Format                                   | Use Case                                         |
| :---------------------- | :--------------------------------------------- | :----------------------------------------------- |
| `list_flashcard_sets`   | _(no arguments)_                               | List all flashcard sets with card counts         |
| `create_flashcard_set`  | `set_name="<name>"`                            | Create a new named flashcard set                 |
| `add_card_to_set`       | `set_name="<name>", front="<EN>", back="<VN>"` | Add a vocab card (English → Vietnamese) to a set |
| `list_cards_in_set`     | `set_name="<name>"`                            | View all cards in a specific set                 |
| `get_synonyms`          | `word="<word>"`                                | Fetch English synonyms via external API          |
| `get_oxford_definition` | `word="<word>"`                                | Fetch official Oxford Dictionary definition      |

### 2.3 LLM Providers Used

- **Primary**: GPT-4o (OpenAI) — used for all agent sessions
- **Secondary (Baseline)**: Gemini 1.5 Flash (`gemini-3-flash-preview`) — used for chatbot baseline comparison

---

## 3. Telemetry & Performance Dashboard

_Metrics collected from `logs/2026-04-06.log` — 59 total LLM calls across 22 agent sessions._

| Metric                                | Value         |
| :------------------------------------ | :------------ |
| **Average Latency (P50)**             | 2018ms        |
| **Max Latency (P99)**                 | 12446ms       |
| **Average Latency (mean)**            | 2283ms        |
| **Min Latency**                       | 1085ms        |
| **Average Tokens per LLM Call**       | 443 tokens    |
| **Total Tokens (all agent calls)**    | 26,163 tokens |
| **Total Estimated Cost**              | $0.2616       |
| **Agent Sessions**                    | 22            |
| **Successful (Final Answer reached)** | 19 (86%)      |
| **Failed (max_steps_reached)**        | 3 (14%)       |

**Chatbot baseline comparison (latency):**

| Model                  | Avg Latency              |
| :--------------------- | :----------------------- |
| GPT-4o (chatbot)       | 9,652ms (single sample)  |
| Gemini Flash (chatbot) | ~2,585ms                 |
| GPT-4o (agent)         | 2,283ms avg per LLM call |

> Note: High P99 (12,446ms) was caused by multi-step sessions that hit the max_steps limit, accumulating context and increasing prompt size significantly.

---

## 4. Root Cause Analysis (RCA) - Failure Traces

### Case Study 1: `list_flashcard_sets` — TypeError on Every Call (Agent v1)

- **Input**: "tra cứu và thêm từ address vào card set công việc" (2026-04-06T09:59:00)
- **Observed behavior**: `list_flashcard_sets()` failed 100% of the time in v1.
- **Log snippet**:

```
Action: list_flashcard_sets()
Tool execution error: list_sets_func() takes 0 positional arguments but 1 was given
  File "src/agent/agent.py", line 116, in _execute_tool
    return tool['func'](args)
TypeError: list_sets_func() takes 0 positional arguments but 1 was given
Observation: Error executing list_flashcard_sets: list_sets_func() takes 0 positional arguments but 1 was given
```

- **Root Cause**: `_execute_tool` unconditionally called `tool['func'](args)`, passing the empty string `""` as a positional argument even when the tool takes no arguments.
- **Fix (v2)**: Added a guard — `if not args.strip(): return tool['func']()`.

---

### Case Study 2: `add_card_to_set` — Missing `back` Argument (Agent v1)

- **Input**: "thêm từ apple vào bộ thẻ Fruit" (2026-04-06T10:22:35)
- **Observed behavior**: Agent tried `add_card_to_set(set_name="Fruit", front="apple", back="táo")` 3 times but failed every time.
- **Log snippet**:

```
Action: add_card_to_set(set_name="Fruit", front="apple", back="táo")
Tool execution error: add_card_func() missing 1 required positional argument: 'back'
TypeError: add_card_func() missing 1 required positional argument: 'back'
```

- **Root Cause**: Line 95 of `agent.py` applied `.strip("'\"")` to the **entire** args string. For `set_name="Fruit", front="apple", back="táo"`, this stripped the trailing `"` off `"táo"`, producing `back="táo` (no closing quote). The `key="value"` regex then failed to match `back`, so it was absent from kwargs.
- **Fix (v2)**: Removed `.strip("'\"")` from argument extraction. The `_execute_tool` method already strips appropriately inside each branch.

---

### Case Study 3: Hallucinated Observations (Agent v1)

- **Input**: "thêm card address vào set công việc" (2026-04-06T10:05:33)
- **Observed behavior**: Despite real tool errors, the agent reported success by fabricating observation text.
- **Log snippet**:

```
--- Step 2 ---
Action: list_flashcard_sets()
Observation: ['học tập', 'công việc', 'cuộc sống']   ← HALLUCINATED by LLM in its own response
Tool execution error: list_sets_func() takes 0 positional arguments but 1 was given
Observation: Error executing list_flashcard_sets: ...  ← Real observation from system
```

- **Root Cause**: The system prompt's format section showed `Observation: result of the tool call.` as an example, which taught the LLM to write its own fake observations as part of its response. These fake observations entered the history and were treated as real.
- **Fix (v2)**:
  1. Replaced the format example with: `[The system will inject the Observation here — do NOT write Observation yourself]`
  2. Added explicit rule: `5. NEVER write 'Observation:' yourself.`
  3. Added code to truncate the LLM's response at any `Observation:` marker before appending to history: `clean_content = content.split("Observation:")[0].rstrip()`

---

## 5. Ablation Studies & Experiments

### Experiment 1: Prompt v1 vs Prompt v2

|                        | Prompt v1                               | Prompt v2                                            |
| :--------------------- | :-------------------------------------- | :--------------------------------------------------- |
| **Format instruction** | `Observation: result of the tool call.` | `[System will inject Observation — do NOT write it]` |
| **Explicit rule**      | _(none)_                                | `5. NEVER write 'Observation:' yourself.`            |
| **History truncation** | Full LLM response appended              | Content truncated at `Observation:` before append    |

**Result**: Prompt v2 eliminated hallucinated observations entirely. The LLM stopped fabricating tool results, and the agent history remained clean.

---

### Experiment 2: Chatbot vs Agent

| Test Case                            | Chatbot Result                         | Agent Result                                    | Winner           |
| :----------------------------------- | :------------------------------------- | :---------------------------------------------- | :--------------- |
| Simple greeting ("hi")               | Correct, fast (1.9s)                   | Correct but slower (3.2s, 1 step)               | **Chatbot**      |
| "What date today?"                   | **Hallucinated** — said "May 22, 2024" | N/A (no date tool implemented)                  | Draw (both fail) |
| "What is the meaning of 'address'?"  | Answered from training data            | Called Oxford API, returned official definition | **Agent**        |
| "Create set + add word (multi-step)" | Cannot manage state or call tools      | Completed with Thought-Action chain             | **Agent**        |
| "List all flashcard sets"            | No tool access, cannot retrieve data   | Retrieved live data from storage                | **Agent**        |

---

## 6. Production Readiness Review

- **Security**: Tool arguments are parsed with regex and passed as keyword arguments — no `eval()` or shell injection risk. However, `set_name` and card content should be sanitized to prevent storage injection if a database backend is used.
- **Guardrails**: `max_steps=5` prevents infinite billing loops. In production, add a token budget limiter and a fallback message when steps are exhausted (currently returns a generic Vietnamese error message).
- **Observability**: Every LLM call logs `prompt_tokens`, `completion_tokens`, `latency_ms`, and `cost_estimate`. The telemetry system in `src/telemetry/` provides a solid foundation for production monitoring dashboards.
- **Reliability**: The Oxford Dictionary API returned 404 errors on some words (`address`). A fallback to the synonym API or a static dictionary should be added.
- **Scaling**: For a production system with many tools, transition to a tool-retrieval pattern (vector DB of tool descriptions) to avoid overloading the prompt. Consider LangGraph for branching, parallel tool calls, or human-in-the-loop approval steps.

---
