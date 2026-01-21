"""
Initialize the database with schema
Run this ONCE at project start: python -m database.init_db
"""

import sqlite3
import os

def init_database(db_path='interview_system.db'):
    """Initialize database with complete schema"""
    
    # Read schema file
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    
    # Create database and execute schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Execute all CREATE statements
    cursor.executescript(schema_sql)
    
    conn.commit()
    conn.close()
    
    print(f"✅ Database initialized successfully at: {db_path}")
    print(f"📊 Tables created:")
    print("   - questions")
    print("   - candidate_profiles")
    print("   - parsed_resumes")
    print("   - interview_history")
    print("   - retrieval_cache")

if __name__ == "__main__":
    init_database()