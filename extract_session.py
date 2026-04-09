"""Extract the user prompt and full session details from the test trace."""
import sqlite3
import json
from datetime import datetime, timezone, timedelta

DB_PATH = r"C:\Users\mattge\AppData\Roaming\Code - Insiders\User\globalStorage\github.copilot-chat\agent-traces.db"
PDT = timezone(timedelta(hours=-7))
TEST_TRACE = "104e62b47b580703e057ed16c6c1a0bb"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Get first chat span's input messages (contains the user prompt)
cur.execute("""
    SELECT s.span_id, s.name, s.start_time_ms, sa.key, sa.value
    FROM spans s
    JOIN span_attributes sa ON s.span_id = sa.span_id
    WHERE s.trace_id = ? AND sa.key = 'gen_ai.input.messages'
    ORDER BY s.start_time_ms
    LIMIT 1
""", (TEST_TRACE,))
first = cur.fetchone()

if first:
    messages = json.loads(first['value'])
    print("=" * 80)
    print("USER PROMPT (from first chat span):")
    print("=" * 80)
    for msg in messages:
        role = msg.get("role", "?")
        parts = msg.get("parts", [])
        for part in parts:
            ptype = part.get("type", "?")
            content = part.get("content", "")
            if role == "user" and ptype == "text":
                print(f"\n[USER MESSAGE]:")
                print(content)
            elif role == "system" and ptype == "text":
                # Just show first 200 chars of system
                if len(content) > 200:
                    print(f"\n[SYSTEM - {len(content)} chars]: {content[:200]}...")
                else:
                    print(f"\n[SYSTEM]: {content}")

# Now get ALL chat spans with output messages to trace the full conversation
print("\n" + "=" * 80)
print("FULL AGENT CONVERSATION FLOW:")
print("=" * 80)

cur.execute("""
    SELECT span_id, name, start_time_ms, end_time_ms, 
           input_tokens, output_tokens, cached_tokens,
           tool_name, status_code, status_message
    FROM spans 
    WHERE trace_id = ? 
    ORDER BY start_time_ms
""", (TEST_TRACE,))
all_spans = cur.fetchall()

def ms_to_pdt(ms):
    return datetime.fromtimestamp(ms/1000, tz=PDT).strftime("%I:%M:%S %p")

for span in all_spans:
    sid = span['span_id']
    name = span['name']
    
    if not name.startswith("chat "):
        continue
    
    time = ms_to_pdt(span['start_time_ms'])
    dur = (span['end_time_ms'] - span['start_time_ms']) / 1000
    
    # Get output messages
    cur.execute("""
        SELECT value FROM span_attributes 
        WHERE span_id = ? AND key = 'gen_ai.output.messages'
    """, (sid,))
    out_row = cur.fetchone()
    
    print(f"\n--- [{time}] {name} ({dur:.1f}s) in={span['input_tokens']} out={span['output_tokens']} ---")
    
    if out_row:
        messages = json.loads(out_row['value'])
        for msg in messages:
            role = msg.get("role", "?")
            parts = msg.get("parts", [])
            for part in parts:
                ptype = part.get("type", "?")
                if ptype == "text":
                    content = part.get("content", "")
                    if len(content) > 500:
                        print(f"  [{role}/text]: {content[:500]}...")
                    else:
                        print(f"  [{role}/text]: {content}")
                elif ptype == "tool_call":
                    tool_name = part.get("name", "?")
                    args = part.get("arguments", {})
                    args_str = json.dumps(args) if isinstance(args, dict) else str(args)
                    if len(args_str) > 300:
                        args_str = args_str[:300] + "..."
                    print(f"  [{role}/tool_call]: {tool_name}({args_str})")
                elif ptype == "server_tool_call":
                    stc = part.get("server_tool_call", {})
                    sname = part.get("name", stc.get("tool_name", "?"))
                    print(f"  [{role}/server_tool_call]: {sname}")
                elif ptype == "reasoning":
                    content = part.get("content", "")
                    if len(content) > 300:
                        print(f"  [{role}/reasoning]: {content[:300]}...")
                    else:
                        print(f"  [{role}/reasoning]: {content}")

# Summary stats
print("\n" + "=" * 80)
print("SUMMARY:")
print("=" * 80)

cur.execute("""
    SELECT COUNT(*) as total_spans,
           SUM(CASE WHEN name LIKE 'chat %' THEN 1 ELSE 0 END) as chat_spans,
           SUM(CASE WHEN name LIKE 'execute_tool%' THEN 1 ELSE 0 END) as tool_spans,
           SUM(input_tokens) as total_input,
           SUM(output_tokens) as total_output,
           SUM(cached_tokens) as total_cached,
           MIN(start_time_ms) as first_start,
           MAX(end_time_ms) as last_end
    FROM spans WHERE trace_id = ?
""", (TEST_TRACE,))
summary = cur.fetchone()
dur_min = (summary['last_end'] - summary['first_start']) / 1000 / 60
print(f"Total spans: {summary['total_spans']}")
print(f"Chat completions: {summary['chat_spans']}")
print(f"Tool executions: {summary['tool_spans']}")
print(f"Total tokens: input={summary['total_input']:,} output={summary['total_output']:,} cached={summary['total_cached']:,}")
print(f"Duration: {dur_min:.1f} minutes")

# Unique tools used
cur.execute("""
    SELECT DISTINCT tool_name FROM spans 
    WHERE trace_id = ? AND tool_name IS NOT NULL
    ORDER BY tool_name
""", (TEST_TRACE,))
tools = [r['tool_name'] for r in cur.fetchall()]
print(f"Tools used: {tools}")

# Error spans
cur.execute("""
    SELECT name, tool_name, status_code, status_message 
    FROM spans 
    WHERE trace_id = ? AND status_code != 0
""", (TEST_TRACE,))
errors = cur.fetchall()
if errors:
    print(f"\nErrors ({len(errors)}):")
    for e in errors:
        print(f"  {e['name']} (tool={e['tool_name']}) status={e['status_code']}: {e['status_message']}")

conn.close()
