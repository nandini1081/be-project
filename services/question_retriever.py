"""
Question Retriever - Person D
Retrieves personalized questions based on candidate profile
"""

from typing import Dict, List, Tuple, Optional
from database import DatabaseManager
from utils import batch_cosine_similarity
from utils.vector_operations import validate_vector
from config import SIMILARITY_THRESHOLD, MAX_QUESTIONS_PER_SESSION

class QuestionRetriever:
    """Retrieve personalized questions for candidates"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self._question_cache = None
    
    def _load_questions(self, force_reload: bool = False):
        """Load all questions into memory (cache)"""
        if self._question_cache is None or force_reload:
            print("🔄 Loading questions from database...")
            self._question_cache = self.db.get_all_questions()
            print(f"✅ Loaded {len(self._question_cache)} questions")
    
    def retrieve_questions(self, candidate_id: str,
                          min_similarity: float = SIMILARITY_THRESHOLD,
                          max_questions: int = MAX_QUESTIONS_PER_SESSION,
                          difficulty: Optional[str] = None,
                          category: Optional[str] = None) -> List[Dict]:
        """
        Retrieve personalized questions for candidate
        
        Args:
            candidate_id: Candidate identifier
            min_similarity: Minimum similarity threshold
            max_questions: Maximum number of questions to return
            difficulty: Optional filter by difficulty
            category: Optional filter by category
        
        Returns:
            List of matched questions with similarity scores
        """
        print(f"🔄 Retrieving questions for candidate: {candidate_id}")
        
        # Check cache first
        cached = self.db.get_cached_retrieval(candidate_id)
        if cached:
            print("✅ Using cached results")
            question_ids = cached['question_ids'][:max_questions]
            return [self.db.get_question_by_id(qid) for qid in question_ids]
        
        # Get candidate profile
        profile = self.db.get_candidate_profile(candidate_id)
        if not profile:
            print(f"❌ Profile not found for: {candidate_id}")
            return []
        
        profile_vector = profile['profile_vector']
        
        # Validate
        try:
            validate_vector(profile_vector, "profile_vector")
        except ValueError as e:
            print(f"❌ Invalid profile vector: {e}")
            return []
        
        # Load questions
        self._load_questions()
        
        # Filter by difficulty and category if specified
        questions = self._question_cache
        if difficulty:
            questions = [q for q in questions if q['difficulty'] == difficulty]
        if category:
            questions = [q for q in questions if q['category'] == category]
        
        print(f"📊 Comparing with {len(questions)} questions...")
        
        # Extract embeddings
        question_embeddings = [q['embedding'] for q in questions]
        
        # Compute similarities (vectorized - FAST!)
        similarities = batch_cosine_similarity(profile_vector, question_embeddings)
        
        # Combine questions with scores
        scored_questions = []
        for q, sim in zip(questions, similarities):
            if sim >= min_similarity:
                q_with_score = q.copy()
                q_with_score['similarity_score'] = round(sim, 4)
                scored_questions.append(q_with_score)
        
        # Sort by similarity (highest first)
        scored_questions.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        # Limit results
        results = scored_questions[:max_questions]
        
        print(f"✅ Found {len(results)} matching questions")
        if results:
            print(f"   Top score: {results[0]['similarity_score']:.4f}")
            print(f"   Lowest score: {results[-1]['similarity_score']:.4f}")
        
        # Cache results
        question_ids = [q['question_id'] for q in results]
        scores = [q['similarity_score'] for q in results]
        self.db.cache_retrieval_results(candidate_id, question_ids, scores)
        
        return results
    
    def retrieve_adaptive_questions(self, candidate_id: str,
                                   last_score: Optional[float] = None,
                                   max_questions: int = 5) -> List[Dict]:
        """
        Retrieve questions with adaptive difficulty
        
        Args:
            candidate_id: Candidate identifier
            last_score: Score from last question (0-1)
            max_questions: Number of questions to return
        
        Returns:
            List of questions adapted to performance
        """
        # Determine difficulty based on last score
        if last_score is None:
            difficulty = 'medium'  # Start with medium
        elif last_score >= 0.8:
            difficulty = 'hard'  # Increase difficulty
        elif last_score >= 0.5:
            difficulty = 'medium'  # Keep same
        else:
            difficulty = 'easy'  # Decrease difficulty
        
        print(f"🎯 Adaptive retrieval - difficulty: {difficulty}")
        
        return self.retrieve_questions(
            candidate_id=candidate_id,
            max_questions=max_questions,
            difficulty=difficulty
        )
    
    def get_diverse_questions(self, candidate_id: str,
                            questions_per_category: int = 3) -> List[Dict]:
        """
        Get diverse questions across categories
        
        Args:
            candidate_id: Candidate identifier
            questions_per_category: Questions per category
        
        Returns:
            Diversified question set
        """
        categories = ['technical', 'behavioral', 'situational']
        all_questions = []
        
        for cat in categories:
            questions = self.retrieve_questions(
                candidate_id=candidate_id,
                max_questions=questions_per_category,
                category=cat
            )
            all_questions.extend(questions)
        
        print(f"✅ Retrieved {len(all_questions)} diverse questions")
        return all_questions
    
    def get_question_recommendations(self, candidate_id: str) -> Dict:
        """
        Get question recommendations with explanations
        
        Args:
            candidate_id: Candidate identifier
        
        Returns:
            Recommendations dict
        """
        profile = self.db.get_candidate_profile(candidate_id)
        if not profile:
            return {'error': 'Profile not found'}
        
        metadata = profile['metadata']
        
        # Get questions
        questions = self.retrieve_questions(candidate_id, max_questions=10)
        
        # Analyze recommendations
        recommended_topics = {}
        for q in questions[:5]:
            for topic in q['topics']:
                recommended_topics[topic] = recommended_topics.get(topic, 0) + 1
        
        return {
            'candidate_id': candidate_id,
            'experience_level': metadata.get('experience_level', 'Unknown'),
            'primary_domain': metadata.get('primary_domain', 'Unknown'),
            'total_matches': len(questions),
            'top_questions': questions[:5],
            'recommended_topics': dict(sorted(recommended_topics.items(), 
                                            key=lambda x: x[1], reverse=True)),
            'average_similarity': round(sum(q['similarity_score'] for q in questions) / len(questions), 4) if questions else 0
        }
