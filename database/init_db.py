"""
Initialize the database with schema
Run this ONCE at project start: python -m database.init_db
"""

import re
import sqlite3
import os


def _migrate_questions_columns(cursor):
    """Add cross-question columns to existing questions tables."""
    columns = {row[1] for row in cursor.execute("PRAGMA table_info(questions)").fetchall()}
    if not columns:
        return
    if "question_group" not in columns:
        cursor.execute("ALTER TABLE questions ADD COLUMN question_group TEXT")
    if "followup_order" not in columns:
        cursor.execute("ALTER TABLE questions ADD COLUMN followup_order INTEGER DEFAULT 1")
    if "parent_question_id" not in columns:
        cursor.execute("ALTER TABLE questions ADD COLUMN parent_question_id TEXT")


def init_database(db_path='interview_system.db'):
    """Initialize database with complete schema"""
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')

    with open(schema_path, 'r') as f:
        schema_sql = f.read()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    table_sql, index_sql = re.split(r"(?=CREATE INDEX)", schema_sql, maxsplit=1)
    cursor.executescript(table_sql)
    _migrate_questions_columns(cursor)

    for statement in re.findall(r"CREATE INDEX[^;]+;", index_sql):
        try:
            cursor.execute(statement)
        except sqlite3.OperationalError:
            pass

    conn.commit()
    conn.close()

    print(f"✅ Database initialized successfully at: {db_path}")
    print("📊 Tables created:")
    print("   - questions")
    print("   - candidate_profiles")
    print("   - parsed_resumes")
    print("   - interview_history")
    print("   - retrieval_cache")


if __name__ == "__main__":
    init_database()
