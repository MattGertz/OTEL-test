# Copilot Chat OpenTelemetry Instrumentation — Setup Guide

This guide walks you through setting up OpenTelemetry (OTel) tracing for GitHub Copilot Chat using the Aspire Dashboard as a local trace viewer. It assumes no prior experience with Docker or VS Code settings.

---

## Prerequisites

- **VS Code Insiders** — The OTel feature is only available in the Insiders build with Copilot Chat extension v0.40+. Download from <https://code.visualstudio.com/insiders/>.
- **GitHub Copilot subscription** — You must be signed in with a GitHub account that has an active Copilot license.
- **Docker Desktop** — Used to run the Aspire Dashboard container. Download from <https://www.docker.com/products/docker-desktop/>.

---

## Step 1: Install and Start Docker Desktop

1. Download Docker Desktop from the link above and run the installer.
2. Follow the on-screen prompts. Accept the defaults.
3. After installation, Docker Desktop should start automatically. You'll see a whale icon in your system tray (bottom-right of the taskbar on Windows).
4. Wait until Docker Desktop shows **"Docker Desktop is running"** in its dashboard window. This may take a minute on first launch.

> **Tip:** If Docker asks you to enable WSL 2 or Hyper-V, follow its prompts — these are required for Docker to function on Windows.

---

## Step 2: Start the Aspire Dashboard Container

1. Open a terminal (PowerShell, Command Prompt, or the VS Code integrated terminal).
2. Run this command:

   ```powershell
   docker run --rm -d -p 18888:18888 -p 4317:18889 --name aspire-dashboard mcr.microsoft.com/dotnet/aspire-dashboard:latest
   ```

   **What this does:**
   - `docker run` — Creates and starts a new container.
   - `--rm` — Automatically removes the container when it stops (clean up).
   - `-d` — Runs in the background (detached mode).
   - `-p 18888:18888` — Maps port 18888 on your machine to the dashboard's web UI inside the container.
   - `-p 4317:18889` — Maps port 4317 on your machine to the OTLP gRPC receiver inside the container. This is where Copilot Chat sends trace data.
   - `--name aspire-dashboard` — Gives the container a friendly name.
   - `mcr.microsoft.com/dotnet/aspire-dashboard:latest` — The container image to use.

3. Verify it's running:

   ```powershell
   docker ps --filter "name=aspire-dashboard"
   ```

   You should see a row with `aspire-dashboard` and status `Up`.

---

## Step 3: Get the Dashboard Login Token

The Aspire Dashboard requires a login token on first access. Retrieve it from the container logs:

```powershell
docker logs aspire-dashboard
```

Look for a line containing a URL like:

```
Login to the dashboard at http://localhost:18888/login?t=<YOUR_TOKEN_HERE>
```

Open that full URL in your browser, or:
1. Open <http://localhost:18888> in your browser.
2. You'll see a login page asking for a token.
3. Copy the token value from the log output and paste it in.

---

## Step 4: Configure VS Code Insiders Settings

1. Open VS Code Insiders.
2. Open the Settings JSON file:
   - Press `Ctrl+Shift+P` to open the Command Palette.
   - Type **"Preferences: Open User Settings (JSON)"** and select it.
3. Add these settings inside the `{}` braces (if the file already has content, add them after the last existing setting, separated by commas).

### Option A: File Export (Recommended for Analysis)

Writes traces as JSON-lines to a local file. Best for programmatic analysis with the included Python scripts.

   ```json
   "github.copilot.chat.otel.enabled": true,
   "github.copilot.chat.otel.outfile": "C:/Users/mattge/source/repos/scratch/otel-traces.jsonl",
   "github.copilot.chat.otel.captureContent": true
   ```

> **Warning:** `captureContent` includes your prompts and Copilot's responses in the telemetry. This may contain sensitive data. Only enable for local testing.

### Option B: Aspire Dashboard (Visual Inspection)

Sends traces to the Aspire Dashboard for a visual trace viewer UI. Requires Docker (Steps 2-3).

   ```json
   "github.copilot.chat.otel.enabled": true,
   "github.copilot.chat.otel.otlpEndpoint": "http://localhost:4317",
   "github.copilot.chat.otel.exporterType": "otlp-grpc"
   ```

> **Note:** Setting `outfile` overrides `exporterType` — you cannot use both simultaneously. To switch modes, change the settings and reload.

### All Available Settings

   | Setting | Value | Purpose |
   |---|---|---|
   | `github.copilot.chat.otel.enabled` | `true` | Turns on OTel trace/metric/log emission |
   | `github.copilot.chat.otel.outfile` | file path | Write traces as JSON-lines to this file (overrides exporterType to `file`) |
   | `github.copilot.chat.otel.otlpEndpoint` | URL | OTLP collector endpoint (for dashboard mode) |
   | `github.copilot.chat.otel.exporterType` | `otlp-grpc`, `otlp-http`, `console`, `file` | Exporter protocol (default: `otlp-http`) |
   | `github.copilot.chat.otel.captureContent` | `true`/`false` | Include prompt/response content in spans |

4. Save the file (`Ctrl+S`).
5. Reload VS Code Insiders:
   - Press `Ctrl+Shift+P`, type **"Developer: Reload Window"**, and select it.

---

## Step 5: Verify OTel Is Active

1. In VS Code Insiders, open the **Output** panel:
   - Press `Ctrl+Shift+U`, or go to **View → Output** in the menu bar.
2. In the dropdown at the top-right of the Output panel, select **"GitHub Copilot Chat"**.
3. Look for a log line like:

   ```
   [OTel] Instrumentation enabled — exporter=otlp-grpc endpoint=http://localhost:4317/ captureContent=false
   ```

   If you see this, OTel is initialized and sending data.

> **Troubleshooting:** If you don't see the `[OTel]` line, check that you're on Copilot Chat v0.40+ (visible in the same log as `Copilot Chat: 0.40.xxxx`) and that your settings are saved correctly.

---

## Step 6: Generate Traces

1. Open the Copilot Chat panel in VS Code Insiders (click the chat icon in the sidebar, or press `Ctrl+Shift+I`).
2. Send any message — for example: *"What is the square root of 144?"*
3. Wait for the response to complete.

---

## Step 7: View Traces in the Aspire Dashboard

1. Go to <http://localhost:18888> in your browser (log in with the token from Step 3 if needed).
2. Click on **Traces** in the left sidebar.
3. You should see `copilot-chat` resources listed.
4. Click into a trace to see the span hierarchy.

**What to look for:**
- **Root spans** named `invoke_agent` with child spans for `chat` and `execute_tool`
- **Span attributes** following OTel GenAI semantic conventions:
  - `gen_ai.agent.name` — the agent that handled the request
  - `gen_ai.system` — e.g., `copilot`
  - `gen_ai.request.model` — the model used (e.g., `claude-opus-4-6`, `gpt-4o-mini-2024-07-18`)
  - `gen_ai.usage.input_tokens` / `gen_ai.usage.output_tokens` — token counts
  - `gen_ai.tool.name` — tool names on tool-call spans

---

## Understanding the Trace Output

### Trace Structure Per User Prompt

Every chat prompt generates **~4 traces**, not just one:

| Trace | Description | Relevant? |
|---|---|---|
| `invoke_agent GitHub Copilot Chat` | **Your actual request** — the agent loop with tool calls and LLM reasoning | **Yes** |
| `chat gpt-4o-mini` (title) | Auto-generates a title for the chat tab | No — sidecar |
| `chat gpt-4o-mini` (categorization) | Classifies your prompt intent for internal routing | No — sidecar |
| `chat gpt-4o-mini` (summary) | Summarizes the result for chat history | No — sidecar |

You can identify sidecars by the `copilot_chat.debug_log_label` or `gen_ai.agent.name` attribute (values: `title`, `promptCategorization`, `copilotLanguageModelWrapper`).

### Automatic Tool Calls

Every `invoke_agent` trace starts with a `manage_todo_list` tool call (checking for existing task lists). This is automatic — not user-driven. The analysis script (`analyze_sessions.py`) filters these out.

### Key Span Attributes

| Attribute | Where | What it tells you |
|---|---|---|
| `gen_ai.tool.name` | `execute_tool` spans | Which tool was called (e.g., `create_file`, `mcp_azure-mcp_storage`) |
| `gen_ai.tool.call.result` | `execute_tool` spans | The tool's return value |
| `gen_ai.request.model` | `chat` spans | Which LLM model handled this turn |
| `gen_ai.usage.input_tokens` | `chat` spans | Tokens consumed |
| `copilot_chat.time_to_first_token` | `chat` spans | Responsiveness (ms) |
| `copilot_chat.canceled` | any span | Whether the user canceled mid-response |
| `copilot_chat.chat_session_id` | all spans | Groups spans to the same chat session |

---

## Stopping the Dashboard

When you're done testing, stop and remove the container:

```powershell
docker stop aspire-dashboard
```

The `--rm` flag from the original `docker run` command means the container is automatically cleaned up when stopped.

To restart it later, just run the `docker run` command from Step 2 again.

---

## Quick Reference

| Item | Value |
|---|---|
| Dashboard UI | <http://localhost:18888> |
| OTLP gRPC endpoint | `http://localhost:4317` |
| VS Code build required | Insiders with Copilot Chat v0.40+ |
| OTel log marker | `[OTel] Instrumentation enabled` in Output panel |
| Settings prefix | `github.copilot.chat.otel.*` |

---

## Analyzing Traces with Python Scripts

When using file export (Option A), analyze traces with:

```powershell
py analyze_sessions.py otel-traces.jsonl
```

The script automatically:
- **Filters out sidecar traces** (title, categorization, summary)
- **Excludes automatic tool calls** (`manage_todo_list`) from effectiveness metrics
- **Groups by session** using `copilot_chat.chat_session_id`
- **Computes an effectiveness score** (0-100) based on turn count, tool thrashing, cancellation, and token ratios

To view the test plan for structured evaluation:

```powershell
py test_effectiveness.py
```

---

## Environment Variable Alternatives

Instead of VS Code settings, you can use environment variables (they take precedence over settings). Set these before launching VS Code Insiders:

```powershell
$env:COPILOT_OTEL_ENABLED = "true"
$env:OTEL_EXPORTER_OTLP_ENDPOINT = "http://localhost:4317"
$env:OTEL_EXPORTER_OTLP_PROTOCOL = "grpc"
$env:COPILOT_OTEL_CAPTURE_CONTENT = "true"   # optional
code-insiders .
```

---

*Last updated: March 17, 2026*
