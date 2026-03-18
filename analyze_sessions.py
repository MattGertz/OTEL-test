"""
OTel Session Effectiveness Analyzer

Reads JSON-lines OTel export from Copilot Chat and computes
effectiveness metrics for chat sessions.

Setup:
  1. In VS Code settings, set:
       "github.copilot.chat.otel.outfile": "C:/Users/mattge/source/repos/scratch/otel-traces.jsonl"
       "github.copilot.chat.otel.captureContent": true
  2. Reload VS Code, run chat sessions, then:
       py analyze_sessions.py otel-traces.jsonl
"""

import json
import sys
from collections import defaultdict
from pathlib import Path


def load_spans(filepath):
    """Load OTLP JSON-lines file into a flat list of spans."""
    spans = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            # OTLP JSON export nests spans under resourceSpans
            for rs in record.get("resourceSpans", [record]):
                for ss in rs.get("scopeSpans", [rs]):
                    for span in ss.get("spans", []):
                        spans.append(span)
    return spans


def attrs_dict(span):
    """Convert span attributes list to a flat dict."""
    result = {}
    for attr in span.get("attributes", []):
        key = attr.get("key", "")
        val = attr.get("value", {})
        # OTel attribute values are typed: stringValue, intValue, etc.
        for v in val.values():
            result[key] = v
            break
    return result


# Sidecar agent names — these are auto-generated LLM calls, not user work
SIDECAR_AGENTS = {"title", "promptCategorization", "copilotLanguageModelWrapper",
                  "progressMessages", "debugCommandIdentifier"}

# Tool calls that fire automatically every invocation (not user-driven)
AUTO_TOOLS = {"manage_todo_list"}


def is_sidecar_span(span):
    """Return True if this span is a sidecar (title/categorization/summary)."""
    a = attrs_dict(span)
    agent = a.get("gen_ai.agent.name", "")
    label = a.get("copilot_chat.debug_log_label", "")
    return agent in SIDECAR_AGENTS or label in SIDECAR_AGENTS


def is_auto_tool(span):
    """Return True if this is an automatic tool call (not user-initiated)."""
    a = attrs_dict(span)
    tool = a.get("gen_ai.tool.name", "")
    return tool in AUTO_TOOLS


def filter_agent_spans(spans):
    """Remove sidecar traces — keep only invoke_agent trees and their children."""
    # A span is part of an agent trace if it has a parent within an invoke_agent root,
    # or if the trace contains an invoke_agent root span.
    # Simple heuristic: keep spans whose trace has an invoke_agent root.
    agent_trace_ids = set()
    for span in spans:
        name = span.get("name", "")
        if name.startswith("invoke_agent"):
            tid = span.get("traceId", "")
            if tid:
                agent_trace_ids.add(tid)
    return [s for s in spans if s.get("traceId", "") in agent_trace_ids]


def group_by_session(spans):
    """Group spans by chat session ID, excluding sidecar traces."""
    agent_spans = filter_agent_spans(spans)
    sessions = defaultdict(list)
    for span in agent_spans:
        a = attrs_dict(span)
        session_id = (a.get("copilot_chat.chat_session_id")
                      or a.get("copilot_chat.session_id")
                      or a.get("copilot_chat.parent_chat_session_id")
                      or "unknown")
        sessions[session_id].append(span)
    return dict(sessions)


def duration_ms(span):
    """Compute span duration in milliseconds from start/end timestamps."""
    start = span.get("startTimeUnixNano", 0)
    end = span.get("endTimeUnixNano", 0)
    if isinstance(start, str):
        start = int(start)
    if isinstance(end, str):
        end = int(end)
    return (end - start) / 1_000_000


# ---------------------------------------------------------------------------
# Effectiveness metrics
# ---------------------------------------------------------------------------

def metric_turn_count(session_spans):
    """How many agent turns in the session. High counts may indicate
    the agent is struggling or the user prompt was ambiguous."""
    turns = set()
    for span in session_spans:
        a = attrs_dict(span)
        idx = a.get("copilot_chat.turn.index")
        if idx is not None:
            turns.add(idx)
    return len(turns) if turns else 1


def metric_tool_calls(session_spans):
    """Total tool calls and unique tools used (excluding auto tools)."""
    calls = []
    unique_tools = set()
    auto_calls = []
    for span in session_spans:
        a = attrs_dict(span)
        tool = a.get("gen_ai.tool.name")
        if tool:
            if tool in AUTO_TOOLS:
                auto_calls.append(tool)
            else:
                calls.append(tool)
                unique_tools.add(tool)
    return len(calls), unique_tools, len(auto_calls)


def metric_tool_repetition(session_spans):
    """Detect repeated calls to the same tool — possible thrashing.
    Returns {tool_name: call_count} for tools called more than once.
    Excludes auto tools (manage_todo_list etc.)."""
    counts = defaultdict(int)
    for span in session_spans:
        a = attrs_dict(span)
        tool = a.get("gen_ai.tool.name")
        if tool and tool not in AUTO_TOOLS:
            counts[tool] += 1
    return {t: c for t, c in counts.items() if c > 1}


def metric_token_usage(session_spans):
    """Aggregate token usage across the session."""
    input_tokens = 0
    output_tokens = 0
    reasoning_tokens = 0
    cache_read = 0
    for span in session_spans:
        a = attrs_dict(span)
        val = a.get("gen_ai.usage.input_tokens")
        if val is not None:
            input_tokens += int(val)
        val = a.get("gen_ai.usage.output_tokens")
        if val is not None:
            output_tokens += int(val)
        val = a.get("gen_ai.usage.reasoning_tokens")
        if val is not None:
            reasoning_tokens += int(val)
        val = a.get("gen_ai.usage.cache_read.input_tokens")
        if val is not None:
            cache_read += int(val)
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "reasoning_tokens": reasoning_tokens,
        "cache_read_tokens": cache_read,
        "output_to_input_ratio": round(output_tokens / max(input_tokens, 1), 3),
    }


def metric_total_duration(session_spans):
    """Wall-clock duration of the session (first span start to last span end)."""
    starts = []
    ends = []
    for span in session_spans:
        s = span.get("startTimeUnixNano", 0)
        e = span.get("endTimeUnixNano", 0)
        if isinstance(s, str):
            s = int(s)
        if isinstance(e, str):
            e = int(e)
        if s:
            starts.append(s)
        if e:
            ends.append(e)
    if not starts or not ends:
        return 0
    return (max(ends) - min(starts)) / 1_000_000_000  # seconds


def metric_models_used(session_spans):
    """Which models were invoked. Multiple models may indicate escalation."""
    models = set()
    for span in session_spans:
        a = attrs_dict(span)
        m = a.get("gen_ai.response.model") or a.get("gen_ai.request.model")
        if m:
            models.add(m)
    return models


def metric_cancel_rate(session_spans):
    """Was the session/turn canceled by the user?"""
    for span in session_spans:
        a = attrs_dict(span)
        if a.get("copilot_chat.canceled"):
            return True
    return False


def metric_time_to_first_token(session_spans):
    """Average time-to-first-token across LLM calls in the session.
    Excludes sidecar spans."""
    ttfts = []
    for span in session_spans:
        if is_sidecar_span(span):
            continue
        a = attrs_dict(span)
        ttft = a.get("copilot_chat.time_to_first_token")
        if ttft is not None:
            ttfts.append(float(ttft))
    return round(sum(ttfts) / len(ttfts), 1) if ttfts else None


def metric_mcp_tool_usage(session_spans):
    """Isolate MCP tool calls from built-in tools.
    MCP tools typically have a server prefix like 'mcp_servername_toolname'.
    Excludes auto tools."""
    mcp_calls = []
    builtin_calls = []
    for span in session_spans:
        a = attrs_dict(span)
        tool = a.get("gen_ai.tool.name")
        if not tool or tool in AUTO_TOOLS:
            continue
        if tool.startswith("mcp_"):
            mcp_calls.append(tool)
        else:
            builtin_calls.append(tool)
    return {"mcp_calls": mcp_calls, "builtin_calls": builtin_calls}


# ---------------------------------------------------------------------------
# Effectiveness scoring (heuristic)
# ---------------------------------------------------------------------------

def score_session(session_spans):
    """Compute a heuristic effectiveness score (0-100) for a session.

    Signals that suggest an EFFECTIVE session:
      - Low turn count (got the answer quickly)
      - Moderate tool calls (not zero, not excessive)
      - Not canceled
      - Reasonable output/input token ratio

    Signals that suggest an INEFFECTIVE session:
      - Many turns (thrashing)
      - High tool repetition
      - User canceled
      - Very high token usage with little output
    """
    score = 100.0
    turns = metric_turn_count(session_spans)
    total_tool_calls, _, _ = metric_tool_calls(session_spans)
    repetitions = metric_tool_repetition(session_spans)
    tokens = metric_token_usage(session_spans)
    canceled = metric_cancel_rate(session_spans)

    # Penalize high turn count (>3 turns starts being expensive)
    if turns > 5:
        score -= min(30, (turns - 5) * 5)
    elif turns > 3:
        score -= (turns - 3) * 3

    # Penalize excessive tool calls per turn
    calls_per_turn = total_tool_calls / max(turns, 1)
    if calls_per_turn > 10:
        score -= min(20, (calls_per_turn - 10) * 2)

    # Penalize tool thrashing (same tool called 3+ times)
    thrashing_tools = sum(1 for c in repetitions.values() if c >= 3)
    score -= thrashing_tools * 10

    # Penalize cancellation heavily
    if canceled:
        score -= 25

    # Penalize very low output ratio (lots of input, very little output)
    if tokens["input_tokens"] > 0 and tokens["output_to_input_ratio"] < 0.02:
        score -= 15

    return max(0, min(100, round(score)))


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def analyze(filepath):
    spans = load_spans(filepath)
    if not spans:
        print(f"No spans found in {filepath}")
        return

    agent_spans = filter_agent_spans(spans)
    sidecar_count = len(spans) - len(agent_spans)
    sessions = group_by_session(spans)
    print(f"Loaded {len(spans)} spans ({len(agent_spans)} agent, {sidecar_count} sidecar)")
    print(f"Sessions: {len(sessions)}")
    print(f"Filtered: sidecar traces (title/categorization/summary), auto tools (manage_todo_list)")
    print("=" * 80)

    for session_id, session_spans in sessions.items():
        turns = metric_turn_count(session_spans)
        total_calls, unique_tools, auto_tool_count = metric_tool_calls(session_spans)
        repetitions = metric_tool_repetition(session_spans)
        tokens = metric_token_usage(session_spans)
        duration = metric_total_duration(session_spans)
        models = metric_models_used(session_spans)
        canceled = metric_cancel_rate(session_spans)
        ttft = metric_time_to_first_token(session_spans)
        mcp = metric_mcp_tool_usage(session_spans)
        score = score_session(session_spans)

        print(f"\nSession: {session_id}")
        print(f"  Effectiveness Score: {score}/100")
        print(f"  Duration:            {duration:.1f}s")
        print(f"  Turns:               {turns}")
        print(f"  Canceled:            {canceled}")
        print(f"  Models:              {', '.join(models) if models else 'N/A'}")
        if ttft is not None:
            print(f"  Avg TTFT:            {ttft}ms")

        print(f"  Tool Calls:          {total_calls} user-driven, {auto_tool_count} auto")
        if unique_tools:
            print(f"    Tools used:        {', '.join(sorted(unique_tools))}")
        if repetitions:
            print(f"    Repeated (thrash): {dict(repetitions)}")
        if mcp["mcp_calls"]:
            print(f"    MCP calls:         {len(mcp['mcp_calls'])} ({', '.join(mcp['mcp_calls'])})")

        print(f"  Tokens:")
        print(f"    Input:             {tokens['input_tokens']:,}")
        print(f"    Output:            {tokens['output_tokens']:,}")
        print(f"    Reasoning:         {tokens['reasoning_tokens']:,}")
        print(f"    Cache read:        {tokens['cache_read_tokens']:,}")
        print(f"    Output/Input:      {tokens['output_to_input_ratio']}")

    print("\n" + "=" * 80)

    # Summary across all sessions
    all_scores = [score_session(s) for s in sessions.values()]
    print(f"\nAggregate ({len(sessions)} sessions):")
    print(f"  Avg effectiveness:   {sum(all_scores) / len(all_scores):.0f}/100")
    print(f"  Min:                 {min(all_scores)}/100")
    print(f"  Max:                 {max(all_scores)}/100")

    # MCP tool effectiveness summary
    all_mcp = []
    all_builtin = []
    for session_spans in sessions.values():
        m = metric_mcp_tool_usage(session_spans)
        all_mcp.extend(m["mcp_calls"])
        all_builtin.extend(m["builtin_calls"])
    if all_mcp:
        mcp_counts = defaultdict(int)
        for t in all_mcp:
            mcp_counts[t] += 1
        print(f"\n  MCP Tool Usage:")
        for tool, count in sorted(mcp_counts.items(), key=lambda x: -x[1]):
            print(f"    {tool}: {count} calls")
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: py analyze_sessions.py <otel-traces.jsonl>")
        sys.exit(1)
    analyze(sys.argv[1])
