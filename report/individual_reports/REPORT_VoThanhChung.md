# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Vo Thanh Chung
- **Student ID**: 2A202600335
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

### Modules Implemented

| Module                     | Role                                                          |
| :------------------------- | :------------------------------------------------------------ |
| `src/agent/agent.py`       | ReAct loop: `get_system_prompt()`, `run()`, `_execute_tool()` |
| `src/tools/tools.py`       | All 6 tool definitions and their backing functions            |
| `src/api/oxford_tool.py`   | Oxford Dictionary API integration                             |
| `src/api/synonym_api.py`   | Synonym lookup API integration                                |
| `src/flashcard/storage.py` | JSON-backed flashcard persistence                             |

### Code Highlights

**1. ReAct loop (`src/agent/agent.py` — `run()` method)**

The core loop builds a running `history` string, sends it to the LLM, parses the `Action:` line with regex, executes the tool, then appends the real `Observation:` back into history for the next step:

```python
history = f"User: {user_input}\n"
while steps < self.max_steps:
    response = self.llm.generate(history, system_prompt=self.get_system_prompt())
    content = response["content"]

    # Strip any fake "Observation:" the LLM hallucinated
    clean_content = content.split("Observation:")[0].rstrip()
    history += clean_content + "\n"

    if "Final Answer:" in content:
        return content.split("Final Answer:")[-1].strip()

    action_match = re.search(r"Action:\s*(\w+)\((.*?)\)", content)
    if action_match:
        tool_name = action_match.group(1)
        tool_args = action_match.group(2)
        observation = self._execute_tool(tool_name, tool_args)
        history += f"Observation: {observation}\n"
```

**2. Dynamic argument parsing (`src/agent/agent.py` — `_execute_tool()`)**

Handles three calling conventions — zero-arg tools, `key="value"` kwargs, and simple positional strings:

```python
def _execute_tool(self, tool_name: str, args: str) -> str:
    for tool in self.tools:
        if tool['name'] == tool_name:
            try:
                if not args.strip():
                    return tool['func']()   # e.g. list_flashcard_sets()

                # Parse key="value" or key='value' pairs
                kv_matches = re.findall(
                    r'(\w+)\s*=\s*(?:"([^"]*)"' + r"|'([^']*)')", args
                )
                if kv_matches:
                    kwargs = {m[0]: (m[1] or m[2]) for m in kv_matches}
                    return tool['func'](**kwargs)   # e.g. add_card_to_set(...)

                # Fallback: single positional arg
                return tool['func'](args.strip().strip('"\''))
            except Exception as e:
                return f"Error executing {tool_name}: {str(e)}"
    return f"Error: Tool '{tool_name}' not found."
```

**3. Tool definitions (`src/tools/tools.py`)**

Each tool is a plain Python dict with `name`, `description`, and `func`. The description is the LLM's only knowledge of the tool — precision here directly determines argument accuracy:

```python
{
    "name": "add_card_to_set",
    "description": "Add a new flashcard (word and meaning). Parameters: set_name, front (English), back (Vietnamese).",
    "func": add_card_func
}
```

### How the code interacts with the ReAct loop

The system prompt embeds all tool `description` strings. The LLM reads these and decides which tool to call and with what arguments. `_execute_tool` bridges the text-based action (e.g. `add_card_to_set(set_name="Fruit", front="apple", back="táo")`) to the actual Python function call. The observation returned by the function is injected as `Observation: ...` in the history, completing the feedback loop before the next LLM step.

---

## II. Debugging Case Study (10 Points)

### Problem Description

After implementing the initial agent (v1), every call to `list_flashcard_sets` failed with the same error, and certain multi-argument tool calls silently lost arguments. This caused cascading failures — the agent could not retrieve existing sets, then hallucinated fake set lists from its training data and reported success to the user.

### Log Source (`logs/2026-04-06.log`)

**Bug 1 — `list_flashcard_sets` TypeError (09:59:02 – 10:12:05):**

```
Action: list_flashcard_sets()
Tool execution error: list_sets_func() takes 0 positional arguments but 1 was given
  File "src/agent/agent.py", line 116, in _execute_tool
    return tool['func'](args)
TypeError: list_sets_func() takes 0 positional arguments but 1 was given
```

This error appeared in every single agent session in v1 — 8+ repeated occurrences.

**Bug 2 — Hallucinated observation (10:05:39):**

```
--- Step 2 ---
Action: list_flashcard_sets()
Observation: ['học tập', 'công việc', 'cuộc sống']    ← fabricated by LLM
Tool execution error: list_sets_func() takes 0 positional arguments but 1 was given
Observation: Error executing list_flashcard_sets: ...  ← real system error
```

The agent used the fabricated observation to reason and ultimately gave a confident but wrong Final Answer.

**Bug 3 — Missing `back` argument (10:22:41):**

```
Action: add_card_to_set(set_name="Fruit", front="apple", back="táo")
TypeError: add_card_func() missing 1 required positional argument: 'back'
```

The action looked syntactically correct but `back` was missing at runtime.

### Diagnosis

**Bug 1** — `_execute_tool` called `tool['func'](args)` unconditionally. For `list_sets_func()` which takes 0 arguments, this passed the empty string `""` as a positional argument, immediately raising `TypeError`. The LLM had no way to fix this — it kept retrying the same call format because the call format was correct; the problem was in the execution layer.

**Bug 2** — The system prompt's format section contained `Observation: result of the tool call.` as an example line. This trained the LLM to complete the full Thought-Action-Observation cycle in a single response. After getting real errors, the LLM started writing its own fake observations inside its reply. These fake observations entered `history` before the real one was appended, so subsequent steps reasoned from corrupted state.

**Bug 3** — Line 95 of `agent.py` applied `.strip("'\"")` to the raw args string. For `set_name="Fruit", front="apple", back="táo"`, this stripped the trailing `"` from `"táo"`, producing `back="táo` (no closing quote). The `key="value"` regex requires a matching closing quote, so `back` was never parsed into kwargs, making the function call fail with a missing argument error.

### Solution

| Bug                                               | Fix                                                                                                                                                                                                              |
| :------------------------------------------------ | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Bug 1** — `tool['func'](args)`                  | Check `if not args.strip()` → call `tool['func']()` with no args                                                                                                                                                 |
| **Bug 2** — LLM writes fake observations          | (a) Changed system prompt format to explicitly say the system injects `Observation`; (b) Added rule "NEVER write Observation yourself"; (c) Truncated LLM response at `Observation:` before appending to history |
| **Bug 3** — `.strip("'\"")` removes closing quote | Removed `.strip("'\"")` from line 95; `_execute_tool` now handles stripping per-case                                                                                                                             |

After applying these three fixes, all previous failure cases resolved correctly in subsequent sessions (visible in log entries from 10:33 onward).

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

### 1. Reasoning — How did the `Thought` block help?

The `Thought` block forces the agent to externalize its reasoning before acting. In the session `"tra cứu và thêm từ address vào card set công việc"` (09:56), the agent's thought was:

> _"I will first check if a flashcard set named 'công việc' exists. If it does, I will fetch the meaning of 'address' and add it to the set."_

A plain chatbot faced with the same input would answer from its training data — it might say "I've added the word" without actually writing anything to storage. The `Thought` step also gave the agent a way to self-correct: when `list_flashcard_sets` kept failing, the agent reasoned "I cannot retrieve the list, I will try creating the set directly" — an adaptive behavior the chatbot cannot exhibit.

### 2. Reliability — When did the Agent perform _worse_ than the Chatbot?

**Simple factual Q&A**: For the input `"who are you"`, the chatbot replied instantly (3.2s, 11 tokens). The agent spent an entire LLM call checking whether a tool was needed, then returned the same answer in 3.2s but consuming 305 tokens. The agent carries unnecessary overhead for questions that require no tools.

**Date question**: Both failed. The chatbot (Gemini Flash) hallucinated "Today is Wednesday, May 22, 2024" — over two years behind. The agent had no `get_current_date` tool, so it would hallucinate similarly if asked. Neither architecture solved this; it requires an external time tool or injecting the date into the system prompt.

**Cascading failure amplification**: When a tool bug caused errors, the agent's multi-step loop amplified the damage — it consumed 5 steps × LLM tokens trying the same failing call, accruing unnecessary cost and eventually hitting `max_steps_reached`. A chatbot would just answer once and stop.

### 3. Observation — How did environment feedback influence next steps?

The `Observation` feedback loop is where the agent architecture genuinely outperforms the chatbot. In the successful Oxford definition trace (09:56):

```
Step 1: Action: get_oxford_definition(address)
        Observation: the particulars of the place where someone lives...
Step 2: Final Answer: Từ "address" có nghĩa là "địa chỉ"...
```

The agent adapted its answer based on the real API response — not its training weights. This is the fundamental advantage: the agent's answer is grounded in live data, not memorized patterns.

The failure cases revealed the dark side: when observations were wrong (due to bugs) or fabricated (hallucinations), the agent's subsequent reasoning was confidently incorrect. The quality of the observation pipeline directly determines the reliability of the entire system.

---

## IV. Future Improvements (5 Points)

- **Scalability**: With 6 tools the prompt is manageable, but at 50+ tools the system prompt would overflow the context window. A **tool retrieval system** (embed tool descriptions in a vector DB, retrieve the top-k relevant tools per query) would scale this to hundreds of tools without prompt bloat.

- **Safety — Supervisor Layer**: Add a lightweight "guard" LLM pass that checks tool arguments before execution. For example, before calling `add_card_to_set`, verify that `set_name` references an existing set. This catches hallucinated arguments before they corrupt persistent storage.

- **Performance — Async Tool Calls**: When the agent needs multiple independent tool calls (e.g., fetch definition AND synonyms for the same word), parallelize them with `asyncio`. This would reduce multi-step latency by the number of parallel tool calls.

- **Memory / Session Continuity**: Currently each `agent.run()` call starts with an empty `history`. Persisting a session history across calls (keyed by user ID) would let the agent remember "you already have a 'Công việc' set" without re-querying `list_flashcard_sets` at the start of every session.

- **Observability — Cost Alerting**: The telemetry system already tracks `cost_estimate` per call. Adding a per-session cost accumulator with a configurable budget cap (e.g., $0.05 per session) would prevent runaway costs on infinite-loop failures before `max_steps` is reached.
