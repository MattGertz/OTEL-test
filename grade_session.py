"""Reconstruct and grade the test session from OTel traces.
Since captureContent isn't showing content attributes, we work with what we have:
event types, tool calls, models, timing, token counts, errors.
"""
import json
from datetime import datetime, timezone
from collections import defaultdict

TRACE_FILE = "otel-traces.jsonl"

records = []
with open(TRACE_FILE, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        records.append(json.loads(line))

print(f"Total records: {len(records)}")

# Split into sessions and orphans
sessions = defaultdict(list)
orphans = []
metrics = []

for rec in records:
    if not rec:  # empty dict
        orphans.append(rec)
        continue
    
    # Check if it's a metric record
    if "scopeMetrics" in rec:
        metrics.append(rec)
        continue
    
    raw = rec.get("resource", {}).get("_rawAttributes", [])
    sid = None
    for pair in raw:
        if pair[0] == "session.id":
            sid = pair[1]
            break
    
    if sid:
        sessions[sid].append(rec)
    else:
        orphans.append(rec)

print(f"\nSessions: {len(sessions)}")
print(f"Metric records: {len(metrics)}")
print(f"Orphan/empty records: {len(orphans)}")

# Analyze each session
for sid, recs in sessions.items():
    print(f"\n{'='*80}")
    print(f"SESSION: {sid}")
    print(f"Records: {len(recs)}")
    
    # Convert hrTime to readable timestamp
    def hr_to_ts(hr):
        if not hr:
            return None
        return hr[0] + hr[1] / 1e9
    
    def hr_to_str(hr):
        ts = hr_to_ts(hr)
        if not ts:
            return "?"
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%H:%M:%S.%f")[:-3]
    
    # Find time range
    times = [hr_to_ts(r.get("hrTime")) for r in recs if r.get("hrTime")]
    if times:
        times.sort()
        duration = times[-1] - times[0]
        print(f"Time range: {hr_to_str(recs[0].get('hrTime', []))} to {hr_to_str(recs[-1].get('hrTime', []))}")
        print(f"Duration: {duration:.1f}s ({duration/60:.1f}m)")
    
    # Categorize events
    events_by_type = defaultdict(list)
    for rec in recs:
        attrs = rec.get("attributes", {})
        ename = attrs.get("event.name", "unknown")
        events_by_type[ename].append(rec)
    
    print(f"\nEvent types:")
    for etype, evts in sorted(events_by_type.items(), key=lambda x: -len(x[1])):
        print(f"  {etype}: {len(evts)}")
    
    # Session starts
    starts = events_by_type.get("copilot_chat.session.start", [])
    for s in starts:
        a = s.get("attributes", {})
        print(f"\n  SESSION START:")
        print(f"    Agent: {a.get('gen_ai.agent.name', '?')}")
        print(f"    Model: {a.get('gen_ai.request.model', '?')}")
        print(f"    Session ID: {a.get('session.id', '?')}")
        print(f"    Time: {hr_to_str(s.get('hrTime', []))}")
    
    # Turns - build timeline
    turns = events_by_type.get("copilot_chat.agent.turn", [])
    turns.sort(key=lambda r: r.get("attributes", {}).get("turn.index", 0))
    print(f"\n  TURNS: {len(turns)}")
    for t in turns:
        a = t.get("attributes", {})
        print(f"    Turn {a.get('turn.index', '?')}:")
        print(f"      Tokens in: {a.get('gen_ai.usage.input_tokens', '?')}")
        print(f"      Tokens out: {a.get('gen_ai.usage.output_tokens', '?')}")
        print(f"      Tool calls: {a.get('tool_call_count', 0)}")
        print(f"      Time: {hr_to_str(t.get('hrTime', []))}")
    
    # Tool calls timeline
    tool_calls = events_by_type.get("copilot_chat.tool.call", [])
    tool_calls.sort(key=lambda r: hr_to_ts(r.get("hrTime")) or 0)
    print(f"\n  TOOL CALLS: {len(tool_calls)}")
    for tc in tool_calls:
        a = tc.get("attributes", {})
        name = a.get("gen_ai.tool.name", "?")
        dur = a.get("duration_ms", "?")
        success = a.get("success", "?")
        time = hr_to_str(tc.get("hrTime", []))
        status = "OK" if success else "FAIL"
        print(f"    [{time}] {name} ({dur}ms) [{status}]")
    
    # Inference details
    inferences = events_by_type.get("gen_ai.client.inference.operation.details", [])
    inferences.sort(key=lambda r: hr_to_ts(r.get("hrTime")) or 0)
    print(f"\n  INFERENCES: {len(inferences)}")
    total_in = 0
    total_out = 0
    models_used = set()
    for inf in inferences:
        a = inf.get("attributes", {})
        model = a.get("gen_ai.request.model", "?")
        resp_model = a.get("gen_ai.response.model", "?")
        tok_in = a.get("gen_ai.usage.input_tokens", 0)
        tok_out = a.get("gen_ai.usage.output_tokens", 0)
        finish = a.get("gen_ai.response.finish_reasons", [])
        time = hr_to_str(inf.get("hrTime", []))
        total_in += tok_in
        total_out += tok_out
        models_used.add(model)
        print(f"    [{time}] {model} -> {resp_model} | in={tok_in} out={tok_out} | finish={finish}")
    
    print(f"\n  Token totals: input={total_in:,} output={total_out:,}")
    print(f"  Models used: {models_used}")
    
    # Errors
    errors = events_by_type.get("copilot_chat.error", [])
    if errors:
        print(f"\n  ERRORS: {len(errors)}")
        for e in errors:
            a = e.get("attributes", {})
            print(f"    Error: {a}")
    
    # Session end
    ends = events_by_type.get("copilot_chat.session.end", [])
    for e in ends:
        a = e.get("attributes", {})
        print(f"\n  SESSION END:")
        for k, v in a.items():
            print(f"    {k}: {v}")
    
    # Any other attributes we might have missed - scan ALL attributes
    all_attr_keys = set()
    for rec in recs:
        for k in rec.get("attributes", {}).keys():
            all_attr_keys.add(k)
    print(f"\n  ALL ATTRIBUTE KEYS: {sorted(all_attr_keys)}")
    
    # Check for any content-related attributes
    content_keys = [k for k in all_attr_keys if any(w in k.lower() for w in ["content", "prompt", "message", "input", "output", "text", "body"])]
    if content_keys:
        print(f"  CONTENT-RELATED KEYS: {content_keys}")
    else:
        print(f"  NO CONTENT-RELATED ATTRIBUTE KEYS FOUND")

# Metric details
if metrics:
    print(f"\n{'='*80}")
    print(f"METRICS: {len(metrics)} records")
    for m in metrics[:3]:
        for sm in m.get("scopeMetrics", []):
            for metric in sm.get("metrics", []):
                desc = metric.get("descriptor", {})
                print(f"  Metric: {desc.get('name')} ({desc.get('type')})")
                dp = metric.get("dataPoints", [])
                if dp:
                    for d in dp[:2]:
                        val = d.get("value", {})
                        print(f"    Value: {val}")

# Build combined timeline for the larger session
print(f"\n{'='*80}")
print("COMBINED TIMELINE (all sessions)")
all_events = []
for sid, recs in sessions.items():
    for rec in recs:
        attrs = rec.get("attributes", {})
        ename = attrs.get("event.name", "unknown")
        ts = hr_to_ts(rec.get("hrTime"))
        if ts:
            all_events.append((ts, sid[-20:], ename, attrs))

all_events.sort(key=lambda x: x[0])
for ts, sid, ename, attrs in all_events:
    t = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%H:%M:%S.%f")[:-3]
    extra = ""
    if "gen_ai.tool.name" in attrs:
        extra = f" tool={attrs['gen_ai.tool.name']}"
        if not attrs.get("success", True):
            extra += " [FAIL]"
    elif "gen_ai.request.model" in attrs and ename == "gen_ai.client.inference.operation.details":
        extra = f" model={attrs['gen_ai.request.model']} in={attrs.get('gen_ai.usage.input_tokens',0)} out={attrs.get('gen_ai.usage.output_tokens',0)}"
    elif "turn.index" in attrs:
        extra = f" turn={attrs['turn.index']} tools={attrs.get('tool_call_count',0)}"
    elif "gen_ai.agent.name" in attrs:
        extra = f" agent={attrs['gen_ai.agent.name']}"
    print(f"  [{t}] ({sid}) {ename}{extra}")
