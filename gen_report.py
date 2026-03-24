"""Generate a detailed Markdown report from OTel trace data."""
import json
from collections import defaultdict, Counter
from datetime import datetime

TRACE_FILE = "otel-traces.jsonl"
REPORT_FILE = "session-analysis-report.md"

DICE_SID = "c6a2449f-ab16-46a4-b608-2adf5fc2aa031773851507809"
THIS_SID = "f18e08a5-2eee-4670-96ff-92c3b90169471773851507818"
AUTO_TOOLS = {"manage_todo_list"}


def load_records():
    records = []
    with open(TRACE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            attrs = rec.get("attributes", {})
            res = rec.get("resource", {})
            res_attrs = dict(res.get("_rawAttributes", []))
            sid = res_attrs.get("session.id", attrs.get("session.id", None))
            records.append({
                "raw": rec,
                "sid": sid,
                "event": attrs.get("event.name", ""),
                "body": str(rec.get("_body", "")),
                "tool": attrs.get("gen_ai.tool.name", ""),
                "model": attrs.get("gen_ai.request.model", ""),
                "resp_model": attrs.get("gen_ai.response.model", ""),
                "agent": attrs.get("gen_ai.agent.name", ""),
                "op": attrs.get("gen_ai.operation.name", ""),
                "input_tok": int(attrs.get("gen_ai.usage.input_tokens", 0)),
                "output_tok": int(attrs.get("gen_ai.usage.output_tokens", 0)),
                "turn": attrs.get("turn.index", None),
                "success": attrs.get("success", None),
                "duration": attrs.get("duration_ms", None),
                "tool_calls": int(attrs.get("tool_call_count", 0)),
                "hrTime": rec.get("hrTime", [0, 0]),
            })
    return records


def analyze_session(records, sid, label):
    session = [r for r in records if r["sid"] == sid]
    session.sort(key=lambda r: r["hrTime"])

    turn_events = [r for r in session if r["event"] == "copilot_chat.agent.turn"]
    tool_events = [r for r in session if r["event"] == "copilot_chat.tool.call"]
    inference_events = [r for r in session if r["event"] == "gen_ai.client.inference.operation.details"]

    # Map tool calls to turns by position in ordered stream
    tool_to_turn = {}
    current_turn = -1
    tool_idx = 0
    for r in session:
        if r["event"] == "copilot_chat.agent.turn":
            current_turn = r["turn"] if r["turn"] is not None else current_turn + 1
        elif r["event"] == "copilot_chat.tool.call":
            tool_to_turn[tool_idx] = current_turn
            tool_idx += 1

    # Models
    req_models = Counter()
    resp_models = Counter()
    for r in inference_events:
        if r["model"]:
            req_models[r["model"]] += 1
        if r["resp_model"]:
            resp_models[r["resp_model"]] += 1

    # Tokens from turn events
    total_input = sum(r["input_tok"] for r in turn_events)
    total_output = sum(r["output_tok"] for r in turn_events)
    inference_input = sum(r["input_tok"] for r in inference_events)
    inference_output = sum(r["output_tok"] for r in inference_events)

    # Tools
    tools = defaultdict(int)
    mcp_tools = defaultdict(int)
    auto_tool_count = 0
    for r in tool_events:
        if r["tool"] in AUTO_TOOLS:
            auto_tool_count += 1
        elif r["tool"].startswith("mcp_"):
            mcp_tools[r["tool"]] += 1
        else:
            tools[r["tool"]] += 1

    # Per-turn details
    turn_details = []
    for r in turn_events:
        tidx = r["turn"] if r["turn"] is not None else len(turn_details)
        turn_tools = []
        for ti, mapped_turn in tool_to_turn.items():
            if mapped_turn == tidx:
                t = tool_events[ti]["tool"]
                turn_tools.append(t)
        turn_details.append({
            "index": tidx,
            "input_tok": r["input_tok"],
            "output_tok": r["output_tok"],
            "tools": [t for t in turn_tools if t not in AUTO_TOOLS],
            "auto_tools": [t for t in turn_tools if t in AUTO_TOOLS],
        })

    return {
        "label": label,
        "sid": sid,
        "total_records": len(session),
        "turn_count": len(turn_events),
        "tool_event_count": len(tool_events),
        "inference_event_count": len(inference_events),
        "total_input": total_input,
        "total_output": total_output,
        "inference_input": inference_input,
        "inference_output": inference_output,
        "req_models": dict(req_models.most_common()),
        "resp_models": dict(resp_models.most_common()),
        "tools": dict(sorted(tools.items(), key=lambda x: -x[1])),
        "mcp_tools": dict(sorted(mcp_tools.items(), key=lambda x: -x[1])),
        "auto_tool_count": auto_tool_count,
        "turns": turn_details,
    }


def score_session(a):
    score = 50
    reasons = []

    n = a["turn_count"]
    if n <= 3:
        score += 10
        reasons.append(f"+10: Concise session ({n} turns)")
    elif n > 15:
        score -= 10
        reasons.append(f"-10: Long session ({n} turns)")

    total_tools = sum(a["tools"].values()) + sum(a["mcp_tools"].values())
    if total_tools > 0:
        score += 10
        reasons.append(f"+10: Active tool usage ({total_tools} deliberate calls)")
    if total_tools > 20:
        score += 5
        reasons.append(f"+5: Heavy tool usage ({total_tools} calls)")

    if a["mcp_tools"]:
        score += 15
        reasons.append(f"+15: MCP server integration ({len(a['mcp_tools'])} tool types)")

    if a["total_input"] > 0:
        ratio = a["total_output"] / a["total_input"]
        if ratio < 0.001:
            score -= 10
            reasons.append(f"-10: Very low output/input ratio ({ratio:.5f})")
        elif ratio > 0.01:
            score += 5
            reasons.append(f"+5: Good output/input ratio ({ratio:.4f})")

    all_models = set(a["req_models"].keys()) | set(a["resp_models"].keys())
    if len(all_models) > 1:
        score += 5
        reasons.append(f"+5: Multi-model usage ({len(all_models)} models)")

    if a["inference_input"] > a["total_input"] * 0.3:
        score -= 5
        reasons.append(f"-5: High inference routing overhead ({fmt(a['inference_input'])} tokens)")

    return max(0, min(100, score)), reasons


def fmt(n):
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def generate_report(records):
    lines = []
    w = lines.append

    sessions = defaultdict(list)
    orphans = [r for r in records if r["sid"] is None]
    for r in records:
        if r["sid"]:
            sessions[r["sid"]].append(r)

    analyses = []
    for sid, label in [
        (DICE_SID, "Dice Roller Service (Azure SDK MCP)"),
        (THIS_SID, "OTel Analysis Session (Current)"),
    ]:
        if sid in sessions:
            analyses.append(analyze_session(records, sid, label))

    # ═══════════════════ HEADER ═══════════════════
    w("# OTel GenAI Session Analysis Report")
    w("")
    w(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    w(f"**Trace File:** `{TRACE_FILE}`")
    w(f"**Total Records:** {len(records):,}")
    w(f"**Sessions Found:** {len(sessions)}")
    w(f"**Orphan Records:** {len(orphans)}")
    w("")

    # ═══════════════════ EXECUTIVE SUMMARY ═══════════════════
    w("## Executive Summary")
    w("")
    w("This report analyzes OpenTelemetry trace data captured from GitHub Copilot Chat")
    w("(VS Code Insiders) using the GenAI instrumentation from")
    w("[PR #3917](https://github.com/microsoft/vscode-copilot-chat/pull/3917).")
    w("Two sessions were captured:")
    w("")
    w("1. **Dice Roller Service** — A TypeSpec-driven SDK generation session that exercised")
    w("   the built-in `azure-sdk-mcp` server for code generation and spec validation.")
    w("2. **OTel Analysis Session** — The current session focused on building analysis")
    w("   tooling and understanding the trace format.")
    w("")

    # ═══════════════════ COMPARISON ═══════════════════
    w("## Session Comparison")
    w("")
    headers = [a["label"].split("(")[0].strip() for a in analyses]
    w("| Metric | " + " | ".join(headers) + " |")
    w("|--------|" + "|".join("--------|" for _ in analyses))

    rows = [
        ("Turns", [str(a["turn_count"]) for a in analyses]),
        ("Total trace records", [str(a["total_records"]) for a in analyses]),
        ("Tool call events", [str(a["tool_event_count"]) for a in analyses]),
        ("Inference detail events", [str(a["inference_event_count"]) for a in analyses]),
        ("Primary input tokens", [fmt(a["total_input"]) for a in analyses]),
        ("Primary output tokens", [fmt(a["total_output"]) for a in analyses]),
        ("Inference routing tokens", [fmt(a["inference_input"]) for a in analyses]),
        ("Deliberate tool types", [str(len(a["tools"]) + len(a["mcp_tools"])) for a in analyses]),
        ("MCP tool types", [str(len(a["mcp_tools"])) for a in analyses]),
        ("Auto tool calls", [str(a["auto_tool_count"]) for a in analyses]),
    ]
    for label, vals in rows:
        w(f"| {label} | " + " | ".join(vals) + " |")
    w("")

    # ═══════════════════ SCORES ═══════════════════
    w("## Effectiveness Scores")
    w("")
    for a in analyses:
        score, reasons = score_session(a)
        w(f"### {a['label']} — **{score}/100**")
        w("")
        for r in reasons:
            w(f"- {r}")
        w("")

    # ═══════════════════ DETAILED SESSIONS ═══════════════════
    for a in analyses:
        w("---")
        w(f"## {a['label']}")
        w("")
        w(f"**Session ID:** `{a['sid']}`")
        w("")

        # Models
        w("### Models Used")
        w("")
        w("| Model (requested) | Inference Calls |")
        w("|-------------------|----------------|")
        for m, c in a["req_models"].items():
            w(f"| `{m}` | {c} |")
        w("")
        if a["resp_models"]:
            w("| Model (responded) | Inference Calls |")
            w("|-------------------|----------------|")
            for m, c in a["resp_models"].items():
                w(f"| `{m}` | {c} |")
            w("")

        # Tools
        w("### Tool Usage")
        w("")
        if a["tools"] or a["mcp_tools"]:
            w("| Tool | Type | Calls |")
            w("|------|------|-------|")
            for t, c in a["tools"].items():
                w(f"| `{t}` | Built-in | {c} |")
            for t, c in a["mcp_tools"].items():
                short = t.replace("mcp_azure-sdk-mcp_", "")
                w(f"| `{short}` | MCP (`azure-sdk-mcp`) | {c} |")
            w("")
            if a["auto_tool_count"]:
                w(f"> **Note:** {a['auto_tool_count']} automatic `manage_todo_list` calls excluded from the table above.")
                w("")
        else:
            w("No deliberate tool calls recorded in this session.")
            w("")

        # Token budget
        w("### Token Budget")
        w("")
        grand_in = a["total_input"] + a["inference_input"]
        grand_out = a["total_output"] + a["inference_output"]
        grand = grand_in + grand_out
        w("| Category | Input | Output | % of Total |")
        w("|----------|-------|--------|-----------|")
        p_pct = (a["total_input"] + a["total_output"]) * 100 // max(grand, 1)
        i_pct = (a["inference_input"] + a["inference_output"]) * 100 // max(grand, 1)
        w(f"| Primary agent turns | {fmt(a['total_input'])} | {fmt(a['total_output'])} | {p_pct}% |")
        w(f"| Inference routing (gpt-4o-mini) | {fmt(a['inference_input'])} | {fmt(a['inference_output'])} | {i_pct}% |")
        w(f"| **Grand Total** | **{fmt(grand_in)}** | **{fmt(grand_out)}** | **100%** |")
        w("")

        if a["total_input"] > 0:
            ratio = a["total_output"] / a["total_input"]
            if ratio < 0.005:
                w(f"> **Output/Input ratio:** {ratio:.5f} — Low ratio indicates large context windows re-sent each turn (expected in agent-mode).")
            else:
                w(f"> **Output/Input ratio:** {ratio:.4f}")
            w("")

        # Per-turn breakdown
        w("### Per-Turn Breakdown")
        w("")
        w("| Turn | Input Tokens | Output Tokens | Deliberate Tools |")
        w("|------|-------------|--------------|-----------------|")
        for t in a["turns"]:
            tool_str = ", ".join(f"`{x}`" for x in t["tools"]) if t["tools"] else "—"
            auto_note = f" (+{len(t['auto_tools'])} auto)" if t["auto_tools"] else ""
            w(f"| {t['index']} | {fmt(t['input_tok'])} | {fmt(t['output_tok'])} | {tool_str}{auto_note} |")
        w("")

        # Token growth chart
        if a["turns"]:
            w("### Input Token Growth Per Turn")
            w("")
            w("```")
            max_tok = max(t["input_tok"] for t in a["turns"]) if a["turns"] else 1
            for t in a["turns"]:
                bar_len = int(t["input_tok"] / max(max_tok, 1) * 50)
                bar = "█" * bar_len
                markers = []
                if t["tools"]:
                    markers.extend(t["tools"])
                suffix = (" ← " + ", ".join(markers)) if markers else ""
                w(f"  Turn {str(t['index']).rjust(2)} | {bar} {fmt(t['input_tok'])}{suffix}")
            w("```")
            w("")

    # ═══════════════════ MCP ANALYSIS ═══════════════════
    w("---")
    w("## Azure SDK MCP Server Analysis")
    w("")
    dice = next((a for a in analyses if a["sid"] == DICE_SID), None)
    if dice and dice["mcp_tools"]:
        w("The **Dice Roller Service** session exercised the built-in `azure-sdk-mcp` server,")
        w("which ships with VS Code and provides Azure SDK development tools.")
        w("")
        w("### MCP Tools Invoked")
        w("")
        w("| Tool | Full Trace Name | Turn |")
        w("|------|----------------|------|")
        for t in dice["turns"]:
            for tool in t["tools"]:
                if tool.startswith("mcp_"):
                    short = tool.replace("mcp_azure-sdk-mcp_", "")
                    w(f"| `{short}` | `{tool}` | {t['index']} |")
        w("")

        w("### Observations")
        w("")
        w("1. **Tool naming convention:** MCP tools appear in traces as `mcp_<server-name>_<tool-name>`.")
        w("   For the Azure SDK MCP server: `mcp_azure-sdk-mcp_azsdk_*`.")
        w("")
        w("2. **TypeSpec validation** (`azsdk_run_typespec_validation`) was invoked at Turn 4,")
        w("   validating the TypeSpec definition before code generation.")
        w("")
        w("3. **Code generation** (`azsdk_package_generate_code`) was invoked at Turn 6,")
        w("   generating SDK code from the validated TypeSpec definition.")
        w("")
        w("4. **Workflow pattern:** The agent followed a logical sequence:")
        w("   create files (Turns 1–2) → validate spec (Turn 4) → generate code (Turn 6) → run terminal (Turn 8).")
        w("")
        w("5. **Token cost:** MCP tool turns consumed comparable tokens to non-MCP turns (~82–83K each),")
        w("   suggesting the MCP tool results don't dramatically inflate context size.")
        w("")
    else:
        w("No MCP tool usage detected in analyzed sessions.")
        w("")

    # ═══════════════════ TRACE FORMAT ═══════════════════
    w("---")
    w("## Trace Format Reference")
    w("")
    w("### Event Types")
    w("")
    all_events = Counter()
    for r in records:
        ev = r["event"] if r["event"] else "<no event>"
        all_events[ev] += 1
    w("| Event | Count | Description |")
    w("|-------|-------|-------------|")
    event_desc = {
        "copilot_chat.agent.turn": "One complete agent turn (prompt → response)",
        "copilot_chat.tool.call": "A tool invocation by the agent",
        "copilot_chat.session.start": "New chat session initiated",
        "gen_ai.client.inference.operation.details": "LLM inference call (routing/classification)",
        "<no event>": "Record without event.name (context/metadata)",
    }
    for ev, c in all_events.most_common():
        desc = event_desc.get(ev, "")
        w(f"| `{ev}` | {c} | {desc} |")
    w("")

    w("### File Format Notes")
    w("")
    w("The file exporter (`github.copilot.chat.otel.outfile`) produces the **OTel JS SDK internal format**,")
    w("not standard OTLP JSON. Key structural differences:")
    w("")
    w("| Aspect | OTLP JSON (expected) | Actual Format |")
    w("|--------|---------------------|---------------|")
    w("| Top-level | `resourceSpans[]` hierarchy | Flat JSONL (one record per line) |")
    w("| Session ID | `resource.attributes[].key/value` | `resource._rawAttributes` (array of `[key, value]` pairs) |")
    w("| Attributes | Nested `{key, value: {stringValue}}` | Flat dictionary `{key: value}` |")
    w("| Event body | Span events array | `_body` field on the record |")
    w("| Timestamps | `timeUnixNano` string | `hrTime` array `[seconds, nanoseconds]` |")
    w("")

    w("### Key Attributes")
    w("")
    w("| Attribute | Location | Description |")
    w("|-----------|----------|-------------|")
    w("| `session.id` | `resource._rawAttributes` | Chat session identifier |")
    w("| `turn.index` | `attributes` | Turn number within session (0-based) |")
    w("| `event.name` | `attributes` | Event type discriminator |")
    w("| `gen_ai.tool.name` | `attributes` | Tool name for tool call events |")
    w("| `gen_ai.usage.input_tokens` | `attributes` | Input token count |")
    w("| `gen_ai.usage.output_tokens` | `attributes` | Output token count |")
    w("| `gen_ai.request.model` | `attributes` | Requested model name |")
    w("| `gen_ai.response.model` | `attributes` | Actual model that responded |")
    w("| `gen_ai.agent.name` | `attributes` | Agent name (if any) |")
    w("| `tool_call_count` | `attributes` | Number of tool calls in a turn |")
    w("")

    # ═══════════════════ KEY FINDINGS ═══════════════════
    w("---")
    w("## Key Findings")
    w("")

    w("### 1. Trace Structure Is Flat, Not Hierarchical")
    w("")
    w("Unlike typical OpenTelemetry span hierarchies, the file export produces flat log records.")
    w("Tool calls are separate events without `turn.index` — they must be mapped to turns by")
    w("their position in the timestamp-ordered stream (tool calls appear between consecutive")
    w("`copilot_chat.agent.turn` events).")
    w("")

    w("### 2. Inference Routing Overhead")
    w("")
    w("Each turn generates multiple `gen_ai.client.inference.operation.details` events,")
    w("primarily using `gpt-4o-mini` for lightweight routing and classification. These")
    w("consume relatively few tokens compared to the primary agent model.")
    w("")
    for a in analyses:
        pct = a["inference_input"] * 100 // max(a["total_input"] + a["inference_input"], 1)
        w(f"- **{a['label'].split('(')[0].strip()}:** Inference routing = {pct}% of total input tokens")
    w("")

    w("### 3. Context Window Growth")
    w("")
    w("Input tokens grow incrementally with each turn as conversation history accumulates.")
    if dice:
        first = dice["turns"][0]["input_tok"] if dice["turns"] else 0
        last = dice["turns"][-1]["input_tok"] if dice["turns"] else 0
        growth = last - first
        pct = growth * 100 // max(first, 1)
        w(f"In the Dice Roller session, context grew from {fmt(first)} to {fmt(last)} tokens")
        w(f"({fmt(growth)} increase, {pct}% growth over {len(dice['turns'])} turns).")
    w("")

    w("### 4. Automatic Tool Calls")
    w("")
    w("`manage_todo_list` is invoked automatically at the beginning of most agent turns.")
    w("This is not a user-initiated tool call and should be excluded when measuring")
    w("deliberate tool usage effectiveness.")
    w("")
    for a in analyses:
        total = a["auto_tool_count"] + sum(a["tools"].values()) + sum(a["mcp_tools"].values())
        if total > 0:
            w(f"- **{a['label'].split('(')[0].strip()}:** {a['auto_tool_count']}/{total} tool calls were automatic ({a['auto_tool_count']*100//total}%)")
    w("")

    w("### 5. MCP Server Integration Works End-to-End")
    w("")
    w("The `azure-sdk-mcp` server was successfully discovered and invoked during the")
    w("Dice Roller session. Both `azsdk_run_typespec_validation` and")
    w("`azsdk_package_generate_code` executed as part of a coherent multi-step workflow.")
    w("MCP tool calls appear in traces identically to built-in tools, making them easy to")
    w("track and analyze.")
    w("")

    # ═══════════════════ METHODOLOGY ═══════════════════
    w("---")
    w("## Methodology")
    w("")
    w("### Data Collection")
    w("")
    w("| Setting | Value |")
    w("|---------|-------|")
    w("| Extension | GitHub Copilot Chat (VS Code Insiders) |")
    w("| OTel PR | [#3917](https://github.com/microsoft/vscode-copilot-chat/pull/3917) |")
    w("| Export method | `github.copilot.chat.otel.outfile` |")
    w("| Content capture | `captureContent: true` |")
    w("| Trace file | `otel-traces.jsonl` |")
    w("")

    w("### Analysis Pipeline")
    w("")
    w("1. Parse JSONL records from trace file")
    w("2. Extract `session.id` from `resource._rawAttributes`")
    w("3. Group records by session")
    w("4. Sort records within each session by `hrTime`")
    w("5. Map tool calls to turns by timestamp ordering")
    w("6. Compute per-turn and per-session metrics")
    w("7. Score effectiveness using weighted heuristics")
    w("")

    w("### Scoring Heuristics (0-100 scale)")
    w("")
    w("| Factor | Points | Condition |")
    w("|--------|--------|-----------|")
    w("| Baseline | 50 | Starting score |")
    w("| Concise session | +10 | <= 3 turns |")
    w("| Long session | -10 | > 15 turns |")
    w("| Active tool usage | +10 | > 0 deliberate tool calls |")
    w("| Heavy tool usage | +5 | > 20 deliberate tool calls |")
    w("| MCP integration | +15 | Any MCP tools used |")
    w("| Low token efficiency | -10 | output/input < 0.001 |")
    w("| Good token efficiency | +5 | output/input > 0.01 |")
    w("| Multi-model | +5 | > 1 model used |")
    w("| High routing overhead | -5 | Inference routing > 30% of total |")
    w("")

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Report written to {REPORT_FILE} ({len(lines)} lines)")


if __name__ == "__main__":
    records = load_records()
    generate_report(records)
