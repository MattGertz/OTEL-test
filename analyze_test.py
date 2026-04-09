"""Analyze otel-traces.jsonl: extract sessions, prompts, span hierarchy, tools, and grade."""
import json
import sys
from collections import defaultdict, Counter

TRACE_FILE = "otel-traces.jsonl"

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
            records.append({
                "raw": rec,
                "attrs": attrs,
                "res_attrs": res_attrs,
                "sid": res_attrs.get("session.id", attrs.get("session.id")),
                "event": attrs.get("event.name", ""),
                "tool": attrs.get("gen_ai.tool.name", ""),
                "model": attrs.get("gen_ai.request.model", ""),
                "resp_model": attrs.get("gen_ai.response.model", ""),
                "agent": attrs.get("gen_ai.agent.name", ""),
                "input_tok": int(attrs.get("gen_ai.usage.input_tokens", 0)),
                "output_tok": int(attrs.get("gen_ai.usage.output_tokens", 0)),
                "turn": attrs.get("turn.index"),
                "hrTime": rec.get("hrTime", [0, 0]),
                "body": rec.get("_body", ""),
                "span_name": attrs.get("name", rec.get("instrumentationScope", {}).get("name", "")),
            })
    return records


def extract_content(rec, key):
    """Try to extract content capture attribute."""
    val = rec["attrs"].get(key, "")
    if not val:
        return ""
    if isinstance(val, str):
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return val
    return val


records = load_records()
print(f"Total records: {len(records)}")

# Group by session
sessions = defaultdict(list)
orphans = []
for r in records:
    if r["sid"]:
        sessions[r["sid"]].append(r)
    else:
        orphans.append(r)

print(f"Sessions: {len(sessions)}")
print(f"Orphan records: {len(orphans)}")

for sid, recs in sorted(sessions.items(), key=lambda x: -len(x[1])):
    print(f"\n{'='*80}")
    print(f"Session: {sid}")
    print(f"Records: {len(recs)}")

    # Sort by time
    recs.sort(key=lambda r: r["hrTime"])

    # Categorize events
    events = Counter(r["event"] for r in recs if r["event"])
    print(f"Events: {dict(events.most_common())}")

    # Agents
    agents = Counter(r["agent"] for r in recs if r["agent"])
    print(f"Agents: {dict(agents)}")

    # Models
    models = Counter(r["model"] for r in recs if r["model"])
    print(f"Models requested: {dict(models)}")

    # Tools
    tools = Counter(r["tool"] for r in recs if r["tool"])
    print(f"Tools: {dict(tools.most_common())}")

    # Turn events
    turn_events = [r for r in recs if r["event"] == "copilot_chat.agent.turn"]
    print(f"Turns: {len(turn_events)}")
    total_in = sum(r["input_tok"] for r in turn_events)
    total_out = sum(r["output_tok"] for r in turn_events)
    print(f"Tokens (from turns): input={total_in:,} output={total_out:,}")

    # Tool calls mapped to turns
    tool_events = [r for r in recs if r["event"] == "copilot_chat.tool.call"]
    current_turn = -1
    tool_idx = 0
    turn_tool_map = defaultdict(list)
    for r in recs:
        if r["event"] == "copilot_chat.agent.turn":
            current_turn = r["turn"] if r["turn"] is not None else current_turn + 1
        elif r["event"] == "copilot_chat.tool.call":
            turn_tool_map[current_turn].append(r["tool"])

    print(f"\nPer-turn breakdown:")
    for r in turn_events:
        tidx = r["turn"] if r["turn"] is not None else "?"
        tools_in_turn = turn_tool_map.get(tidx, [])
        deliberate = [t for t in tools_in_turn if t != "manage_todo_list"]
        auto = [t for t in tools_in_turn if t == "manage_todo_list"]
        tool_str = ", ".join(deliberate) if deliberate else "—"
        auto_str = f" (+{len(auto)} auto)" if auto else ""
        print(f"  Turn {tidx}: in={r['input_tok']:,} out={r['output_tok']:,} | tools: {tool_str}{auto_str}")

    # --- EXTRACT USER PROMPT ---
    print(f"\n--- CONTENT CAPTURE ---")

    # Look for gen_ai.content.prompt, gen_ai.input.messages, or gen_ai.content.completion
    content_keys = [
        "gen_ai.content.prompt", "gen_ai.input.messages",
        "gen_ai.system_instructions", "gen_ai.content.completion",
        "gen_ai.output.messages", "gen_ai.tool.call.arguments",
        "gen_ai.tool.call.result",
    ]

    for r in recs:
        for key in content_keys:
            val = r["attrs"].get(key)
            if val:
                # Truncate for display
                val_str = str(val)
                if len(val_str) > 500:
                    val_str = val_str[:500] + "..."
                print(f"\n  [{r['event'] or 'span'}] {key}:")
                print(f"    {val_str}")
                break  # Only show first content key per record

    # Also check _body for anything useful
    print(f"\n--- BODY CONTENT (first 20 with body) ---")
    body_count = 0
    for r in recs:
        body = r["body"]
        if body and str(body) != "None" and str(body).strip():
            body_str = str(body)
            if len(body_str) > 300:
                body_str = body_str[:300] + "..."
            print(f"  [{r['event']}] {body_str}")
            body_count += 1
            if body_count >= 20:
                break

    # Errors
    errors = [r for r in recs if r["attrs"].get("error.type")]
    if errors:
        print(f"\n--- ERRORS ({len(errors)}) ---")
        for r in errors:
            print(f"  [{r['event']}] tool={r['tool']} error={r['attrs'].get('error.type')}")
