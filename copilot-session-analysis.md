# Copilot CLI Session Analysis Report

**Session ID:** `f397d418-a232-4c0e-b08e-34009ac14369`
**Date:** March 25, 2026
**Duration:** ~31 minutes (17:23 – 17:54 UTC)
**Agent:** GitHub Copilot CLI v1.0.12-0
**Primary Model:** Claude Opus 4.6 (1M context)
**Subagent Model:** Claude Haiku 4.5

## Task Summary

The user asked the Copilot CLI to create a **SunTimes** Azure service in the `azure-sdk-tools` repository. The service accepts GPS coordinates (or a city name) and a date, returning sunrise/sunset times with timezone-aware DST handling. The end-to-end workflow was:

1. Define the service in TypeSpec
2. Compile and validate the TypeSpec
3. Generate a Python SDK from the TypeSpec definition
4. Use the Azure SDK MCP server (`azsdk`, 69 tools) throughout

The agent completed all objectives, producing a TypeSpec service definition, OpenAPI spec, and a fully-generated Python SDK with sync/async clients from scratch.

## Toolchain

| Tool | Role |
|------|------|
| **copilot-watson** | Captured OTLP traces from the CLI and converted them to ATIF trajectory format |
| **copilot-graders** | Ran 9 trajectory measurers and produced pass/fail grades |
| **Copilot CLI** | The agent under test |
| **Azure SDK MCP Server** | Provided 69 domain-specific tools for TypeSpec/SDK workflows |

## Copilot Grader Results

### Measurements

| Measurer | Value | Direction | Explanation |
|----------|------:|-----------|-------------|
| **cache-efficiency** | **0.947** (94.7%) | Higher is better | 5,894,173 of 6,225,557 prompt tokens served from cache |
| **cached-tokens** | 5,894,173 | Higher is better | Total tokens served from prompt cache |
| **input-tokens** | 6,225,557 | Lower is better | Total prompt tokens consumed |
| **output-tokens** | 24,709 | Lower is better | Total completion tokens produced |
| **read-write-ratio** | 0.0 | Lower is better | 0 reads, 0 writes recorded (tool calls not captured in ATIF) |
| **step-count** | 62 | Lower is better | 62 agent steps (excludes user/system messages) |
| **tool-call-count** | 0 | Lower is better | Tool calls not individually captured in ATIF format |
| **total-cost** | $360 | Lower is better | Placeholder cost ($6/step; see note below) |
| **wasted-edits** | 0 | Lower is better | No edits were overwritten by later edits |

### Grades

| Measurer | Grade | Threshold | Aggregate |
|----------|-------|-----------|-----------|
| cache-efficiency | **Pass** | 0.50 | 0.947 |
| wasted-edits | **Pass** | 0 | 0 |
| All others | NotEvaluated | — | No threshold configured |

> **Note on cost:** Watson records `$6` per step as a flat placeholder; actual cost depends on provider pricing. The `$360` total is **not** the real cost. True cost would need to be calculated from token counts and per-model rates.

## Phase-by-Phase Breakdown

### Phase 1: Setup (Steps 1–6) — 43s

Confirmed the Azure SDK MCP server was running and listed its 69 available tools. Quick and efficient — the user had already set up the MCP server in a prior session.

| Metric | Value |
|--------|------:|
| Agent steps | 4 |
| Prompt tokens | 322,638 |
| Completion tokens | 1,128 |
| Cache hit rate | 75% |

### Phase 2: Exploration (Steps 7–11) — 68s

User gave the main prompt. The agent spawned a Haiku subagent (`explore-typespec`) that produced a comprehensive 3,600-token summary of existing TypeSpec patterns, configurations, and conventions in the repo. This research was thorough but time-consuming.

| Metric | Value |
|--------|------:|
| Agent steps | 4 |
| Prompt tokens | 316,324 |
| Completion tokens | 4,789 |
| Cache hit rate | 67% |

### Phase 3: TypeSpec Creation (Steps 12–27) — 298s

The agent created `main.tsp`, `tspconfig.yaml`, `package.json`, installed dependencies, and compiled. TypeSpec compiled successfully but produced **2 linter warnings** about `use-standard-operations`.

| Metric | Value |
|--------|------:|
| Agent steps | 15 |
| Prompt tokens | 1,357,495 |
| Completion tokens | 4,348 |
| Cache hit rate | 99% |

**Created files:**
- `specification/suntimes/SunTimes/main.tsp`
- `specification/suntimes/SunTimes/tspconfig.yaml`
- `specification/suntimes/SunTimes/package.json`
- Generated OpenAPI spec

**Endpoints defined:**
- `GET /suntimes/by-coordinates?latitude=...&longitude=...&date=...`
- `GET /suntimes/by-city?city=...&date=...`

### Phase 4: Warning Fix (Steps 28–54) — 631s (largest phase)

The user pushed back on the 2 linter warnings. The agent spawned a second Haiku subagent (`azure-core-ops`) that spent **5 minutes** researching Azure.Core standard operations, producing a 4,600-token reference document. The agent then rewrote the operations using `RpcOperation` to eliminate all warnings.

| Metric | Value |
|--------|------:|
| Agent steps | 25 |
| Prompt tokens | 2,613,512 |
| Completion tokens | 10,281 |
| Cache hit rate | 95% |

This was the most expensive phase — 42% of total prompt tokens and 42% of completion tokens. The agent should have used `RpcOperation` from the start, since existing examples in the repo (e.g., CityFinder) demonstrated the pattern.

**Top slowest individual step:** Step 30 (Haiku subagent research) at **300 seconds** — by far the single longest operation.

### Phase 5: Python SDK Generation (Steps 55–68) — 321s

Used the MCP server's `azsdk_package_generate_code` tool. Hit a lockfile issue requiring two regeneration attempts before succeeding.

| Metric | Value |
|--------|------:|
| Agent steps | 12 |
| Prompt tokens | 1,366,547 |
| Completion tokens | 2,467 |
| Cache hit rate | 99% |

**Generated Python SDK at** `azure-sdk-for-python/sdk/suntimes/azure-suntimes/`:
- `SunTimesClient` (sync) + async client
- `SunTimesResult` model with proper type mappings
- Operations: `get_by_coordinates()`, `get_by_city()`
- Test scaffolding, packaging files

### Phase 6: Wrap-up (Steps 69–71) — 51s

User asked for a session notes markdown file; agent wrote `specification/suntimes/SESSION_NOTES.md` with lessons learned and a self-assessment.

| Metric | Value |
|--------|------:|
| Agent steps | 2 |
| Prompt tokens | 249,041 |
| Completion tokens | 1,696 |
| Cache hit rate | 99% |

## Aggregate Metrics

| Metric | Value |
|--------|------:|
| Total steps | 71 (62 agent, 5 user, 4 system) |
| Wall-clock time | ~31 minutes |
| Total agent compute time | ~1,412s (sum of step durations) |
| Total prompt tokens | 6,225,557 |
| Total completion tokens | 24,709 |
| Total cached tokens | 5,894,173 |
| **Cache hit rate** | **94.7%** |
| Wasted edits | 0 |
| User interventions | 5 messages |
| Models used | 2 (Opus 4.6 primary, Haiku 4.5 subagent) |

## Top 5 Slowest Steps

| Step | Duration | Model | Prompt Tokens | Completion Tokens | Phase |
|-----:|---------:|-------|-------------:|------------------:|-------|
| 30 | 300.2s | Haiku 4.5 | 224,998 | 4,643 | Warning fix (subagent research) |
| 65 | 96.4s | Opus 4.6 | 114,846 | 227 | SDK generation |
| 62 | 75.2s | Opus 4.6 | 112,894 | 389 | SDK generation |
| 16 | 72.1s | Opus 4.6 | 88,890 | 203 | TypeSpec creation |
| 58 | 67.9s | Opus 4.6 | 111,525 | 203 | SDK generation |

## Azure SDK MCP Server Usage Analysis

The raw OTLP data (1.2 MB, 41 ResourceSpans batches) reveals tool-level detail that the ATIF trajectory summary does not. The following is derived from the `execute_tool` spans in the raw telemetry.

### Complete Tool Call Inventory (83 total)

| Tool | Count | Purpose |
|------|------:|---------|
| `view` | 35 | Read files and list directories |
| `powershell` | 11 | Shell commands (npm install, tsp compile, azsdk CLI) |
| `grep` | 9 | Search file contents |
| `glob` | 9 | File pattern matching |
| `report_intent` | 5 | Declare intent to the user |
| `edit` | 5 | Modify `main.tsp` (all 5 edits targeted a single file) |
| `task` | 3 | Spawn subagent tasks |
| `create` | 3 | Create `main.tsp`, `tspconfig.yaml`, `package.json` |
| `read_agent` | 2 | Retrieve subagent results |

### How the MCP Server Was Used

The agent did **not** invoke the Azure SDK MCP server's tools via MCP protocol. Instead, it used `powershell` tool calls to run `dotnet run --project ./tools/azsdk-cli/Azure.Sdk.Tools.Cli` commands directly. Specific azsdk invocations:

| Shell Command | Description |
|---------------|-------------|
| `Get-Process -Name "azsdk"` | Verified the MCP server process was running |
| `dotnet run ... -- mcp` (with stdout parsing) | Listed available MCP tools (returned 69 tool names) |
| `dotnet run ... -- package generate --package-path specification/suntimes/SunTimes --language python --help` | Checked SDK generation syntax |
| `dotnet run ... -- package generate ...` | Actual SDK generation (implied from later steps) |

**Assessment:** The agent used the azsdk CLI correctly for its two substantive operations (listing tools and generating the SDK), but it bypassed the MCP tool-calling protocol entirely. It invoked the CLI binary via shell rather than calling MCP tools like `azsdk_package_generate_code` directly. This means:

- The MCP server's 69 tools were **available but mostly unused** — of 69 tools, at most 2-3 were exercised (status check, tool listing, code generation).
- TypeSpec-related tools (`azsdk_init_project`, `azsdk_run_validation`, `azsdk_generate_authoring_plan`) were **not used**. The agent wrote TypeSpec files manually using `create` and `edit` tools, compiled with `npx tsp compile` via shell, and did its own linter research via subagents.
- The `azsdk_convert_swagger`, `azsdk_check_api_spec_ready_for_sdk`, and `azsdk_run_validation` tools could have shortened the warning-fix phase significantly.

### File Operation Patterns

The agent's 35 `view` calls broke down into clear categories:

| Category | Count | Examples |
|----------|------:|---------|
| Exploring existing TypeSpec examples | 15 | `diceroller/main.tsp`, `booklibrary/main.tsp`, `cityfinder/main.tsp`, their configs |
| Exploring Azure.Core library internals | 8 | `node_modules/@azure-tools/typespec-azure-core/lib/operations.tsp` |
| Verifying own work output | 6 | `specification/suntimes/...`, generated OpenAPI, SDK files |
| Reading documentation | 4 | `mcp-tools.md`, `specs/README.md`, `tsp-client/README.md` |
| Repo-level exploration | 2 | Root directory, `package.json` |

The 5 `edit` calls all targeted `main.tsp` — corresponding to the iterative fix of the linter warnings (rewriting operations from raw `op` to `RpcOperation`).

## Key Observations

1. **Cache efficiency is excellent at 94.7%.** The 1M context window allowed the agent to reuse context heavily across the many rapid-fire tool-calling steps. Only Phase 2 (67%) showed lower cache rates, likely due to the large subagent response introducing new content.

2. **The warning-fix phase was disproportionately expensive.** It consumed 42% of all tokens and 47% of wall-clock time. The agent initially used raw `op` declarations instead of `RpcOperation`, which violated the Azure linter rules. A more experienced agent should have recognized the `RpcOperation` pattern from the existing examples (CityFinder, BookLibrary) during the exploration phase.

3. **Subagent research calls are very costly.** The two Haiku subagent calls (steps 11 and 30) together consumed 8,258 completion tokens and ~340 seconds. The 5-minute Haiku research step was the single most expensive operation. The main Opus agent could have made targeted tool calls instead of delegating broad research to a subagent.

4. **The MCP server was underutilized.** Despite 69 available tools, the agent relied on shell commands and manual file operations for most of the workflow. It read TypeSpec library internals manually (8 `view` calls into `node_modules`) when the MCP server had purpose-built validation and generation tools. The user explicitly told the agent to use the MCP server (step 28: "I already said the MCP server should be used when appropriate"), but this correction had limited effect.

5. **Zero wasted edits** — the 5 edits to `main.tsp` were sequential refinements, none overwritten. However, all 5 targeted the same file, indicating iterative trial-and-error on linter compliance rather than getting it right from the exploration data.

6. **Heavy read-to-write ratio.** 35 views + 9 greps vs. 5 edits + 3 creates = 44 reads to 8 writes (5.5:1). This is reasonable for an exploration-heavy task, but the reading was partly redundant — the agent explored the same example files in both the main session and the Haiku subagent.

7. **The user was concise and the agent was autonomous.** Only 5 user messages drove 62 agent steps. The autonomy ratio (~12 agent steps per user message) reflects efficient delegation.

## Limitations of This Analysis

### What copilot-graders could not measure

Several grader metrics returned 0 or NotEvaluated due to limitations in the ATIF data captured from the CLI:

- **tool-call-count = 0**: The CLI's OTLP exporter doesn't emit individual tool calls as separate spans the way VS Code does. Tool invocations are embedded within agent response spans but not parsed into the ATIF step structure.
- **read-write-ratio = 0**: Same root cause — file reads and writes aren't captured as distinct tool-call events.
- **total-cost = $360 (placeholder)**: Watson writes a flat $6/step rather than computing actual cost from token counts and model pricing.
- **No threshold configured** for most measurers: Only `cache-efficiency` (≥0.50) and `wasted-edits` (= 0) had thresholds, so 7 of 9 graders returned `NotEvaluated`.

### What data would have been helpful to collect

1. **Individual tool call traces.** The CLI's OTLP exporter batches tool calls into agent turn spans. If each tool call were a separate span (as VS Code's exporter does), we'd get accurate `tool-call-count`, `read-write-ratio`, and `wasted-edits` metrics. This is a CLI exporter gap.

2. **File diff content.** Watson can extract unified diffs from tool calls that perform edits (create, edit, replace), but the CLI didn't emit these in its spans. Having diffs would enable the `wasted-edits` measurer to detect overwrites and let us trace exactly what was written and rewritten.

3. **Accurate per-model cost rates.** Watson records a flat $6/step regardless of model or token count. Configuring actual pricing (e.g., Opus at $X/1M input tokens, Haiku at $Y/1M) would make the `total-cost` measurer meaningful.

4. **MCP tool invocation details.** The agent called the azsdk CLI via shell commands rather than through MCP protocol. While we were able to extract this from the raw OTLP `powershell` spans, a proper MCP tool call trace (tool name, arguments, duration, success/failure) would make the analysis automatic and enable the graders to measure MCP usage directly.

5. **User satisfaction / task correctness signal.** The graders measure efficiency (tokens, steps, cache) and quality (wasted edits), but there's no metric for "did the output actually work?" A post-hoc validation step (e.g., does the TypeSpec compile? Does the generated SDK pass type-checking?) would close this gap.

6. **Subagent traces in the primary trajectory.** The two Haiku subagent calls appear as single steps in the main trajectory, but their internal multi-turn conversations are opaque. Inlining subagent traces (or at least their token/tool summaries) would give a fuller picture of total work performed.

7. **Latency breakdown (model vs. network vs. tool execution).** The `duration_ms` field captures end-to-end step time but doesn't distinguish model inference time from network latency from tool execution time. The `msbench-trajectory-model-vs-tool-duration` measurer exists for MSBench format but has no ATIF equivalent.

---

## Appendix: Data Collection Setup

Getting the toolchain working end-to-end required substantial trial and error. This appendix documents what was needed, what went wrong, and what the final working configuration looked like.

### Prerequisites

- **.NET 10.0 SDK** (10.0.104) — already installed; required for building copilot-watson and copilot-graders
- **GitHub Copilot CLI** (v1.0.11, installed via `npm install -g @github/copilot`) — must be >= 1.0.8-0 for OTLP support
- **ai-tools repo** cloned from `github.com/dotnet-microsoft/ai-tools` (internal, SSO-gated)

### Step 1: Building the Tools

Both tools built cleanly from the ai-tools repo root:

```
dotnet build src\copilot-watson\copilot-watson.csproj    # 28s
dotnet build src\copilot-graders\copilot-graders.csproj  # 17s
```

Both target `net10.0`. Watson depends on `Copilot.Watson`; Graders depends on `Copilot.Graders` and `Copilot.Graders.Builtins`.

### Step 2: Initial Attempt — VS Code File Exporter (Failed)

We initially tried to use existing `otel-traces.jsonl` data captured by VS Code's file-based OTel exporter (`github.copilot.chat.otel.*` settings). This produced LogRecords, not Trace Spans. Watson requires OTLP Trace Spans (protobuf over HTTP/gRPC), so this data was **incompatible**.

### Step 3: VS Code OTLP Endpoint (Failed)

We added `"chat.completions.tracing.otlpEndpoint": "http://localhost:4317"` to VS Code settings. Watson was running and listening. Ran a Copilot chat interaction in a separate VS Code window. **No traces arrived.** The setting either doesn't exist in this VS Code Insiders build, isn't wired up, or requires a different configuration. We abandoned this approach.

### Step 4: Copilot CLI Setup (Working, After Several Issues)

**Issue 1: CLI not installed.** The shim at `AppData\Roaming\Code - Insiders\...` was a VS Code wrapper that bundled an old CLI version. We installed the standalone CLI via npm.

**Issue 2: Helper script parse error.** The Watson repo includes `Set-CopilotCliOtel.ps1` to configure environment variables. It failed with a PowerShell parse error about a "missing terminator" on line 77. Root cause was unclear — the file bytes looked clean (all ASCII). We bypassed the script entirely and set the 4 environment variables manually:

```powershell
$env:OTEL_TRACES_EXPORTER = "otlp"
$env:OTEL_EXPORTER_OTLP_ENDPOINT = "http://localhost:4318"
$env:OTEL_EXPORTER_OTLP_PROTOCOL = "http/protobuf"
$env:OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT = "true"
```

**Issue 3: Watson started with wrong agent type.** Initially started Watson with `--agent vscode`, then had to kill and restart with `--agent cli` when we switched to the CLI.

**Issue 4: Environment variables lost between sessions.** The env vars are process-scoped. When the user exited the CLI and restarted it, the vars were gone. First CLI session produced zero traces. After re-setting the vars, traces began flowing.

**Issue 5: Chat UI eating commands.** Commands containing `@github/copilot` (the npm package name) were interpreted as `@mentions` by the VS Code Chat UI and disappeared from the response. We worked around this by writing instructions to a file (`cli-instructions.txt`) instead of displaying them inline.

### Final Working Configuration

```
Terminal 1 (Watson receiver, inside VS Code):
  dotnet run --project <ai-tools>\src\copilot-watson\copilot-watson.csproj \
    -- capture --output <scratch>\watson-output --agent cli

Terminal 2 (Copilot CLI, external PowerShell):
  $env:OTEL_TRACES_EXPORTER = "otlp"
  $env:OTEL_EXPORTER_OTLP_ENDPOINT = "http://localhost:4318"
  $env:OTEL_EXPORTER_OTLP_PROTOCOL = "http/protobuf"
  $env:OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT = "true"
  cd C:\Users\mattge\source\repos\azure-sdk-tools
  copilot
```

The CLI sends OTLP/HTTP (protobuf) spans to Watson on port 4318. Watson converts them to ATIF and writes trajectory files per session. After the CLI session ends, copilot-graders runs the ATIF measurers.

### Lessons Learned

1. **Watson only supports live capture** — no offline file conversion. If you already have trace data in a different format, it can't be retroactively processed.
2. **The CLI's OTLP exporter is reliable once configured** — but the env vars must be set in the same process where `copilot` runs, and must be set before launch.
3. **Watson must be started before the CLI** — the CLI silently discards spans if the receiver isn't reachable.
4. **The ATIF output from the CLI converter lacks tool-call granularity** compared to VS Code traces. Individual tool calls are embedded in chat spans rather than being separate entries, which is why copilot-graders reported `tool-call-count = 0`. The raw OTLP log (`otel-raw.jsonl`) does contain the detail and can be parsed separately.
5. **The whole setup took longer than the actual analysis** — approximately 60 minutes of configuration and debugging vs. 31 minutes of captured CLI interaction and 5 minutes of grading.

### Ad Hoc Python Scripts for Analysis

The analysis required approximately 10 ephemeral Python scripts run inline via the terminal. These were necessary because the toolchain has a gap: **copilot-watson produces ATIF trajectory JSON, and copilot-graders consumes it, but neither tool provides a human-readable exploratory view** of the data at the level of detail needed for the report. The graders output aggregate scores (e.g., "62 steps", "94.7% cache efficiency") but not the per-phase, per-model, or per-tool breakdowns that tell the story.

#### Why Python and not copilot-graders?

Copilot-graders runs predefined measurers that produce a single numeric score per metric. It answers "how many total steps?" but not "how many steps per phase?" or "which model was used for each step?" or "what did the agent actually do with the MCP server?" These are exploratory analytical questions that don't map to the fixed measurer framework.

The raw OTLP log (`otel-raw.jsonl`, 1.2 MB) was particularly challenging. Watson writes it as pretty-printed multi-line JSON objects concatenated together — not true JSONL (one object per line). Parsing it required a custom brace-depth counter:

```python
objects = []
depth = 0
start = 0
for i, c in enumerate(content):
    if c == '{':
        if depth == 0:
            start = i
        depth += 1
    elif c == '}':
        depth -= 1
        if depth == 0:
            objects.append(content[start:i+1])
```

#### What the scripts did

| Script | Purpose | Why it was needed |
|--------|---------|-------------------|
| Trajectory structure inspection | Read `f397d418.atif.json`, enumerate step types, extract user messages, identify models | The ATIF file is 50 KB / 1,194 lines of JSON; manual reading isn't feasible |
| Per-phase token aggregation | Group the 62 agent steps into 6 logical phases, sum prompt/completion/cached tokens per phase | Graders only report totals; the phase breakdown was essential for understanding where time and tokens were spent |
| Slowest-step ranking | Sort all steps by `duration_ms`, identify the top 5 | Pinpointed the 5-minute Haiku subagent call as the dominant bottleneck |
| Event type enumeration | Scan the original `otel-traces.jsonl` file to list distinct `event.name` values | Needed early on to determine whether the pre-existing VS Code traces were compatible with Watson (they weren't) |
| Raw OTLP parsing | Parse the multi-line JSON in `otel-raw.jsonl`, extract `execute_tool` spans | The ATIF trajectory reported 0 tool calls; the raw OTLP had the actual 83 tool calls embedded in span attributes |
| Tool call categorization | Separate `powershell` spans into azsdk-related vs. regular commands | Needed to assess MCP server utilization — were the 69 tools actually called? |
| View target extraction | Catalog all 35 `view` tool calls by file path | Revealed the agent's exploration pattern (15 calls reading existing TypeSpec examples, 8 diving into `node_modules`) |
| Edit/create target extraction | Catalog `edit` and `create` tool call arguments | Showed all 5 edits targeted `main.tsp` — evidence of iterative linter-fix attempts |

#### The gap this reveals

There's a clear opportunity for a `copilot-watson report` or `copilot-graders analyze` command that produces a narrative-style breakdown from ATIF + raw OTLP data, rather than just aggregate scores. The raw OTLP log contains rich tool-call detail that Watson's ATIF converter discards (because the CLI converter doesn't map `execute_tool` spans to ATIF tool-call steps). A purpose-built analysis tool would eliminate the need for these ad hoc scripts.
