"""Analyze the test session from the SQLite span database."""
import sqlite3
import json
from datetime import datetime, timezone, timedelta

DB_PATH = r"C:\Users\mattge\AppData\Roaming\Code - Insiders\User\globalStorage\github.copilot-chat\agent-traces.db"
PDT = timezone(timedelta(hours=-7))

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

def ms_to_pdt(ms):
    return datetime.fromtimestamp(ms/1000, tz=PDT).strftime("%I:%M:%S %p")

# Get all unique trace_ids with their time ranges and agent names
cur.execute("""
    SELECT trace_id, 
           MIN(start_time_ms) as first_start,
           MAX(end_time_ms) as last_end,
           COUNT(*) as span_count,
           GROUP_CONCAT(DISTINCT agent_name) as agents,
           GROUP_CONCAT(DISTINCT request_model) as models
    FROM spans 
    GROUP BY trace_id
    ORDER BY first_start
""")
traces = cur.fetchall()

print(f"Found {len(traces)} traces\n")
for t in traces:
    start_pdt = ms_to_pdt(t['first_start'])
    end_pdt = ms_to_pdt(t['last_end'])
    dur_s = (t['last_end'] - t['first_start']) / 1000
    print(f"Trace {t['trace_id'][:16]}...")
    print(f"  Time: {start_pdt} - {end_pdt} ({dur_s:.1f}s)")
    print(f"  Spans: {t['span_count']}")
    print(f"  Agents: {t['agents']}")
    print(f"  Models: {t['models']}")
    print()

# Find traces that started around 11:40 PDT (18:40 UTC = epoch ~1775587200000)
# 11:40 PDT = 18:40 UTC. Let's look for traces starting after 11:35 PDT
target_start = 1775586900000  # roughly 11:35 PDT
target_end = 1775588400000    # roughly 12:00 PDT

print(f"{'='*80}")
print(f"TRACES STARTING BETWEEN 11:35-12:00 PDT:")
cur.execute("""
    SELECT trace_id, MIN(start_time_ms) as first_start
    FROM spans 
    WHERE start_time_ms BETWEEN ? AND ?
    GROUP BY trace_id
    ORDER BY first_start
""", (target_start, target_end))
target_traces = cur.fetchall()

for tt in target_traces:
    tid = tt['trace_id']
    print(f"\n{'='*80}")
    print(f"TRACE: {tid}")
    print(f"Started: {ms_to_pdt(tt['first_start'])}")
    
    # Get all spans in this trace, ordered by start time
    cur.execute("""
        SELECT * FROM spans WHERE trace_id = ? ORDER BY start_time_ms
    """, (tid,))
    spans = cur.fetchall()
    
    print(f"Total spans: {len(spans)}\n")
    
    # Build hierarchy
    span_map = {s['span_id']: s for s in spans}
    
    def get_depth(span):
        depth = 0
        pid = span['parent_span_id']
        while pid and pid in span_map:
            depth += 1
            pid = span_map[pid]['parent_span_id']
        return depth
    
    for s in spans:
        depth = get_depth(s)
        indent = "  " * depth
        dur = (s['end_time_ms'] - s['start_time_ms']) / 1000
        time = ms_to_pdt(s['start_time_ms'])
        
        extra = ""
        if s['tool_name']:
            extra = f" [tool: {s['tool_name']}]"
        if s['input_tokens']:
            extra += f" [in={s['input_tokens']} out={s['output_tokens']}"
            if s['cached_tokens']:
                extra += f" cached={s['cached_tokens']}"
            extra += "]"
        if s['status_code'] and s['status_code'] != 0:
            extra += f" [STATUS={s['status_code']}: {s['status_message']}]"
        
        print(f"  {indent}[{time}] {s['name']} ({dur:.1f}s){extra}")
    
    # Get attributes for spans with content
    print(f"\n  CHECKING FOR CONTENT ATTRIBUTES:")
    cur.execute("""
        SELECT sa.span_id, sa.key, sa.value 
        FROM span_attributes sa
        JOIN spans s ON sa.span_id = s.span_id
        WHERE s.trace_id = ? 
          AND (sa.key LIKE '%content%' OR sa.key LIKE '%prompt%' 
               OR sa.key LIKE '%message%' OR sa.key LIKE '%input%'
               OR sa.key LIKE '%instruction%' OR sa.key LIKE '%text%')
        LIMIT 20
    """, (tid,))
    content_attrs = cur.fetchall()
    if content_attrs:
        for ca in content_attrs:
            val = ca['value']
            if len(val) > 200:
                val = val[:200] + "..."
            print(f"    {ca['span_id'][:12]} | {ca['key']}: {val}")
    else:
        print(f"    (none found)")
    
    # Get ALL unique attribute keys for this trace
    cur.execute("""
        SELECT DISTINCT sa.key
        FROM span_attributes sa
        JOIN spans s ON sa.span_id = s.span_id
        WHERE s.trace_id = ?
        ORDER BY sa.key
    """, (tid,))
    all_keys = [r['key'] for r in cur.fetchall()]
    print(f"\n  ALL ATTRIBUTE KEYS: {all_keys}")
    
    # Get span events for this trace
    cur.execute("""
        SELECT se.*
        FROM span_events se
        JOIN spans s ON se.span_id = s.span_id
        WHERE s.trace_id = ?
        ORDER BY se.timestamp_ms
    """, (tid,))
    events = cur.fetchall()
    if events:
        print(f"\n  SPAN EVENTS: {len(events)}")
        for ev in events:
            time = ms_to_pdt(ev['timestamp_ms'])
            attrs = ev['attributes'] or "{}"
            if len(attrs) > 200:
                attrs = attrs[:200] + "..."
            print(f"    [{time}] {ev['name']}: {attrs}")

conn.close()
