-- Complete database schema for AI Interview System

-- Table 1: Questions with pre-computed embeddings
CREATE TABLE IF NOT EXISTS questions (
    question_id TEXT PRIMARY KEY,
    question_text TEXT NOT NULL,
    category TEXT NOT NULL CHECK(category IN ('technical', 'behavioral', 'situational')),
    difficulty TEXT NOT NULL CHECK(difficulty IN ('easy', 'medium', 'hard')),
    topics TEXT NOT NULL,  -- JSON array: ["Python", "ML"]
    job_roles TEXT NOT NULL,  -- JSON array: ["Software Engineer"]
    embedding TEXT NOT NULL,  -- JSON array: 384 floats
    ideal_keywords TEXT,  -- JSON array: ["keyword1", "keyword2"]
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Table 2: Candidate profiles with vectors
CREATE TABLE IF NOT EXISTS candidate_profiles (
    candidate_id TEXT PRIMARY KEY,
    profile_vector TEXT NOT NULL,  -- JSON array: 384 floats (normalized)
    metadata TEXT NOT NULL,  -- JSON: {skills, experience_level, domain}
    version INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Table 3: Parsed resumes
CREATE TABLE IF NOT EXISTS parsed_resumes (
    candidate_id TEXT PRIMARY KEY,
    personal_info TEXT NOT NULL,  -- JSON: {name, email}
    skills TEXT NOT NULL,  -- JSON array: ["Python", "ML"]
    experience TEXT NOT NULL,  -- JSON array of experience objects
    projects TEXT NOT NULL,  -- JSON array of project objects
    education TEXT NOT NULL,  -- JSON array of education objects
    raw_text TEXT NOT NULL,  -- Full concatenated text for embedding
    created_at TEXT NOT NULL
);

-- Table 4: Interview history and responses
CREATE TABLE IF NOT EXISTS interview_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id TEXT NOT NULL,
    question_id TEXT NOT NULL,
    answer_text TEXT,
    knowledge_score REAL,  -- 0.0 to 1.0
    speech_score REAL,  -- 0.0 to 1.0
    total_score REAL,  -- Weighted combination
    timestamp TEXT NOT NULL,
    FOREIGN KEY (candidate_id) REFERENCES candidate_profiles(candidate_id),
    FOREIGN KEY (question_id) REFERENCES questions(question_id)
);

-- Table 5: Question retrieval cache (optional, for performance)
CREATE TABLE IF NOT EXISTS retrieval_cache (
    cache_id TEXT PRIMARY KEY,
    candidate_id TEXT NOT NULL,
    retrieved_questions TEXT NOT NULL,  -- JSON array of question_ids
    similarity_scores TEXT NOT NULL,  -- JSON array of scores
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);

-- Indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_candidate_history ON interview_history(candidate_id);
CREATE INDEX IF NOT EXISTS idx_question_difficulty ON questions(difficulty);
CREATE INDEX IF NOT EXISTS idx_question_category ON questions(category);
CREATE INDEX IF NOT EXISTS idx_history_timestamp ON interview_history(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_cache_candidate ON retrieval_cache(candidate_id);