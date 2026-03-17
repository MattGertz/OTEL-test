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
3. Add these settings inside the `{}` braces (if the file already has content, add them after the last existing setting, separated by commas):

   ```json
   "github.copilot.chat.otel.enabled": true,
   "github.copilot.chat.otel.otlpEndpoint": "http://localhost:4317",
   "github.copilot.chat.otel.exporterType": "otlp-grpc"
   ```

   **What each setting does:**
   | Setting | Value | Purpose |
   |---|---|---|
   | `github.copilot.chat.otel.enabled` | `true` | Turns on OTel trace/metric/log emission |
   | `github.copilot.chat.otel.otlpEndpoint` | `http://localhost:4317` | Where to send telemetry (the Aspire Dashboard's OTLP receiver) |
   | `github.copilot.chat.otel.exporterType` | `otlp-grpc` | Protocol to use (must match the Aspire Dashboard's gRPC endpoint) |

   **Other available values for `exporterType`:** `otlp-http`, `console`, `file`

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

## Optional: Enable Content Capture

By default, message content is **not** included in traces (for privacy). To enable it:

1. Add this setting to your `settings.json`:

   ```json
   "github.copilot.chat.otel.captureContent": true
   ```

2. Reload VS Code Insiders (`Ctrl+Shift+P` → **Developer: Reload Window**).
3. Send a chat message and check the trace in the Aspire Dashboard.
4. You should now see additional attributes like `gen_ai.content.prompt` and `gen_ai.content.completion` on spans.

> **Warning:** Content capture includes your prompts and Copilot's responses in the telemetry. This may contain sensitive data. Only enable for local testing.

---

## Optional: Check Metrics and Events

In the Aspire Dashboard:
- **Metrics tab** — Look for metrics like `gen_ai.client.operation.duration` and `copilot_chat.tool.call.count`.
- **Events within traces** — Click into individual spans to see events such as `copilot_chat.session.start` and `copilot_chat.tool.call`.

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
