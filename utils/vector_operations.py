"""
Vector operations for similarity computation
Shared by ALL team members
"""

import numpy as np
from typing import List, Tuple
from config import VECTOR_DIMENSION

def normalize_vector(vector: List[float]) -> List[float]:
    """
    Normalize vector to unit length
    
    Args:
        vector: Input vector
    
    Returns:
        Normalized vector (unit length)
    """
    vector = np.array(vector)
    norm = np.linalg.norm(vector)
    
    if norm == 0:
        return vector.tolist()
    
    normalized = vector / norm
    return normalized.tolist()

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Compute cosine similarity between two vectors
    Assumes vectors are already normalized
    
    Args:
        vec1: First vector (normalized)
        vec2: Second vector (normalized)
    
    Returns:
        Similarity score (0 to 1)
    """
    return float(np.dot(vec1, vec2))

def batch_cosine_similarity(query_vector: List[float], 
                           vectors: List[List[float]]) -> List[float]:
    """
    Compute cosine similarity between query and multiple vectors
    Optimized for speed using NumPy
    
    Args:
        query_vector: Single query vector (normalized)
        vectors: List of vectors to compare against (normalized)
    
    Returns:
        List of similarity scores
    """
    query = np.array(query_vector)
    matrix = np.array(vectors)
    
    # Dot product for all vectors at once
    similarities = np.dot(matrix, query)
    
    return similarities.tolist()

def validate_vector(vector: List[float], name: str = "vector") -> bool:
    """
    Validate vector dimensions and properties
    
    Args:
        vector: Vector to validate
        name: Name for error messages
    
    Returns:
        True if valid
    
    Raises:
        ValueError: If validation fails
    """
    if len(vector) != VECTOR_DIMENSION:
        raise ValueError(f"{name} must have {VECTOR_DIMENSION} dimensions, got {len(vector)}")
    
    if not all(isinstance(x, (int, float)) for x in vector):
        raise ValueError(f"{name} must contain only numeric values")
    
    norm = np.linalg.norm(vector)
    if not (0.99 <= norm <= 1.01):
        print(f"⚠️  Warning: {name} norm is {norm:.4f}, expected ~1.0 (not normalized)")
    
    return True

def weighted_vector_update(old_vector: List[float], 
                          new_vector: List[float],
                          old_weight: float = 0.8,
                          new_weight: float = 0.2) -> List[float]:
    """
    Update vector using weighted averaging
    Used by Person B for profile updates
    
    Args:
        old_vector: Current profile vector
        new_vector: New information vector
        old_weight: Weight for old vector
        new_weight: Weight for new vector
    
    Returns:
        Updated normalized vector
    """
    old = np.array(old_vector)
    new = np.array(new_vector)
    
    # Weighted average
    updated = (old * old_weight) + (new * new_weight)
    
    # Normalize
    return normalize_vector(updated.tolist())