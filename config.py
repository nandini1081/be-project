"""
Shared configuration for all team members
"""

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

# Scoring Weights
KNOWLEDGE_WEIGHT = 0.6
SPEECH_WEIGHT = 0.4

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