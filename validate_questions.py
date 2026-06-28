"""Validate questions.sql numbering, groups, and SQL row format."""
import re
import sqlite3
from collections import defaultdict
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

# Group chain validation
group_pattern = re.compile(
    r"\('(Q\d+)','.+?','(\w+)','(\w+)','.+?','.+?','\[\]','.+?',"
    r"'([^']+)',(\d+),(NULL|'Q\d+')"
)
groups: dict[str, list[tuple]] = defaultdict(list)
for line in data_lines:
    m = group_pattern.search(line.replace("''", "'"))
    if not m:
        continue
    qid, _cat, _diff, group_id, order, parent = m.groups()
    parent = None if parent == "NULL" else parent.strip("'")
    groups[group_id].append((int(order), qid, parent))

bad_groups = []
for group_id, items in groups.items():
    items.sort(key=lambda x: x[0])
    orders = [o for o, _, _ in items]
    if orders != list(range(1, len(items) + 1)):
        bad_groups.append((group_id, "non-sequential followup_order", orders))
    parents = [p for _, _, p in items]
    if parents[0] is not None:
        bad_groups.append((group_id, "first question should have NULL parent", parents[0]))
    root = items[0][1]
    for order, qid, parent in items[1:]:
        if parent != root:
            bad_groups.append((group_id, f"{qid} parent should be {root}", parent))

if bad_groups:
    print("GROUP ISSUES:")
    for row in bad_groups[:15]:
        print(" ", row)
else:
    print("GROUP CHAINS: OK (%d groups)" % len(groups))

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

if (
    not dups
    and not missing
    and not out_of_order
    and data_lines
    and data_lines[-1].strip().endswith(";")
    and not bad_groups
):
    print("\nRESULT: PASS")
else:
    print("\nRESULT: ISSUES FOUND")
