"""
Centralized embedding service
Shared by ALL team members
"""

from sentence_transformers import SentenceTransformer
from typing import List
from config import EMBEDDING_MODEL, VECTOR_DIMENSION
from .vector_operations import normalize_vector

class EmbeddingService:
    """Singleton service for text embeddings"""

    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            cls._instance._initialize_model()
        return cls._instance

    def _initialize_model(self):
        """Load the embedding model once"""
        print(f"🔄 Loading embedding model: {EMBEDDING_MODEL}")
        self._model = SentenceTransformer(EMBEDDING_MODEL)
        print("✅ Model loaded successfully")

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for single text
        """
        if not text or not text.strip():
            return [0.0] * VECTOR_DIMENSION

        embedding = self._model.encode(text, convert_to_numpy=True)
        return normalize_vector(embedding.tolist())

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (faster)
        """
        if not texts:
            return []

        embeddings = self._model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=True
        )

        return [normalize_vector(emb.tolist()) for emb in embeddings]

    def embed_resume(self, resume_data: dict) -> List[float]:
        """
        Create embedding from parsed resume data
        """
        text_parts = []

        if 'skills' in resume_data:
            text_parts.append(' '.join(resume_data['skills']))

        if 'experience' in resume_data:
            for exp in resume_data['experience']:
                text_parts.append(exp.get('role', ''))
                text_parts.append(exp.get('description', ''))

        if 'projects' in resume_data:
            for proj in resume_data['projects']:
                text_parts.append(proj.get('name', ''))
                text_parts.append(proj.get('description', ''))
                if 'technologies' in proj:
                    text_parts.append(' '.join(proj['technologies']))

        if 'education' in resume_data:
            for edu in resume_data['education']:
                text_parts.append(edu.get('degree', ''))

        combined_text = ' '.join(filter(None, text_parts))
        return self.embed_text(combined_text)

# ✅ Global singleton instance (THIS is what everyone should import)
embedding_service = EmbeddingService()

# ✅ Explicit public API
__all__ = ["embedding_service", "EmbeddingService"]