"""Apply question_group columns to an existing interview_system.db."""
import sqlite3

DB = "interview_system.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()
cols = {row[1] for row in cur.execute("PRAGMA table_info(questions)").fetchall()}
if "question_group" not in cols:
    cur.execute("ALTER TABLE questions ADD COLUMN question_group TEXT")
if "followup_order" not in cols:
    cur.execute("ALTER TABLE questions ADD COLUMN followup_order INTEGER DEFAULT 1")
if "parent_question_id" not in cols:
    cur.execute("ALTER TABLE questions ADD COLUMN parent_question_id TEXT")
cur.execute("CREATE INDEX IF NOT EXISTS idx_question_group ON questions(question_group)")
cur.execute(
    "CREATE INDEX IF NOT EXISTS idx_question_group_order "
    "ON questions(question_group, followup_order)"
)
conn.commit()
conn.close()
print("Migration complete")
