"""Validate questions.sql numbering and SQL row format."""
import re
import sqlite3
from pathlib import Path

text = Path("database/queries/questions.sql").read_text(encoding="utf-8")
ids = re.findall(r"\('(Q\d+)'", text)
nums = [int(x[1:]) for x in ids]

print("Total questions:", len(ids))
print("Unique IDs:", len(set(ids)))

dups = sorted({x for x in ids if ids.count(x) > 1})
if dups:
    print("DUPLICATES:", dups)

if nums:
    expected_max = max(nums)
    missing = [n for n in range(1, expected_max + 1) if f"Q{n:03d}" not in ids]
    if missing:
        print("MISSING:", [f"Q{n:03d}" for n in missing])

    out_of_order = []
    for i, (expected, actual) in enumerate(zip(range(1, len(ids) + 1), nums), 1):
        if expected != actual:
            out_of_order.append((i, f"Q{expected:03d}", f"Q{actual:03d}"))
    if out_of_order:
        print("ORDER MISMATCHES (position, expected, got):")
        for row in out_of_order[:10]:
            print(" ", row)
    else:
        print("ORDER: Q001 through Q%03d sequential" % expected_max)

lines = text.strip().splitlines()
data_lines = [l for l in lines if l.strip().startswith("('Q")]
if data_lines:
    last = data_lines[-1].strip()
    print("Last ID:", re.search(r"\('(Q\d+)'", last).group(1))
    print("Last row terminator:", "OK (semicolon)" if last.endswith(";") else "BAD")

# Invalid category/difficulty values
valid_cat = {"technical", "behavioral", "situational"}
valid_diff = {"easy", "medium", "hard"}
bad_fields = []
for i, line in enumerate(lines, 1):
    if not line.strip().startswith("('Q"):
        continue
    m = re.match(
        r"\('Q\d+','.+?','(\w+)','(\w+)'",
        line,
    )
    if m:
        cat, diff = m.group(1), m.group(2)
        if cat not in valid_cat or diff not in valid_diff:
            bad_fields.append((i, cat, diff))

if bad_fields:
    print("INVALID category/difficulty:")
    for row in bad_fields[:20]:
        print(" ", row)

# SQL syntax check (in-memory)
conn = sqlite3.connect(":memory:")
conn.executescript(Path("database/schema.sql").read_text(encoding="utf-8"))
try:
    conn.executescript(text)
    count = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    print("SQL EXECUTION: OK (%d rows would be inserted)" % count)
except sqlite3.Error as e:
    print("SQL EXECUTION ERROR:", e)

conn.close()

if not dups and not missing and not out_of_order and data_lines[-1].strip().endswith(";"):
    print("\nRESULT: PASS")
else:
    print("\nRESULT: ISSUES FOUND")
