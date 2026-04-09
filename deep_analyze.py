"""Deep dive: find the user prompt and full structure from trace data."""
import json
from collections import Counter

TRACE_FILE = "otel-traces.jsonl"

records = []
with open(TRACE_FILE, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        records.append(json.loads(line))

print(f"Total records: {len(records)}")

# Look at ALL attribute keys across all records
all_keys = Counter()
for rec in records:
    attrs = rec.get("attributes", {})
    for k in attrs:
        all_keys[k] += 1

print("\n=== ALL ATTRIBUTE KEYS ===")
for k, c in all_keys.most_common():
    print(f"  {k}: {c}")

# Look specifically for content-related keys
print("\n=== CONTENT-RELATED ATTRIBUTES ===")
content_patterns = ["content", "prompt", "message", "input", "output", "instruction", "completion", "argument", "result"]
for k, c in all_keys.most_common():
    if any(p in k.lower() for p in content_patterns):
        print(f"  {k}: {c}")

# Check record types (span vs log record)
print("\n=== RECORD TYPES ===")
types = Counter()
for rec in records:
    if "instrumentationScope" in rec:
        scope = rec["instrumentationScope"].get("name", "unknown")
    else:
        scope = "no-scope"
    has_trace = "traceId" in rec or "traceId" in rec.get("spanContext", {})
    has_span = "spanId" in rec or "spanId" in rec.get("spanContext", {})
    types[f"scope={scope}"] += 1

for t, c in types.most_common():
    print(f"  {t}: {c}")

# Look at spanContext to find trace hierarchy
print("\n=== SPANS WITH TRACE/SPAN IDS ===")
span_count = 0
for rec in records:
    sc = rec.get("spanContext", {})
    if sc.get("traceId"):
        span_count += 1
        if span_count <= 3:
            attrs = rec.get("attributes", {})
            print(f"  traceId={sc.get('traceId','?')[:16]}... spanId={sc.get('spanId','?')}")
            print(f"    name={attrs.get('name', '?')} op={attrs.get('gen_ai.operation.name', '?')}")
            print(f"    attrs keys: {list(attrs.keys())[:15]}")
print(f"  Total spans with spanContext: {span_count}")

# Orphan records - what are they?
print("\n=== ORPHAN RECORDS (no session.id) ===")
orphan_events = Counter()
orphan_attrs_sample = None
for rec in records:
    attrs = rec.get("attributes", {})
    res_attrs = dict(rec.get("resource", {}).get("_rawAttributes", []))
    sid = res_attrs.get("session.id", attrs.get("session.id"))
    if sid is None:
        ev = attrs.get("event.name", "<none>")
        orphan_events[ev] += 1
        if orphan_attrs_sample is None:
            orphan_attrs_sample = list(attrs.keys())

print(f"  Events: {dict(orphan_events.most_common())}")
print(f"  Sample attrs: {orphan_attrs_sample}")

# Check first orphan in detail
for rec in records:
    attrs = rec.get("attributes", {})
    res_attrs = dict(rec.get("resource", {}).get("_rawAttributes", []))
    sid = res_attrs.get("session.id", attrs.get("session.id"))
    if sid is None:
        print(f"\n  FIRST ORPHAN RAW KEYS: {list(rec.keys())}")
        res = rec.get("resource", {})
        print(f"  resource keys: {list(res.keys())}")
        print(f"  resource._rawAttributes: {res.get('_rawAttributes', [])[:5]}")
        sc = rec.get("spanContext", {})
        print(f"  spanContext: {sc}")
        scope = rec.get("instrumentationScope", {})
        print(f"  instrumentationScope: {scope}")
        # Show all attrs
        print(f"  ALL attrs ({len(attrs)} keys):")
        for k, v in list(attrs.items())[:20]:
            val = str(v)[:200]
            print(f"    {k}: {val}")
        break

# Now specifically find records with prompt/user content
print("\n=== SEARCHING FOR USER PROMPTS ===")
for rec in records:
    attrs = rec.get("attributes", {})
    for k, v in attrs.items():
        val_str = str(v)
        if "user" in k.lower() and "message" in k.lower():
            print(f"  KEY={k} VAL_LEN={len(val_str)} PREVIEW={val_str[:300]}")
        if isinstance(v, str) and len(v) > 100:
            # Large string attribute - could be content
            if any(marker in v[:200].lower() for marker in ["create", "build", "write", "help", "make", "generate", "fix"]):
                print(f"  LARGE ATTR: key={k} len={len(v)} preview={v[:200]}")
