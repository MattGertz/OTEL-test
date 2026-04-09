"""Quick targeted check: which session is which, and is the test data complete?"""
import json
from datetime import datetime, timezone, timedelta

TRACE_FILE = "otel-traces.jsonl"
PDT = timezone(timedelta(hours=-7))

records = []
with open(TRACE_FILE, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            records.append(json.loads(line))

print(f"Total records: {len(records)}")

# Separate into categories
sessions = {}
orphans = []
metrics = []
for rec in records:
    if not rec:
        orphans.append(rec)
        continue
    if "scopeMetrics" in rec:
        metrics.append(rec)
        continue
    raw = rec.get("resource", {}).get("_rawAttributes", [])
    sid = None
    for pair in raw:
        if pair[0] == "session.id":
            sid = pair[1]
    if sid:
        sessions.setdefault(sid, []).append(rec)
    else:
        orphans.append(rec)

# For each session, show time range in PDT and key identifiers
print(f"\n{'='*60}")
for sid, recs in sessions.items():
    times = []
    for r in recs:
        hr = r.get("hrTime")
        if hr:
            times.append(hr[0] + hr[1]/1e9)
    if not times:
        continue
    times.sort()
    start_pdt = datetime.fromtimestamp(times[0], tz=PDT).strftime("%I:%M:%S %p PDT")
    end_pdt = datetime.fromtimestamp(times[-1], tz=PDT).strftime("%I:%M:%S %p PDT")
    
    # What models?
    models = set()
    tools = set()
    agents = set()
    has_turns = False
    for r in recs:
        a = r.get("attributes", {})
        if a.get("gen_ai.request.model"):
            models.add(a["gen_ai.request.model"])
        if a.get("gen_ai.tool.name"):
            tools.add(a["gen_ai.tool.name"])
        if a.get("gen_ai.agent.name"):
            agents.add(a["gen_ai.agent.name"])
        if a.get("event.name") == "copilot_chat.agent.turn":
            has_turns = True
    
    print(f"\nSession: {sid[:30]}...")
    print(f"  Time: {start_pdt} -> {end_pdt}")
    print(f"  Records: {len(recs)}")
    print(f"  Models: {models}")
    print(f"  Tools: {tools}")
    print(f"  Agents: {agents}")
    print(f"  Has turns: {has_turns}")

# Check orphans
print(f"\n{'='*60}")
print(f"Orphan records: {len(orphans)}")
non_empty = [o for o in orphans if o]
print(f"Non-empty orphans: {len(non_empty)}")
for o in non_empty[:3]:
    print(f"  Keys: {list(o.keys())}")
    if o.get("attributes"):
        print(f"  Attrs: {o['attributes']}")

# Check metric records for session info
print(f"\nMetric records: {len(metrics)}")
metric_sessions = set()
for m in metrics:
    raw = m.get("resource", {}).get("_rawAttributes", [])
    for pair in raw:
        if pair[0] == "session.id":
            metric_sessions.add(pair[1])
print(f"Metric session IDs: {metric_sessions}")

# NOW THE KEY QUESTION: Is session 2 (claude-opus) actually THIS window?
# Check if it uses the tools we've been using
print(f"\n{'='*60}")
print("IDENTITY CHECK:")
print("Session 2 tools (manage_todo_list, run_in_terminal, create_file, read_file)")
print("  -> These are exactly what THIS grading session has been using")
print("Session 1 tools (vscode_get_terminal_confirmation, vscode_get_confirmation)")  
print("  -> These are user-approval tools for an agent running in the OTHER window")
print()
print("Session 1 ONLY has gpt-4o-mini — no main model (Claude/GPT-4)")
print("This suggests Session 1 only captured BACKGROUND classification calls,")
print("NOT the main agent inference. The main test agent traces may be missing.")
