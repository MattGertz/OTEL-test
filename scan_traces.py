"""Quick scan of otel-traces.jsonl to list sessions and find the dice roller."""
import json
from collections import defaultdict

sessions = defaultdict(lambda: {
    "count": 0,
    "tools": set(),
    "models": set(),
    "events": [],
    "labels": set(),
    "input_tokens": 0,
    "output_tokens": 0,
    "ttfts": [],
    "bodies": [],
    "agent_names": set(),
    "turn_indices": set(),
})

with open("otel-traces.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        attrs = rec.get("attributes", {})
        body = str(rec.get("_body", ""))

        # Session ID is in the resource attributes
        res = rec.get("resource", {})
        res_attrs = dict(res.get("_rawAttributes", []))
        sid = res_attrs.get("session.id", attrs.get("session.id", "unknown"))

        event = attrs.get("event.name", "")
        tool = attrs.get("gen_ai.tool.name", "")
        model = attrs.get("gen_ai.request.model", "")
        agent = attrs.get("gen_ai.agent.name", "")
        op = attrs.get("gen_ai.operation.name", "")
        input_tok = attrs.get("gen_ai.usage.input_tokens", 0)
        output_tok = attrs.get("gen_ai.usage.output_tokens", 0)
        turn_idx = attrs.get("turn.index", None)
        success = attrs.get("success", None)
        duration = attrs.get("duration_ms", None)
        tool_calls = attrs.get("tool_call_count", 0)

        s = sessions[sid]
        s["count"] += 1
        if tool:
            s["tools"].add(tool)
        if model:
            s["models"].add(model)
        if event:
            s["events"].append(event)
        if agent:
            s["agent_names"].add(agent)
        if input_tok:
            s["input_tokens"] += int(input_tok)
        if output_tok:
            s["output_tokens"] += int(output_tok)
        if turn_idx is not None:
            s["turn_indices"].add(turn_idx)
        if body and body != "None":
            s["bodies"].append(body[:200])

total = sum(s["count"] for s in sessions.values())
print(f"Total records: {total}")
print(f"Sessions: {len(sessions)}")
print("=" * 80)

for sid, info in sorted(sessions.items(), key=lambda x: -x[1]["count"]):
    if sid == "unknown":
        continue
    print(f"\nSession: {sid}")
    print(f"  Records:       {info['count']}")
    print(f"  Turns:         {len(info['turn_indices']) if info['turn_indices'] else 'N/A'}")
    print(f"  Models:        {', '.join(sorted(info['models'])) if info['models'] else 'N/A'}")
    print(f"  Agents:        {', '.join(sorted(info['agent_names'])) if info['agent_names'] else 'none'}")
    print(f"  Tools:         {', '.join(sorted(info['tools'])) if info['tools'] else 'none'}")
    print(f"  Input tokens:  {info['input_tokens']:,}")
    print(f"  Output tokens: {info['output_tokens']:,}")
    events = [e for e in info["events"] if e]
    if events:
        from collections import Counter
        ec = Counter(events)
        print(f"  Events:        {dict(ec)}")
    bodies = [b for b in info["bodies"] if b and "GenAI" not in b and len(b) > 5]
    if bodies:
        print(f"  Sample bodies:")
        for b in bodies[:5]:
            print(f"    - {b}")

# Also show unknown/no-session records
if "unknown" in sessions:
    print(f"\n(Records with no session ID: {sessions['unknown']['count']})")
