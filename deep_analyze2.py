"""Look at raw record structures to understand format."""
import json

TRACE_FILE = "otel-traces.jsonl"

records = []
with open(TRACE_FILE, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        records.append(json.loads(line))

# Find different types and print a full example of each
seen_types = set()
for i, rec in enumerate(records):
    attrs = rec.get("attributes", {})
    event = attrs.get("event.name", "")
    has_scope = bool(rec.get("instrumentationScope", {}).get("name"))
    has_attrs = len(attrs) > 0
    has_res = len(rec.get("resource", {}).get("_rawAttributes", [])) > 0
    rec_type = f"event={event or 'none'}_scope={has_scope}_attrs={has_attrs}_res={has_res}"

    if rec_type not in seen_types:
        seen_types.add(rec_type)
        # Print full record structure (truncate long vals)
        print(f"\n{'='*60}")
        print(f"Record #{i} type: {rec_type}")
        print(f"Top-level keys: {list(rec.keys())}")

        for k, v in rec.items():
            if k == "attributes":
                print(f"  attributes ({len(v)} keys):")
                for ak, av in v.items():
                    avs = str(av)
                    if len(avs) > 200:
                        avs = avs[:200] + f"... ({len(avs)} chars)"
                    print(f"    {ak}: {avs}")
            elif k == "resource":
                raw = v.get("_rawAttributes", [])
                print(f"  resource._rawAttributes ({len(raw)} items): {raw[:5]}")
            elif k == "spanContext":
                print(f"  spanContext: {v}")
            elif k == "_body":
                bs = str(v)
                if len(bs) > 200:
                    bs = bs[:200] + "..."
                print(f"  _body: {bs}")
            elif k == "hrTime":
                print(f"  hrTime: {v}")
            else:
                vs = str(v)
                if len(vs) > 200:
                    vs = vs[:200] + "..."
                print(f"  {k}: {vs}")

# Now check: are any records actually OTLP spans (not log records)?
print(f"\n{'='*60}")
print("CHECKING FOR OTLP SPAN FORMAT")
for i, rec in enumerate(records[:5]):
    print(f"\nRecord {i} top keys: {sorted(rec.keys())}")

# Check the 342 scope=no-scope records
print(f"\n{'='*60}")
print("NO-SCOPE RECORDS SAMPLE")
no_scope_count = 0
for rec in records:
    if not rec.get("instrumentationScope", {}).get("name"):
        no_scope_count += 1
        if no_scope_count <= 3:
            print(f"\nRecord: {json.dumps(rec, default=str)[:500]}")
print(f"\nTotal no-scope: {no_scope_count}")

# Check: maybe it's OTLP format now (resourceSpans)?
print(f"\n{'='*60}")
print("FIRST 2 RECORDS RAW (truncated to 800 chars)")
with open(TRACE_FILE, "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if i >= 2:
            break
        line = line.strip()
        if len(line) > 800:
            print(f"Line {i} ({len(line)} chars): {line[:800]}...")
        else:
            print(f"Line {i} ({len(line)} chars): {line}")
