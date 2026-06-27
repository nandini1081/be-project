"""Load questions from database/queries/questions.sql into interview_system.db."""

import argparse
import re
import sqlite3
from pathlib import Path

DEFAULT_SQL = Path("database/queries/questions.sql")
DEFAULT_DB = Path("interview_system.db")

QUESTION_ID_PATTERN = re.compile(r"\('(Q\d+)'")


def extract_question_ids(sql_script: str) -> set[str]:
    return set(QUESTION_ID_PATTERN.findall(sql_script))


def prepare_sql(sql_script: str, mode: str) -> str:
    if mode == "fail":
        return sql_script

    conflict_clause = "OR IGNORE" if mode == "skip" else "OR REPLACE"
    return re.sub(
        r"INSERT\s+INTO\s+questions",
        f"INSERT {conflict_clause} INTO questions",
        sql_script,
        count=1,
        flags=re.IGNORECASE,
    )


def prune_questions_not_in_sql(conn: sqlite3.Connection, sql_ids: set[str]) -> int:
    """Remove questions (and related history) that are not in the SQL file."""
    db_ids = {
        row[0]
        for row in conn.execute("SELECT question_id FROM questions").fetchall()
    }
    orphan_ids = sorted(db_ids - sql_ids)
    if not orphan_ids:
        return 0

    placeholders = ",".join("?" * len(orphan_ids))
    conn.execute(
        f"DELETE FROM interview_history WHERE question_id IN ({placeholders})",
        orphan_ids,
    )
    conn.execute(
        f"DELETE FROM questions WHERE question_id IN ({placeholders})",
        orphan_ids,
    )
    return len(orphan_ids)


def load_questions(sql_path: Path, db_path: Path, mode: str, sync: bool) -> None:
    if not sql_path.is_file():
        raise FileNotFoundError(f"SQL file not found: {sql_path}")
    if not db_path.is_file():
        raise FileNotFoundError(f"Database not found: {db_path}. Run: python -m database.init_db")

    sql_script = sql_path.read_text(encoding="utf-8")
    sql_ids = extract_question_ids(sql_script)
    prepared_sql = prepare_sql(sql_script, mode)

    conn = sqlite3.connect(db_path)
    try:
        before = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
        removed = 0
        if sync:
            removed = prune_questions_not_in_sql(conn, sql_ids)

        conn.executescript(prepared_sql)
        after = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
        conn.commit()
    finally:
        conn.close()

    print(f"Loaded questions from {sql_path}")
    print(f"  Questions in SQL file: {len(sql_ids)}")
    print(f"  Mode: {mode}" + (" + sync (remove old)" if sync else ""))
    print(f"  Questions in database: {after} (was {before})")
    if sync and removed:
        print(f"  Removed {removed} old question(s) not in SQL file")
    elif sync:
        print("  No old questions to remove")

    if mode == "replace" and before != after and not sync:
        print("  Note: use --sync to drop questions that are no longer in the SQL file.")
    if mode in ("replace", "fail") or sync:
        print("  Re-run generate_embeddings.py if you need to refresh embeddings.")

    print("Questions loaded successfully")


def main() -> None:
    parser = argparse.ArgumentParser(description="Load interview questions into SQLite")
    parser.add_argument(
        "--sql",
        type=Path,
        default=DEFAULT_SQL,
        help=f"Path to questions SQL file (default: {DEFAULT_SQL})",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB,
        help=f"Path to SQLite database (default: {DEFAULT_DB})",
    )
    parser.add_argument(
        "--mode",
        choices=("replace", "skip", "fail"),
        default="replace",
        help="replace: upsert questions (default); skip: insert only new IDs; fail: error on duplicates",
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        default=True,
        help="remove DB questions not present in the SQL file (default: on)",
    )
    parser.add_argument(
        "--no-sync",
        action="store_false",
        dest="sync",
        help="keep old questions that are not in the SQL file",
    )
    args = parser.parse_args()
    load_questions(args.sql, args.db, args.mode, args.sync)


if __name__ == "__main__":
    main()
