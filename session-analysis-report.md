# OTel GenAI Session Analysis Report

**Generated:** 2026-03-18 10:04
**Trace File:** `otel-traces.jsonl`
**Total Records:** 682
**Sessions Found:** 2
**Orphan Records:** 128

## Executive Summary

This report analyzes OpenTelemetry trace data captured from GitHub Copilot Chat
(VS Code Insiders) using the GenAI instrumentation from
[PR #3917](https://github.com/microsoft/vscode-copilot-chat/pull/3917).
Two sessions were captured:

1. **Dice Roller Service** — A TypeSpec-driven SDK generation session that exercised
   the built-in `azure-sdk-mcp` server for code generation and spec validation.
2. **OTel Analysis Session** — The current session focused on building analysis
   tooling and understanding the trace format.

## Session Comparison

| Metric | Dice Roller Service | OTel Analysis Session |
|--------|--------||--------|
| Turns | 11 | 36 |
| Total trace records | 243 | 311 |
| Tool call events | 11 | 36 |
| Inference detail events | 28 | 51 |
| Primary input tokens | 910.9K | 3.6M |
| Primary output tokens | 2.4K | 38.5K |
| Inference routing tokens | 934.8K | 3.7M |
| Deliberate tool types | 4 | 6 |
| MCP tool types | 2 | 0 |
| Auto tool calls | 6 | 3 |

## Effectiveness Scores

### Dice Roller Service (Azure SDK MCP) — **75/100**

- +10: Active tool usage (5 deliberate calls)
- +15: MCP server integration (2 tool types)
- +5: Multi-model usage (6 models)
- -5: High inference routing overhead (934.8K tokens)

### OTel Analysis Session (Current) — **60/100**

- -10: Long session (36 turns)
- +10: Active tool usage (33 deliberate calls)
- +5: Heavy tool usage (33 calls)
- +5: Good output/input ratio (0.0108)
- +5: Multi-model usage (6 models)
- -5: High inference routing overhead (3.7M tokens)

---
## Dice Roller Service (Azure SDK MCP)

**Session ID:** `c6a2449f-ab16-46a4-b608-2adf5fc2aa031773851507809`

### Models Used

| Model (requested) | Inference Calls |
|-------------------|----------------|
| `gpt-4o-mini` | 14 |
| `claude-opus-4.6` | 11 |
| `gpt-4o-mini-2024-07-18` | 2 |
| `gpt-4.1` | 1 |

| Model (responded) | Inference Calls |
|-------------------|----------------|
| `gpt-4o-mini-2024-07-18` | 16 |
| `claude-opus-4-6` | 11 |
| `gpt-4.1-2025-04-14` | 1 |

### Tool Usage

| Tool | Type | Calls |
|------|------|-------|
| `create_file` | Built-in | 2 |
| `run_in_terminal` | Built-in | 1 |
| `azsdk_run_typespec_validation` | MCP (`azure-sdk-mcp`) | 1 |
| `azsdk_package_generate_code` | MCP (`azure-sdk-mcp`) | 1 |

> **Note:** 6 automatic `manage_todo_list` calls excluded from the table above.

### Token Budget

| Category | Input | Output | % of Total |
|----------|-------|--------|-----------|
| Primary agent turns | 910.9K | 2.4K | 49% |
| Inference routing (gpt-4o-mini) | 934.8K | 2.7K | 50% |
| **Grand Total** | **1.8M** | **5.1K** | **100%** |

> **Output/Input ratio:** 0.00265 — Low ratio indicates large context windows re-sent each turn (expected in agent-mode).

### Per-Turn Breakdown

| Turn | Input Tokens | Output Tokens | Deliberate Tools |
|------|-------------|--------------|-----------------|
| 0 | 81.2K | 228 | — (+1 auto) |
| 1 | 81.4K | 549 | `create_file` |
| 2 | 82.0K | 286 | `create_file` |
| 3 | 82.4K | 162 | — (+1 auto) |
| 4 | 82.6K | 102 | `mcp_azure-sdk-mcp_azsdk_run_typespec_validation` |
| 5 | 82.7K | 160 | — (+1 auto) |
| 6 | 82.9K | 180 | `mcp_azure-sdk-mcp_azsdk_package_generate_code` |
| 7 | 83.2K | 158 | — (+1 auto) |
| 8 | 83.3K | 185 | `run_in_terminal` |
| 9 | 84.5K | 156 | — (+1 auto) |
| 10 | 84.7K | 246 | — |

### Input Token Growth Per Turn

```
  Turn  0 | ███████████████████████████████████████████████ 81.2K
  Turn  1 | ████████████████████████████████████████████████ 81.4K ← create_file
  Turn  2 | ████████████████████████████████████████████████ 82.0K ← create_file
  Turn  3 | ████████████████████████████████████████████████ 82.4K
  Turn  4 | ████████████████████████████████████████████████ 82.6K ← mcp_azure-sdk-mcp_azsdk_run_typespec_validation
  Turn  5 | ████████████████████████████████████████████████ 82.7K
  Turn  6 | ████████████████████████████████████████████████ 82.9K ← mcp_azure-sdk-mcp_azsdk_package_generate_code
  Turn  7 | █████████████████████████████████████████████████ 83.2K
  Turn  8 | █████████████████████████████████████████████████ 83.3K ← run_in_terminal
  Turn  9 | █████████████████████████████████████████████████ 84.5K
  Turn 10 | ██████████████████████████████████████████████████ 84.7K
```

---
## OTel Analysis Session (Current)

**Session ID:** `f18e08a5-2eee-4670-96ff-92c3b90169471773851507818`

### Models Used

| Model (requested) | Inference Calls |
|-------------------|----------------|
| `claude-opus-4.6` | 37 |
| `gpt-4o-mini` | 11 |
| `gpt-4o-mini-2024-07-18` | 2 |
| `gpt-4.1` | 1 |

| Model (responded) | Inference Calls |
|-------------------|----------------|
| `claude-opus-4-6` | 37 |
| `gpt-4o-mini-2024-07-18` | 13 |
| `gpt-4.1-2025-04-14` | 1 |

### Tool Usage

| Tool | Type | Calls |
|------|------|-------|
| `run_in_terminal` | Built-in | 21 |
| `create_file` | Built-in | 6 |
| `read_file` | Built-in | 3 |
| `grep_search` | Built-in | 1 |
| `multi_replace_string_in_file` | Built-in | 1 |
| `replace_string_in_file` | Built-in | 1 |

> **Note:** 3 automatic `manage_todo_list` calls excluded from the table above.

### Token Budget

| Category | Input | Output | % of Total |
|----------|-------|--------|-----------|
| Primary agent turns | 3.6M | 38.5K | 48% |
| Inference routing (gpt-4o-mini) | 3.7M | 42.8K | 51% |
| **Grand Total** | **7.3M** | **81.2K** | **100%** |

> **Output/Input ratio:** 0.0108

### Per-Turn Breakdown

| Turn | Input Tokens | Output Tokens | Deliberate Tools |
|------|-------------|--------------|-----------------|
| 0 | 129.6K | 114 | `grep_search`, `run_in_terminal`, `run_in_terminal` |
| 1 | 130.0K | 145 | `read_file`, `run_in_terminal`, `create_file` |
| 2 | 131.7K | 2.6K | `multi_replace_string_in_file`, `run_in_terminal`, `run_in_terminal` |
| 3 | 134.3K | 127 | `run_in_terminal`, `read_file` (+1 auto) |
| 0 | 134.7K | 240 | `grep_search`, `run_in_terminal`, `run_in_terminal` |
| 1 | 135.0K | 732 | `read_file`, `run_in_terminal`, `create_file` |
| 2 | 135.7K | 693 | `multi_replace_string_in_file`, `run_in_terminal`, `run_in_terminal` |
| 3 | 136.4K | 244 | `run_in_terminal`, `read_file` (+1 auto) |
| 4 | 136.7K | 185 | `run_in_terminal`, `run_in_terminal` |
| 5 | 136.9K | 505 | `run_in_terminal`, `create_file` |
| 6 | 137.9K | 193 | `run_in_terminal`, `run_in_terminal` |
| 7 | 138.2K | 305 | `run_in_terminal`, `create_file` |
| 8 | 138.7K | 614 | `run_in_terminal`, `run_in_terminal` |
| 9 | 139.4K | 581 | `run_in_terminal`, `create_file` |
| 10 | 140.5K | 1.1K | `create_file`, `read_file` |
| 11 | 141.7K | 159 | `run_in_terminal`, `run_in_terminal` |
| 12 | 141.9K | 240 | `run_in_terminal`, `create_file` |
| 13 | 142.3K | 274 | `run_in_terminal` |
| 14 | 142.7K | 349 | `run_in_terminal` |
| 15 | 143.6K | 2.3K | `replace_string_in_file` |
| 16 | 145.9K | 147 | `run_in_terminal` |
| 17 | 146.7K | 456 | — (+1 auto) |
| 0 | 147.4K | 1.4K | `grep_search`, `run_in_terminal`, `run_in_terminal` |
| 1 | 15.9K | 6.0K | `read_file`, `run_in_terminal`, `create_file` |
| 2 | 22.0K | 140 | `multi_replace_string_in_file`, `run_in_terminal`, `run_in_terminal` |
| 3 | 22.1K | 109 | `run_in_terminal`, `read_file` (+1 auto) |
| 4 | 23.4K | 746 | `run_in_terminal`, `run_in_terminal` |
| 5 | 24.2K | 859 | `run_in_terminal`, `create_file` |
| 6 | 25.1K | 147 | `run_in_terminal`, `run_in_terminal` |
| 7 | 25.8K | 1.3K | `run_in_terminal`, `create_file` |
| 8 | 27.1K | 145 | `run_in_terminal`, `run_in_terminal` |
| 9 | 27.9K | 7.6K | `run_in_terminal`, `create_file` |
| 10 | 35.5K | 107 | `create_file`, `read_file` |
| 11 | 35.6K | 162 | `run_in_terminal`, `run_in_terminal` |
| 12 | 35.8K | 7.3K | `run_in_terminal`, `create_file` |
| 13 | 43.2K | 136 | `run_in_terminal` |

### Input Token Growth Per Turn

```
  Turn  0 | ███████████████████████████████████████████ 129.6K ← grep_search, run_in_terminal, run_in_terminal
  Turn  1 | ████████████████████████████████████████████ 130.0K ← read_file, run_in_terminal, create_file
  Turn  2 | ████████████████████████████████████████████ 131.7K ← multi_replace_string_in_file, run_in_terminal, run_in_terminal
  Turn  3 | █████████████████████████████████████████████ 134.3K ← run_in_terminal, read_file
  Turn  0 | █████████████████████████████████████████████ 134.7K ← grep_search, run_in_terminal, run_in_terminal
  Turn  1 | █████████████████████████████████████████████ 135.0K ← read_file, run_in_terminal, create_file
  Turn  2 | ██████████████████████████████████████████████ 135.7K ← multi_replace_string_in_file, run_in_terminal, run_in_terminal
  Turn  3 | ██████████████████████████████████████████████ 136.4K ← run_in_terminal, read_file
  Turn  4 | ██████████████████████████████████████████████ 136.7K ← run_in_terminal, run_in_terminal
  Turn  5 | ██████████████████████████████████████████████ 136.9K ← run_in_terminal, create_file
  Turn  6 | ██████████████████████████████████████████████ 137.9K ← run_in_terminal, run_in_terminal
  Turn  7 | ██████████████████████████████████████████████ 138.2K ← run_in_terminal, create_file
  Turn  8 | ███████████████████████████████████████████████ 138.7K ← run_in_terminal, run_in_terminal
  Turn  9 | ███████████████████████████████████████████████ 139.4K ← run_in_terminal, create_file
  Turn 10 | ███████████████████████████████████████████████ 140.5K ← create_file, read_file
  Turn 11 | ████████████████████████████████████████████████ 141.7K ← run_in_terminal, run_in_terminal
  Turn 12 | ████████████████████████████████████████████████ 141.9K ← run_in_terminal, create_file
  Turn 13 | ████████████████████████████████████████████████ 142.3K ← run_in_terminal
  Turn 14 | ████████████████████████████████████████████████ 142.7K ← run_in_terminal
  Turn 15 | ████████████████████████████████████████████████ 143.6K ← replace_string_in_file
  Turn 16 | █████████████████████████████████████████████████ 145.9K ← run_in_terminal
  Turn 17 | █████████████████████████████████████████████████ 146.7K
  Turn  0 | ██████████████████████████████████████████████████ 147.4K ← grep_search, run_in_terminal, run_in_terminal
  Turn  1 | █████ 15.9K ← read_file, run_in_terminal, create_file
  Turn  2 | ███████ 22.0K ← multi_replace_string_in_file, run_in_terminal, run_in_terminal
  Turn  3 | ███████ 22.1K ← run_in_terminal, read_file
  Turn  4 | ███████ 23.4K ← run_in_terminal, run_in_terminal
  Turn  5 | ████████ 24.2K ← run_in_terminal, create_file
  Turn  6 | ████████ 25.1K ← run_in_terminal, run_in_terminal
  Turn  7 | ████████ 25.8K ← run_in_terminal, create_file
  Turn  8 | █████████ 27.1K ← run_in_terminal, run_in_terminal
  Turn  9 | █████████ 27.9K ← run_in_terminal, create_file
  Turn 10 | ████████████ 35.5K ← create_file, read_file
  Turn 11 | ████████████ 35.6K ← run_in_terminal, run_in_terminal
  Turn 12 | ████████████ 35.8K ← run_in_terminal, create_file
  Turn 13 | ██████████████ 43.2K ← run_in_terminal
```

---
## Azure SDK MCP Server Analysis

The **Dice Roller Service** session exercised the built-in `azure-sdk-mcp` server,
which ships with VS Code and provides Azure SDK development tools.

### MCP Tools Invoked

| Tool | Full Trace Name | Turn |
|------|----------------|------|
| `azsdk_run_typespec_validation` | `mcp_azure-sdk-mcp_azsdk_run_typespec_validation` | 4 |
| `azsdk_package_generate_code` | `mcp_azure-sdk-mcp_azsdk_package_generate_code` | 6 |

### Observations

1. **Tool naming convention:** MCP tools appear in traces as `mcp_<server-name>_<tool-name>`.
   For the Azure SDK MCP server: `mcp_azure-sdk-mcp_azsdk_*`.

2. **TypeSpec validation** (`azsdk_run_typespec_validation`) was invoked at Turn 4,
   validating the TypeSpec definition before code generation.

3. **Code generation** (`azsdk_package_generate_code`) was invoked at Turn 6,
   generating SDK code from the validated TypeSpec definition.

4. **Workflow pattern:** The agent followed a logical sequence:
   create files (Turns 1–2) → validate spec (Turn 4) → generate code (Turn 6) → run terminal (Turn 8).

5. **Token cost:** MCP tool turns consumed comparable tokens to non-MCP turns (~82–83K each),
   suggesting the MCP tool results don't dramatically inflate context size.

---
## Trace Format Reference

### Event Types

| Event | Count | Description |
|-------|-------|-------------|
| `<no event>` | 505 | Record without event.name (context/metadata) |
| `gen_ai.client.inference.operation.details` | 79 | LLM inference call (routing/classification) |
| `copilot_chat.tool.call` | 47 | A tool invocation by the agent |
| `copilot_chat.agent.turn` | 47 | One complete agent turn (prompt → response) |
| `copilot_chat.session.start` | 4 | New chat session initiated |

### File Format Notes

The file exporter (`github.copilot.chat.otel.outfile`) produces the **OTel JS SDK internal format**,
not standard OTLP JSON. Key structural differences:

| Aspect | OTLP JSON (expected) | Actual Format |
|--------|---------------------|---------------|
| Top-level | `resourceSpans[]` hierarchy | Flat JSONL (one record per line) |
| Session ID | `resource.attributes[].key/value` | `resource._rawAttributes` (array of `[key, value]` pairs) |
| Attributes | Nested `{key, value: {stringValue}}` | Flat dictionary `{key: value}` |
| Event body | Span events array | `_body` field on the record |
| Timestamps | `timeUnixNano` string | `hrTime` array `[seconds, nanoseconds]` |

### Key Attributes

| Attribute | Location | Description |
|-----------|----------|-------------|
| `session.id` | `resource._rawAttributes` | Chat session identifier |
| `turn.index` | `attributes` | Turn number within session (0-based) |
| `event.name` | `attributes` | Event type discriminator |
| `gen_ai.tool.name` | `attributes` | Tool name for tool call events |
| `gen_ai.usage.input_tokens` | `attributes` | Input token count |
| `gen_ai.usage.output_tokens` | `attributes` | Output token count |
| `gen_ai.request.model` | `attributes` | Requested model name |
| `gen_ai.response.model` | `attributes` | Actual model that responded |
| `gen_ai.agent.name` | `attributes` | Agent name (if any) |
| `tool_call_count` | `attributes` | Number of tool calls in a turn |

---
## Key Findings

### 1. Trace Structure Is Flat, Not Hierarchical

Unlike typical OpenTelemetry span hierarchies, the file export produces flat log records.
Tool calls are separate events without `turn.index` — they must be mapped to turns by
their position in the timestamp-ordered stream (tool calls appear between consecutive
`copilot_chat.agent.turn` events).

### 2. Inference Routing Overhead

Each turn generates multiple `gen_ai.client.inference.operation.details` events,
primarily using `gpt-4o-mini` for lightweight routing and classification. These
consume relatively few tokens compared to the primary agent model.

- **Dice Roller Service:** Inference routing = 50% of total input tokens
- **OTel Analysis Session:** Inference routing = 51% of total input tokens

### 3. Context Window Growth

Input tokens grow incrementally with each turn as conversation history accumulates.
In the Dice Roller session, context grew from 81.2K to 84.7K tokens
(3.5K increase, 4% growth over 11 turns).

### 4. Automatic Tool Calls

`manage_todo_list` is invoked automatically at the beginning of most agent turns.
This is not a user-initiated tool call and should be excluded when measuring
deliberate tool usage effectiveness.

- **Dice Roller Service:** 6/11 tool calls were automatic (54%)
- **OTel Analysis Session:** 3/36 tool calls were automatic (8%)

### 5. MCP Server Integration Works End-to-End

The `azure-sdk-mcp` server was successfully discovered and invoked during the
Dice Roller session. Both `azsdk_run_typespec_validation` and
`azsdk_package_generate_code` executed as part of a coherent multi-step workflow.
MCP tool calls appear in traces identically to built-in tools, making them easy to
track and analyze.

---
## Methodology

### Data Collection

| Setting | Value |
|---------|-------|
| Extension | GitHub Copilot Chat (VS Code Insiders) |
| OTel PR | [#3917](https://github.com/microsoft/vscode-copilot-chat/pull/3917) |
| Export method | `github.copilot.chat.otel.outfile` |
| Content capture | `captureContent: true` |
| Trace file | `otel-traces.jsonl` |

### Analysis Pipeline

1. Parse JSONL records from trace file
2. Extract `session.id` from `resource._rawAttributes`
3. Group records by session
4. Sort records within each session by `hrTime`
5. Map tool calls to turns by timestamp ordering
6. Compute per-turn and per-session metrics
7. Score effectiveness using weighted heuristics

### Scoring Heuristics (0-100 scale)

| Factor | Points | Condition |
|--------|--------|-----------|
| Baseline | 50 | Starting score |
| Concise session | +10 | <= 3 turns |
| Long session | -10 | > 15 turns |
| Active tool usage | +10 | > 0 deliberate tool calls |
| Heavy tool usage | +5 | > 20 deliberate tool calls |
| MCP integration | +15 | Any MCP tools used |
| Low token efficiency | -10 | output/input < 0.001 |
| Good token efficiency | +5 | output/input > 0.01 |
| Multi-model | +5 | > 1 model used |
| High routing overhead | -5 | Inference routing > 30% of total |

