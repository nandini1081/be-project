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

# 🔥 ADD THIS FUNCTION (ideal answer generator)
def generate_ideal_answer(question_text, topics_json, keywords_json):
    try:
        topics = json.loads(topics_json)
    except:
        topics = []

    try:
        keywords = json.loads(keywords_json) if keywords_json else []
    except:
        keywords = []

    topic_part = ", ".join(topics)
    keyword_part = ", ".join(keywords)

    return f"A strong answer explaining {topic_part}, covering key concepts such as {keyword_part}."

# Connect DB
conn = sqlite3.connect("interview_system.db")
cursor = conn.cursor()

# 🔥 IMPORTANT: Fetch topics + keywords also
cursor.execute("""
    SELECT question_id, question_text, topics, ideal_keywords
    FROM questions
""")

questions = cursor.fetchall()

for qid, qtext, topics, keywords in questions:
    
    # 1️⃣ Question embedding (already existed)
    question_embedding = generate_embedding(qtext)

    # 2️⃣ Generate ideal answer (NEW)
    ideal_answer = generate_ideal_answer(qtext, topics, keywords)

    # 3️⃣ Ideal answer embedding (NEW)
    ideal_embedding = generate_embedding(ideal_answer)

    # 4️⃣ Store both
    cursor.execute("""
        UPDATE questions
        SET embedding = ?, 
            ideal_answer_embedding = ?, 
            updated_at = ?
        WHERE question_id = ?
    """, (
        question_embedding,
        ideal_embedding,
        datetime.utcnow().isoformat(),
        qid
    ))

conn.commit()
conn.close()

# to generate embeddings for questions, run: python generate_embeddings.py
print("✅ Question + Ideal Answer embeddings generated successfully.")