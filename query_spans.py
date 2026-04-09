"""Query the agent-traces.db SQLite database for span data."""
import sqlite3
import json
from datetime import datetime, timezone, timedelta

DB_PATH = r"C:\Users\mattge\AppData\Roaming\Code - Insiders\User\globalStorage\github.copilot-chat\agent-traces.db"
PDT = timezone(timedelta(hours=-7))

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# List all tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print(f"Tables: {tables}")

for table in tables:
    cur.execute(f"SELECT COUNT(*) FROM [{table}]")
    count = cur.fetchone()[0]
    print(f"  {table}: {count} rows")
    
    # Show columns
    cur.execute(f"PRAGMA table_info([{table}])")
    cols = cur.fetchall()
    col_names = [c['name'] for c in cols]
    print(f"    Columns: {col_names}")
    
    # Show first 3 rows
    cur.execute(f"SELECT * FROM [{table}] LIMIT 3")
    rows = cur.fetchall()
    for i, row in enumerate(rows):
        print(f"\n    Row {i}:")
        for col in col_names:
            val = row[col]
            if isinstance(val, str) and len(val) > 300:
                val = val[:300] + f"... ({len(row[col])} chars)"
            elif isinstance(val, bytes) and len(val) > 100:
                val = f"<{len(val)} bytes>"
            print(f"      {col}: {val}")

conn.close()
