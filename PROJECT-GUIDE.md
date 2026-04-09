# Copilot Telemetry Analysis Toolkit

https://github.com/MattGertz/OTEL-test

This project captures, analyzes, and grades GitHub Copilot Chat sessions using OpenTelemetry (OTel) traces. It supports both **VS Code Copilot Chat** and the **Copilot CLI**, with multiple telemetry backends (Aspire Dashboard, file export, and Watson/ATIF pipeline).

---

## Table of Contents

- [What This Project Does](#what-this-project-does)
- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Telemetry Source: VS Code vs. CLI](#telemetry-source-vs-code-vs-cli)
  - [VS Code Session Setup](#vs-code-session-setup)
  - [CLI Session Setup](#cli-session-setup)
  - [Switching Between Sources](#switching-between-sources)
- [Telemetry Backend: Aspire vs. File vs. Watson](#telemetry-backend-aspire-vs-file-vs-watson)
  - [Option A: Raw File Export (Lightweight)](#option-a-raw-file-export-lightweight)
  - [Option B: Aspire Dashboard (Visual)](#option-b-aspire-dashboard-visual)
  - [Option C: Watson + Graders Pipeline (Full Evaluation)](#option-c-watson--graders-pipeline-full-evaluation)
  - [Switching Between Backends](#switching-between-backends)
- [Analysis Scripts](#analysis-scripts)
- [Watson + Copilot Graders Workflow](#watson--copilot-graders-workflow)
- [Test Scenarios](#test-scenarios)
- [Understanding Trace Data](#understanding-trace-data)
- [OTel Documentation References](#otel-documentation-references)
- [Known Issues and Gotchas](#known-issues-and-gotchas)
- [Directory Layout](#directory-layout)

---

## What This Project Does

This toolkit answers the question: **"How effective is a Copilot Chat session?"**

It does this by:

1. **Capturing** OTel traces emitted by Copilot Chat (VS Code or CLI) during real interactions
2. **Analyzing** the traces with Python scripts to extract session-level metrics: turn count, tool calls, token usage, model selection, tool repetition ("thrashing"), cache efficiency, and more
3. **Grading** sessions using the `copilot-graders` tool from the `ai-tools` repo, which runs deterministic and model-backed measurers against ATIF trajectory files
4. **Reporting** findings as markdown documents with per-phase breakdowns, aggregate scores, and actionable observations

The project was built to evaluate Copilot's agentic behavior — especially how it selects and uses tools (built-in and MCP), handles multi-turn workflows, and manages token budgets.

---

## Architecture Overview

```
┌────────────────────┐     ┌─────────────────────┐
│  VS Code Copilot   │     │   Copilot CLI       │
│  Chat Extension    │     │   (>= v1.0.8)       │
└────────┬───────────┘     └────────┬────────────┘
         │ OTel spans                │ OTel spans
         ▼                           ▼
┌──────────────────────────────────────────────────┐
│            Telemetry Backend (pick one)          │
│                                                  │
│  ┌─────────────┐  ┌──────────┐  ┌────────────┐   │
│  │ File Export │  │  Aspire  │  │   Watson   │   │
│  │ (.jsonl)    │  │Dashboard │  │ (OTLP→ATIF)│   │
│  └──────┬──────┘  └────┬─────┘  └─────┬──────┘   │
│         │              │               │         │
└─────────┼──────────────┼───────────────┼─────────┘
          ▼              ▼               ▼
   Python scripts    Browser UI    copilot-graders
   (analyze, scan)   (traces)     (measure + grade)
```

---

## Prerequisites

| Requirement                                                 | Purpose                                       | Install                                                      |
|-------------------------------------------------------------|-----------------------------------------------|--------------------------------------------------------------|
| **Python 3.x**                                              | Analysis scripts                              | `winget install Python.Python.3.12`                          |
| **VS Code Insiders**                                        | OTel feature available in Copilot Chat v0.40+ | [Download](https://code.visualstudio.com/insiders/)          |
| **GitHub Copilot subscription**                             | Required for Copilot Chat                     | Sign in with a licensed GitHub account                       |
| **Docker Desktop**                                          | Only if using Aspire Dashboard backend        | [Download](https://www.docker.com/products/docker-desktop/)  |
| **.NET 10.0 SDK**                                           | Only if using Watson + Graders pipeline       | `winget install Microsoft.DotNet.SDK.10`                     |
| **Copilot CLI** (>= 1.0.8)                                  | Only if capturing CLI sessions                | `npm install -g @github/copilot`                             |
| **ai-tools repo**                                           | Only if using Watson + Graders                | Clone from `github.com/dotnet-microsoft/ai-tools` (internal) |

---

## Telemetry Source: VS Code vs. CLI

Copilot Chat emits OTel traces from two different surfaces. The trace format and configuration method differ significantly.

### VS Code Session Setup

VS Code Copilot Chat has built-in OTel settings. Configure them in your User Settings JSON (`Ctrl+Shift+P` → "Preferences: Open User Settings (JSON)"):

```jsonc
// Required — enables OTel emission
"github.copilot.chat.otel.enabled": true,

// Required — pick ONE of the export options below (see "Telemetry Backend" section)
// For file export:
"github.copilot.chat.otel.outfile": "C:/Users/<you>/source/repos/scratch/otel-traces.jsonl",
// OR for OTLP endpoint (Aspire or Watson):
"github.copilot.chat.otel.otlpEndpoint": "http://localhost:4317",
"github.copilot.chat.otel.exporterType": "otlp-grpc",

// Optional — includes prompt/response text in spans (sensitive!)
"github.copilot.chat.otel.captureContent": true
```

After saving, reload VS Code: `Ctrl+Shift+P` → "Developer: Reload Window".

**Verify it's working:** Open the Output panel (`Ctrl+Shift+U`), select "GitHub Copilot Chat", and look for:

```
[OTel] Instrumentation enabled — exporter=... endpoint=... captureContent=...
```

#### All VS Code OTel Settings

| Setting | Values | Notes |
|-------------------------------------------|------------------|-------------------------------------------------------------------|
| `github.copilot.chat.otel.enabled`        | `true` / `false` | Master switch                                                     |
| `github.copilot.chat.otel.outfile`        | file path        | JSON-lines file export; **overrides** `exporterType` to `file`    |
| `github.copilot.chat.otel.otlpEndpoint`   | URL              | OTLP collector endpoint                                           |
| `github.copilot.chat.otel.exporterType`   | `otlp-grpc`,     | Protocol (default: `otlp-http`)                                   |
|                                           | `otlp-http`,     |                                                                   |
|                                           | `console`,       |                                                                   |
|                                           | `file`           |                                                                   |
|                                           |                  |                                                                   |
| `github.copilot.chat.otel.captureContent` | `true` / `false` | Include prompt/response text in spans                             |

> **Important:** `outfile` and `otlpEndpoint` are mutually exclusive. Setting `outfile` forces file export mode regardless of `exporterType`. To switch modes, remove one and set the other, then reload.

### CLI Session Setup

The Copilot CLI uses standard OTel environment variables. These must be set **in the same terminal process** before launching `copilot`:

```powershell
# Set these in a new PowerShell window (outside VS Code)
$env:OTEL_TRACES_EXPORTER = "otlp"
$env:OTEL_EXPORTER_OTLP_ENDPOINT = "http://localhost:4318"
$env:OTEL_EXPORTER_OTLP_PROTOCOL = "http/protobuf"
$env:OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT = "true"

# Then launch the CLI
copilot
```

> **Critical:** The env vars are process-scoped. If you close the terminal and reopen it, they're gone. Re-set them before each CLI session.

Check the CLI version first: `copilot version` (must be >= 1.0.8).

#### CLI vs. VS Code Port Difference

| Surface | Protocol      | Default Port | Endpoint                |
|---------|---------------|--------------|-------------------------|
| VS Code | gRPC          | 4317         | `http://localhost:4317` |
| CLI     | HTTP/protobuf | 4318         | `http://localhost:4318` |

The Aspire Dashboard maps both: `-p 4317:18889` for gRPC and listens on 4318 for HTTP. Watson listens on both by default.

### Switching Between Sources

To switch from capturing VS Code sessions to CLI sessions (or vice versa):

1. **VS Code → CLI:**
   - No need to change VS Code settings (they can stay enabled — both can emit simultaneously)
   - Set the 4 environment variables in your external terminal
   - If using Watson, restart it with `--agent cli` instead of `--agent vscode`

2. **CLI → VS Code:**
   - If using Watson, restart it with `--agent vscode`
   - Ensure VS Code settings point to the correct backend (`otlpEndpoint` or `outfile`)
   - Reload VS Code

3. **Both simultaneously:**
   - This works with Aspire Dashboard (both send traces to the same collector)
   - With Watson, you need separate Watson instances (one per agent type) or capture them sequentially
   - File export is VS Code-only (CLI doesn't support file export)

---

## Telemetry Backend: Aspire vs. File vs. Watson

### Option A: Raw File Export (Lightweight)

**Best for:** Quick local analysis with the Python scripts. No external services needed.

**VS Code only** — the CLI does not support file export.

```jsonc
"github.copilot.chat.otel.enabled": true,
"github.copilot.chat.otel.outfile": "C:/Users/<you>/source/repos/scratch/otel-traces.jsonl",
"github.copilot.chat.otel.captureContent": true
```

Traces are written as JSON-lines to the specified file. Analyze with:

```powershell
py analyze_sessions.py otel-traces.jsonl
```

**Pros:** Zero dependencies beyond Python. Immediate access to data.
**Cons:** Produces LogRecords, not Trace Spans — incompatible with Watson/Graders. No visual UI. VS Code only.

### Option B: Aspire Dashboard (Visual)

**Best for:** Visual inspection of trace hierarchies. Great for understanding span relationships.

#### Setup

1. Start Docker Desktop
2. Launch the Aspire container:

   ```powershell
   docker run --rm -d -p 18888:18888 -p 4317:18889 --name aspire-dashboard mcr.microsoft.com/dotnet/aspire-dashboard:latest
   ```

3. Get the login token:

   ```powershell
   docker logs aspire-dashboard
   # Look for: Login to the dashboard at http://localhost:18888/login?t=<TOKEN>
   ```

4. Configure VS Code to send to Aspire:

   ```jsonc
   "github.copilot.chat.otel.enabled": true,
   "github.copilot.chat.otel.otlpEndpoint": "http://localhost:4317",
   "github.copilot.chat.otel.exporterType": "otlp-grpc"
   ```

5. Open <http://localhost:18888> and navigate to **Traces**.

**Pros:** Real-time visual trace viewer. See span hierarchies, timing, attributes. Works with both VS Code and CLI.
**Cons:** Requires Docker. No grading/scoring. Data is ephemeral (lost when container stops).

To stop: `docker stop aspire-dashboard`

### Option C: Watson + Graders Pipeline (Full Evaluation)

**Best for:** Systematic evaluation with automated grades. Produces ATIF trajectory files for the copilot-graders framework.

#### How It Works

1. **Watson** (`copilot-watson`) runs as an OTLP receiver, captures traces in real-time, and converts them to ATIF (Agent Trajectory Interchange Format) JSON files
2. **Graders** (`copilot-graders`) runs measurers against the ATIF files and produces pass/fail grades

#### Setup

Build the tools from the `ai-tools` repo:

```powershell
cd C:\Users\mattge\source\repos\ai-tools
dotnet build src\copilot-watson\copilot-watson.csproj
dotnet build src\copilot-graders\copilot-graders.csproj
```

#### Capturing a CLI Session

Terminal 1 — Start Watson:

```powershell
dotnet run --project C:\Users\mattge\source\repos\ai-tools\src\copilot-watson\copilot-watson.csproj `
    -- capture --output C:\Users\mattge\source\repos\scratch\watson-output --agent cli
```

Terminal 2 — Start the CLI (separate PowerShell window, **outside** VS Code):

```powershell
$env:OTEL_TRACES_EXPORTER = "otlp"
$env:OTEL_EXPORTER_OTLP_ENDPOINT = "http://localhost:4318"
$env:OTEL_EXPORTER_OTLP_PROTOCOL = "http/protobuf"
$env:OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT = "true"
copilot
```

#### Capturing a VS Code Session

Terminal 1 — Start Watson:

```powershell
dotnet run --project C:\Users\mattge\source\repos\ai-tools\src\copilot-watson\copilot-watson.csproj `
    -- capture --output C:\Users\mattge\source\repos\scratch\watson-output-vscode --agent vscode
```

VS Code Settings:

```jsonc
"github.copilot.chat.otel.enabled": true,
"github.copilot.chat.otel.otlpEndpoint": "http://localhost:4317",
"github.copilot.chat.otel.exporterType": "otlp-grpc",
"github.copilot.chat.otel.captureContent": true
```

Reload VS Code, then run chat interactions in a **separate** VS Code window.

#### Running Graders

After capturing, Watson writes ATIF files at `watson-output/<session-id>/<session-id>.atif.json`. Run the graders:

```powershell
dotnet run --project C:\Users\mattge\source\repos\ai-tools\src\copilot-graders\copilot-graders.csproj `
    -- measure --trajectory watson-output\<session-id>\<session-id>.atif.json `
    --output grader-results

dotnet run --project C:\Users\mattge\source\repos\ai-tools\src\copilot-graders\copilot-graders.csproj `
    -- grade --measurements grader-results\<timestamp>\measurements.json `
    --output grader-results
```

The graders produce `grades-summary.md` and `measurements-summary.md`.

**Pros:** Automated scoring. Systematic evaluation. Supports both CLI and VS Code.
**Cons:** Requires .NET 10, ai-tools repo. Watson must be running before the session starts. Watson only supports live capture (no offline conversion).

### Switching Between Backends

| From → To       | What to Change                                                                                 |
|-----------------|------------------------------------------------------------------------------------------------|
| File → Aspire   | Remove `outfile`, add `otlpEndpoint` + `exporterType`. Start Docker. Reload VS Code.           |
| File → Watson   | Remove `outfile`, add `otlpEndpoint` + `exporterType`. Start Watson. Reload VS Code.           |
| Aspire → File   | Remove `otlpEndpoint` + `exporterType`, add `outfile`. Reload VS Code. Stop Docker if desired. |
| Aspire → Watson | Just start Watson — it can share the same OTLP port, OR use a different port.                  |
| Watson → File   | Remove `otlpEndpoint`, add `outfile`. Reload VS Code. Stop Watson if desired.                  |

> **Remember:** `outfile` overrides `exporterType`. You cannot use file export and an OTLP endpoint simultaneously.

---

## Analysis Scripts

All scripts are in the project root. Run with `py <script> [args]`.

### Primary Analysis

| Script                | Purpose                                                                                                                                          | Usage                                      |
|-----------------------|--------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------|
| `analyze_sessions.py` | **Main analyzer.** Parses OTLP JSON-lines, groups by session, computes effectiveness scores (0–100), token usage, tool thrashing, MCP usage.     | `py analyze_sessions.py otel-traces.jsonl` |
| `grade_session.py`    | Reconstructs session timeline from the raw OTel file-export format (LogRecords). Shows events, turns, tool calls, inference details, and errors. | `py grade_session.py`                      |
| `gen_report.py`       | Generates a detailed markdown report from OTel traces, mapping tool calls to turns and computing per-session breakdowns.                         | `py gen_report.py`                         |

### Exploratory / Debugging

| Script                 | Purpose                                                                       |
|------------------------|-------------------------------------------------------------------------------|
| `scan_traces.py`       | Quick scan of `otel-traces.jsonl` to list sessions and key stats.             |
| `identify_sessions.py` | Targeted check: which session is which, time ranges, models, tools.           |
| `identify_atif.py`     | Reads Watson ATIF output files and summarizes session metadata.               |
| `deep_analyze.py`      | Enumerate all attribute keys, content attributes, span types, orphan records. |
| `deep_analyze2.py`     | Inspect raw record structures to understand export format differences.        |
| `analyze_test.py`      | Full session analysis with content extraction, agent flow reconstruction.     |

### SQLite Database Scripts

VS Code Insiders also stores traces in a local SQLite database. These scripts query it directly:

| Script                 | Purpose                                                                                           |
|------------------------|---------------------------------------------------------------------------------------------------|
| `query_spans.py`       | Enumerate tables, columns, and sample rows from `agent-traces.db`.                                |
| `analyze_spans.py`     | Trace hierarchy analysis from the SQLite span database — shows timing, tools, content attributes. |
| `extract_session.py`   | Extract user prompts and full conversation flow from a specific trace.                            |
| `show_test_session.py` | Show Watson ATIF session details — user messages, agent flow, tool calls.                         |

The SQLite database is at:
```
%APPDATA%\Code - Insiders\User\globalStorage\github.copilot-chat\agent-traces.db
```

### Effectiveness Scoring

`analyze_sessions.py` computes a heuristic effectiveness score (0–100):

| Signal              | Good                    | Bad                             |
|---------------------|-------------------------|---------------------------------|
| Turn count          | 1–3 turns               | >5 turns (penalty)              |
| Tool calls per turn | Moderate                | >10 per turn (penalty)          |
| Tool repetition     | No thrashing            | Same tool 3+ times (penalty)    |
| User cancellation   | Not canceled            | Canceled (–25 points)           |
| Token ratio         | Reasonable output/input | Very low output ratio (penalty) |

---

## Watson + Copilot Graders Workflow

### Available Measurers

The graders run both **deterministic** (computed from data) and **model-backed** (LLM-evaluated) measurers:

| Measurer                           | Kind                         | What It Measures                                       |
|------------------------------------|------------------------------|--------------------------------------------------------|
| `atif-trajectory-cache-efficiency` | Deterministic                | % of prompt tokens served from cache (threshold: ≥50%) |
| `atif-trajectory-wasted-edits`     | Deterministic                | Edits overwritten by later edits (threshold: 0)        |
| `atif-trajectory-input-tokens`     | Deterministic                | Total prompt tokens consumed                           |
| `atif-trajectory-output-tokens`    | Deterministic                | Total completion tokens produced                       |
| `atif-trajectory-cached-tokens`    | Deterministic                | Total tokens served from cache                         |
| `atif-trajectory-step-count`       | Deterministic                | Total agent steps                                      |
| `atif-trajectory-tool-call-count`  | Deterministic                | Total tool call count                                  |
| `atif-trajectory-total-cost`       | Deterministic                | Estimated cost (uses flat $6/step placeholder)         |
| `atif-trajectory-read-write-ratio` | Deterministic                | Ratio of file reads to writes                          |
| `code-duplication`                 | Model-backed                 | Detects duplicated code                                |
| `comment-quality`                  | Model-backed                 | Evaluates inline comment quality                       |
| `cyclomatic-complexity`            | Deterministic / Model-backed | Function complexity analysis                           |
| `async-exception-handling`         | Model-backed                 | Proper async error handling                            |

### Known Grader Limitations

- **CLI sessions report `tool-call-count = 0`**: The CLI OTLP exporter batches tool calls into agent turn spans rather than emitting them as separate spans. Watson can't extract them.
- **Cost is a placeholder**: Watson records $6 per step. Actual cost requires per-model token pricing.
- **Most measurers need thresholds configured**: Only `cache-efficiency` (≥0.50) and `wasted-edits` (= 0) have default thresholds. Others return `NotEvaluated`.

---

## Test Scenarios

The file `test_effectiveness.py` defines structured test prompts organized by category. Run them manually in Copilot Chat, then analyze the resulting traces:

| Category           | Test IDs           | What It Tests                                                          |
|--------------------|--------------------|------------------------------------------------------------------------|
| Prompt Clarity     | CLEAR-1 to CLEAR-3 | Clear vs. vague vs. ambiguous prompts                                  |
| Tool Effectiveness | TOOL-1 to TOOL-3   | File reads, search patterns, tool thrashing                            |
| Azure MCP          | MCP-1 to MCP-8     | MCP tool selection, accuracy, error handling, multi-tool orchestration |
| Session Patterns   | SESS-1 to SESS-3   | Single-shot, multi-turn, user cancellation                             |
| Token Efficiency   | TOKEN-1 to TOKEN-2 | Concise answers, context bloat                                         |
| Model Usage        | MODEL-1            | Model selection per task type                                          |

Print the test plan:

```powershell
py -c "from test_effectiveness import print_test_plan; print_test_plan()"
```

---

## Understanding Trace Data

### Trace Structure Per User Prompt

Every chat prompt generates **~4 traces**, not just one:

| Trace                               | Description                                                                | Relevant?    |
|-------------------------------------|----------------------------------------------------------------------------|--------------|
| `invoke_agent GitHub Copilot Chat`  | **Your actual request** — the agent loop with tool calls and LLM reasoning | **Yes**      |
| `chat gpt-4o-mini` (title)          | Auto-generates a title for the chat tab                                    | No — sidecar |
| `chat gpt-4o-mini` (categorization) | Classifies prompt intent for routing                                       | No — sidecar |
| `chat gpt-4o-mini` (summary)        | Summarizes the result for chat history                                     | No — sidecar |

Identify sidecars by `gen_ai.agent.name` attribute: `title`, `promptCategorization`, `copilotLanguageModelWrapper`.

### Key Span Attributes

| Attribute                                       | Location             | Meaning                            |
|-------------------------------------------------|----------------------|------------------------------------|
| `gen_ai.tool.name`                              | `execute_tool` spans | Which tool was called              |
| `gen_ai.tool.call.result`                       | `execute_tool` spans | Tool return value                  |
| `gen_ai.request.model`                          | `chat` spans         | LLM model for this turn            |
| `gen_ai.usage.input_tokens`                     | `chat` spans         | Tokens consumed                    |
| `gen_ai.usage.output_tokens`                    | `chat` spans         | Tokens produced                    |
| `gen_ai.usage.reasoning_tokens`                 | `chat` spans         | Reasoning tokens (thinking models) |
| `gen_ai.usage.cache_read.input_tokens`          | `chat` spans         | Tokens served from cache           |
| `copilot_chat.time_to_first_token`              | `chat` spans         | Responsiveness (ms)                |
| `copilot_chat.canceled`                         | any span             | User canceled mid-response         |
| `copilot_chat.chat_session_id`                  | all spans            | Groups spans to the same session   |
| `gen_ai.agent.name`                             | all spans            | Agent that handled the request     |
| `copilot_chat.turn.index`                       | turn spans           | Turn number within the session     |

### Automatic Tool Calls

Every `invoke_agent` trace starts with a `manage_todo_list` tool call (checking for existing task lists). This is automatic — not user-driven. The analysis scripts filter it out by default.

### Data Formats

| Source              | Format                    | Contains                                              |
|---------------------|---------------------------|-------------------------------------------------------|
| VS Code file export | JSON-lines (LogRecords)   | Events with attributes; no span hierarchy             |
| VS Code OTLP        | OTLP gRPC/HTTP (protobuf) | Full trace spans with parent-child relationships      |
| CLI OTLP            | OTLP HTTP (protobuf)      | Full trace spans (tool calls embedded in agent turns) |
| Watson output       | ATIF JSON                 | Structured trajectory with steps, tool calls, diffs   |
| Watson raw log      | `otel-raw.jsonl`          | Pretty-printed OTLP JSON (multi-line, not true JSONL) |
| VS Code SQLite      | `agent-traces.db`         | Spans, attributes, events in relational tables        |

---

## OTel Documentation References

Point the agent at these resources when working with OTel trace data:

### OpenTelemetry Specifications

| Document                                                                                | URL                                                                               | Covers                                            |
|-----------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|---------------------------------------------------|
| OTel Trace Specification                                                                | https://opentelemetry.io/docs/specs/otel/trace/                                   | Spans, traces, context propagation                |
| OTel Semantic Conventions — GenAI                                                       | https://opentelemetry.io/docs/specs/semconv/gen-ai/                               | `gen_ai.*` attribute naming for LLM calls         |
| OTLP Protocol Specification                                                             | https://opentelemetry.io/docs/specs/otlp/                                         | Protocol formats (gRPC, HTTP/protobuf, HTTP/JSON) |
| OTel Exporter Configuration                                                             | https://opentelemetry.io/docs/specs/otel/configuration/sdk-environment-variables/ | `OTEL_*` environment variables                    |

### GenAI Semantic Conventions (Most Relevant)

The GenAI semantic conventions define the attribute names used in Copilot traces:

| Convention    | URL                                                                |
|---------------|--------------------------------------------------------------------|
| GenAI Spans   | https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-spans/   |
| GenAI Metrics | https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-metrics/ |
| GenAI Events  | https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-events/  |

Key attributes from these conventions used in Copilot traces:
- `gen_ai.system` — e.g., `copilot`
- `gen_ai.operation.name` — e.g., `chat`
- `gen_ai.request.model` / `gen_ai.response.model`
- `gen_ai.usage.input_tokens` / `gen_ai.usage.output_tokens`
- `gen_ai.tool.name` / `gen_ai.tool.call.id`

### Aspire Dashboard

| Document                    | URL                                                                                 |
|-----------------------------|-------------------------------------------------------------------------------------|
| Aspire Dashboard Overview   | https://learn.microsoft.com/en-us/dotnet/aspire/fundamentals/dashboard/overview     |
| Standalone Aspire Dashboard | https://learn.microsoft.com/en-us/dotnet/aspire/fundamentals/dashboard/standalone   |

### Copilot-Specific

| Document              | Location                                                                 |
|-----------------------|--------------------------------------------------------------------------|
| Watson & Graders docs | `ai-tools/docs/` directory in the ai-tools repo                          |
| Evaluation docs       | `ai-tools/docs/evaluation/`                                              |
| ATIF format           | Defined by the copilot-watson converter; see ATIF JSON output for schema |

---

## Known Issues and Gotchas

### Configuration Pitfalls

1. **`outfile` overrides `exporterType`** — You cannot use file export and OTLP endpoint simultaneously. Remove `outfile` to use an OTLP endpoint.

2. **CLI env vars are process-scoped** — If you close the terminal and reopen it, the OTEL env vars are gone. Re-set them every time.

3. **Watson must start before the client** — Both the CLI and VS Code silently discard spans if the OTLP receiver isn't reachable. Always start Watson first.

4. **Watson `--agent` flag matters** — Use `--agent cli` for CLI sessions and `--agent vscode` for VS Code sessions. The converters parse different span structures. Using the wrong one produces empty or malformed ATIF files.

5. **Reload VS Code after settings changes** — OTel settings are read at startup. Use `Ctrl+Shift+P` → "Developer: Reload Window".

### Data Format Gotchas

6. **VS Code file export produces LogRecords, not Trace Spans** — These are incompatible with Watson. Watson requires OTLP Trace Spans (protobuf). Use the OTLP endpoint mode for Watson.

7. **Watson's `otel-raw.jsonl` is not true JSONL** — It contains pretty-printed multi-line JSON objects. Parsing requires a brace-depth counter or reading the whole file.

8. **CLI traces lack tool-call granularity** — The CLI batches tool calls into agent turn spans. Watson reports `tool-call-count = 0` for CLI sessions. The raw OTLP log does contain the detail.

### Operational Issues

9. **Watson only supports live capture** — No offline file conversion. You can't retroactively process existing trace files.

10. **The `Set-CopilotCliOtel.ps1` helper may fail** — The Watson repo's PowerShell helper script has had parse errors. Set the 4 env vars manually instead (see [CLI Session Setup](#cli-session-setup)).

11. **VS Code Chat UI eats `@mentions`** — If you type a package name like `@github/copilot` in chat, VS Code interprets the `@` as a mention. Write instructions to a file instead.

12. **The SQLite `agent-traces.db` is separate from OTel export** — VS Code maintains its own span database regardless of OTel settings. The Python scripts can query either source.

---

## Directory Layout

```
scratch/
├── PROJECT-GUIDE.md              ← This file
├── otel-setup-guide.md           ← Step-by-step Aspire Dashboard + VS Code setup
├── cli-instructions.txt          ← CLI env var setup steps (paste into external terminal)
├── copilot-session-analysis.md   ← Detailed analysis report of a CLI session
│
├── analyze_sessions.py           ← Main effectiveness analyzer (OTLP JSON-lines)
├── analyze_test.py               ← Session analysis with content extraction
├── analyze_spans.py              ← SQLite agent-traces.db analyzer
├── extract_session.py            ← Extract prompts/conversation from SQLite
├── query_spans.py                ← SQLite database schema inspector
├── grade_session.py              ← Session timeline reconstruction from OTel file export
├── gen_report.py                 ← Markdown report generator
├── scan_traces.py                ← Quick session listing from otel-traces.jsonl
├── identify_sessions.py          ← Session identification with time ranges
├── identify_atif.py              ← Watson ATIF file summarizer
├── deep_analyze.py               ← Attribute key enumeration, orphan record analysis
├── deep_analyze2.py              ← Raw record structure inspector
├── show_test_session.py          ← Watson ATIF session detail viewer
├── test_effectiveness.py         ← Structured test scenario definitions
│
├── otel-traces.jsonl             ← VS Code file-exported traces (LogRecords)
│
├── watson-output/                ← Watson captures from CLI sessions
│   ├── otel-raw.jsonl            ← Raw OTLP JSON from CLI
│   └── f397d418/                 ← Session trajectory (ATIF)
│       └── f397d418.atif.json
│
├── watson-output-vscode/         ← Watson captures from VS Code sessions
│   ├── otel-raw.jsonl            ← Raw OTLP JSON from VS Code
│   ├── 48de0c87/                 ← Test session trajectory
│   │   └── 48de0c87.atif.json
│   └── fa32508d/                 ← Analysis session trajectory
│
├── grader-results/               ← Grader output from CLI sessions
│   ├── 2026-03-25_180512/
│   │   ├── grades-summary.md
│   │   └── measurements-summary.md
│   └── 2026-04-07_193035/
│       ├── grades-summary.md
│       └── measurements-summary.md
│
├── grader-results-this-session/  ← Grader output from VS Code sessions
│
├── nearest_city_sdk/             ← (Unrelated) Generated SDK example
├── main.py                       ← Python entry point (hello world placeholder)
└── README.md                     ← Original minimal readme
```

---

## Quick Start Recipes

### "I just want to see what Copilot is doing" (5 minutes)

1. Add to VS Code Insiders settings:
   ```jsonc
   "github.copilot.chat.otel.enabled": true,
   "github.copilot.chat.otel.outfile": "C:/path/to/scratch/otel-traces.jsonl"
   ```
2. Reload VS Code. Send a chat message.
3. Run: `py analyze_sessions.py otel-traces.jsonl`

### "I want to visually explore traces" (10 minutes)

1. `docker run --rm -d -p 18888:18888 -p 4317:18889 --name aspire-dashboard mcr.microsoft.com/dotnet/aspire-dashboard:latest`
2. Get token: `docker logs aspire-dashboard`
3. Set VS Code settings for OTLP endpoint (port 4317, `otlp-grpc`)
4. Open <http://localhost:18888> → Traces

### "I want to systematically grade a session" (30 minutes)

1. Build Watson and Graders from the ai-tools repo
2. Start Watson with `-- capture --output ./watson-output --agent vscode`
3. Configure VS Code OTLP settings → Reload → Run chat interactions
4. Run Graders: `measure` then `grade`
5. Read `grades-summary.md`
