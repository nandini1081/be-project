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
MAX_QUESTIONS_PER_SESSION = 10
MIN_SIMILARITY_SCORE = 0.7

# Scoring Weights
KNOWLEDGE_WEIGHT = 0.6
SPEECH_WEIGHT = 0.4