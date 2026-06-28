"""
Shared configuration for all team members
"""

import os

# Vector and Model Configuration
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
VECTOR_DIMENSION = 384
SIMILARITY_THRESHOLD = 0.2

# Database Configuration
DATABASE_PATH = "interview_system.db"
ENABLE_CACHE = True
CACHE_EXPIRY_MINUTES = 5

# History Configuration
HISTORY_LIMIT = 50

# Update Weights (for Person B)
UPDATE_OLD_WEIGHT = 0.8
UPDATE_NEW_WEIGHT = 0.2

# Question Retrieval
MAX_QUESTIONS_PER_SESSION = 15
TOP_MATCH_POOL_SIZE = 40
MIN_SIMILARITY_SCORE = 0.7
MAX_FOLLOWUPS_PER_GROUP = 3          # entry question + up to 3 follow-ups
MAX_QUESTIONS_PER_GROUP = MAX_FOLLOWUPS_PER_GROUP + 1
MAX_BEHAVIORAL_RATIO = 0.20          # at most 20% behavioral in a mixed interview

# Scoring Weights
KNOWLEDGE_WEIGHT = 0.6
SPEECH_WEIGHT = 0.4
SPEECH_SCORE_MAX = 0.94                # speech score is capped below 100%

# Audio speech analysis (faster-whisper + librosa)
SPEECH_WHISPER_MODEL = "base"
SPEECH_WHISPER_DEVICE = "cpu"
SPEECH_COMPONENT_WEIGHTS = {
    "filler": 0.25,
    "pause_pacing": 0.25,
    "pronunciation": 0.25,
    "tone_energy": 0.25,
}
SPEECH_IDEAL_WPM = 135
SPEECH_LONG_PAUSE_SECONDS = 1.2
SPEECH_MAX_FILLER_RATE = 0.15

# LLM feedback (set OPENAI_API_KEY in .env to enable)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "45"))