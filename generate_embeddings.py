from sentence_transformers import SentenceTransformer
import sqlite3
import json
from datetime import datetime
import google.generativeai as genai
import time

# Load 384-d embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# ----------------------------
# Configure Gemini
# ----------------------------
genai.configure(api_key="AIzaSyB6vCP3q03wtWaybBpmuLyHn4iOSce7ROM")

llm = genai.GenerativeModel("gemini-2.5-flash")

# ----------------------------
# Load embedding model
# ----------------------------
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def generate_embedding(text):
    return json.dumps(
        model.encode(text, normalize_embeddings=True).tolist()
    )

# 🔥 ADD THIS FUNCTION (ideal answer generator)
def generate_ideal_answers(question_batch):
    """
    question_batch = [
        {
            "question_id": ...,
            "question": ...,
            "topics": ...,
            "keywords": ...
        }
    ]
    """

    prompt = """
You are an expert technical interviewer.

Generate the IDEAL interview answer for every question.

Rules:
1. Return ONLY valid JSON.
2. Preserve question_id.
3. Each answer should be 120-180 words.
4. Be technically accurate.
5. Naturally include all supplied keywords.
6. No bullet points.
7. No markdown.

Output format:

[
  {
    "question_id": 1,
    "ideal_answer": "..."
  }
]

Questions:

"""

    for q in question_batch:

        try:
            topics = json.loads(q["topics"]) if q["topics"] else []
        except:
            topics = []

        try:
            keywords = json.loads(q["keywords"]) if q["keywords"] else []
        except:
            keywords = []

        prompt += f"""

Question ID: {q['question_id']}

Question:
{q['question']}

Topics:
{', '.join(topics)}

Keywords:
{', '.join(keywords)}

"""

    while True:

        try:

            response = llm.generate_content(prompt)

            text = response.text.strip()

            text = text.replace("```json", "").replace("```", "").strip()

            return json.loads(text)

        except Exception as e:

            if "429" in str(e):

                print("Rate limit exceeded.")
                print("Waiting 40 seconds...\n")

                time.sleep(40)
                continue

            print(e)
            return []   

# Connect DB
conn = sqlite3.connect("interview_system.db")
cursor = conn.cursor()

# 🔥 IMPORTANT: Fetch topics + keywords also
cursor.execute("""
    SELECT question_id, question_text, topics, ideal_keywords
    FROM questions
""")

questions = cursor.fetchall()

batch_size = 10

for start in range(0, len(questions), batch_size):

    batch_rows = questions[start:start+batch_size]

    batch = []

    for qid, qtext, topics, keywords in batch_rows:

        batch.append({

            "question_id": qid,
            "question": qtext,
            "topics": topics,
            "keywords": keywords

        })

    print(f"Processing questions {start+1} - {start+len(batch)}")

    ideal_answers = generate_ideal_answers(batch)

    ideal_answer_lookup = {

        item["question_id"]: item["ideal_answer"]

        for item in ideal_answers

    }

    for qid, qtext, topics, keywords in batch_rows:

        question_embedding = generate_embedding(qtext)

        ideal_answer = ideal_answer_lookup.get(qid, "")

        ideal_embedding = generate_embedding(ideal_answer)

        cursor.execute("""

        UPDATE questions

        SET

            embedding=?,

            ideal_answer_embedding=?,

            updated_at=?

        WHERE question_id=?

        """,

        (

            question_embedding,

            ideal_embedding,

            datetime.utcnow().isoformat(),

            qid

        ))

    conn.commit()

    print("Batch saved.\n")

    # Stay below free-tier limit
    time.sleep(15)

conn.commit()
conn.close()

# to generate embeddings for questions, run: python generate_embeddings.py
print("✅ Question + Ideal Answer embeddings generated successfully.")