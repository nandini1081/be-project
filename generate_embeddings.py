from sentence_transformers import SentenceTransformer
import sqlite3
import json
from datetime import datetime

# Load 384-d embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

def generate_embedding(text):
    return json.dumps(
        model.encode(text, normalize_embeddings=True).tolist()
    )

# Update path if needed
conn = sqlite3.connect("interview_system.db")
cursor = conn.cursor()

cursor.execute("SELECT question_id, question_text FROM questions")
questions = cursor.fetchall()

for qid, qtext in questions:
    embedding = generate_embedding(qtext)
    cursor.execute("""
        UPDATE questions
        SET embedding = ?, updated_at = ?
        WHERE question_id = ?
    """, (embedding, datetime.utcnow().isoformat(), qid))

conn.commit()

# cursor.execute("SELECT COUNT(*) FROM questions")
# print("Question count:", cursor.fetchone()[0])

conn.close()

print("✅ Embeddings successfully generated and stored.")