# AI Interview Preparation System

Complete end-to-end system for personalized interview preparation.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Initialize Database
```bash
python -m database.init_db
python -m database.sample_data  # Optional: add sample data
```

### 3. Run Application
```bash
python app.py
```

Server will start at `http://localhost:5000`

## API Endpoints

### Person A - Profile Creation
- `POST /api/parse-resume` - Parse resume
- `POST /api/create-profile` - Create profile vector
- `POST /api/full-resume-processing` - Complete pipeline

### Person B - Profile Updates
- `POST /api/update-profile/<candidate_id>` - Update profile
- `POST /api/record-response` - Record interview response
- `GET /api/performance-summary/<candidate_id>` - Get stats

### Person C - Question Management
- `POST /api/add-question` - Add single question
- `POST /api/bulk-add-questions` - Add multiple questions
- `GET /api/database-summary` - Get database stats

### Person D - Question Retrieval
- `GET /api/retrieve-questions/<candidate_id>` - Get personalized questions
- `GET /api/adaptive-questions/<candidate_id>` - Get adaptive questions
- `GET /api/diverse-questions/<candidate_id>` - Get diverse questions
- `GET /api/recommendations/<candidate_id>` - Get recommendations

### Common
- `GET /api/health` - Health check
- `GET /api/stats` - Database statistics
- `GET /api/candidate/<candidate_id>` - Get candidate info

## Testing Examples

### 1. Parse Resume and Create Profile
```bash
curl -X POST http://localhost:5000/api/full-resume-processing \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "John Doe, Python Developer with 3 years experience in Machine Learning..."
  }'
```

### 2. Add Questions
```bash
curl -X POST http://localhost:5000/api/add-question \
  -H "Content-Type: application/json" \
  -d '{
    "question_text": "Explain supervised learning",
    "category": "technical",
    "difficulty": "medium",
    "topics": ["Machine Learning", "AI"],
    "job_roles": ["Data Scientist"]
  }'
```

### 3. Retrieve Questions
```bash
curl http://localhost:5000/api/retrieve-questions/CANDIDATE_ID?max_questions=5
```

### 4. Record Response
```bash
curl -X POST http://localhost:5000/api/record-response \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_id": "CANDIDATE_ID",
    "question_id": "QUESTION_ID",
    "answer_text": "Supervised learning uses labeled data...",
    "knowledge_score": 0.85,
    "speech_score": 0.75
  }'
```

## Architecture
````
Resume → Parser → Profile Creator → Database
                         ↓
                  Profile Vector (384-dim)
                         ↓
              Question Retriever (Similarity Match)
                         ↓
                  Personalized Questions
                         ↓
              Interview Response Recording
                         ↓
              Profile Updater (Weighted Average)