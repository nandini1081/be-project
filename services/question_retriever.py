"""
Question Retriever - Person D
Retrieves personalized questions based on candidate profile
"""

import random
from typing import Dict, List, Optional
from database import DatabaseManager
from utils import batch_cosine_similarity
from utils.vector_operations import validate_vector
from config import TOP_MATCH_POOL_SIZE

class QuestionRetriever:
    """Retrieve personalized questions for candidates"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self._question_cache = None
    
    def _load_questions(self, force_reload: bool = False):
        ##load questions according to profile vector of candidate and according to the label.
        """Load all questions into memory (cache)"""
        if self._question_cache is None or force_reload:
            print("🔄 Loading questions from database...")
            self._question_cache = self.db.get_all_questions()
            print(f"✅ Loaded {len(self._question_cache)} questions")
    
    def _filter_questions(self, questions: List[Dict],
                          difficulty: Optional[str] = None,
                          category: Optional[str] = None) -> List[Dict]:
        """Apply optional difficulty and category filters."""
        filtered = [q for q in questions if q]
        if difficulty:
            filtered = [q for q in filtered if q.get('difficulty') == difficulty]
        if category:
            filtered = [q for q in filtered if q.get('category') == category]
        return filtered

    def retrieve_questions(self, candidate_id: str,
                          max_questions: int = 15,
                          difficulty: Optional[str] = None,
                          category: Optional[str] = None,
                          randomize: bool = True) -> List[Dict]:
        """
        Retrieve personalized questions for candidate
        
        Args:
            candidate_id: Candidate identifier
            max_questions: Number of questions to return (5, 10, or 15)
            difficulty: Optional filter by difficulty
            category: Optional filter by category
            randomize: If True, sample randomly from top pool and shuffle order
        
        Returns:
            List of matched questions with similarity scores
        """
        print(f"🔄 Retrieving questions for candidate: {candidate_id}")
        print(f"   Requested count: {max_questions}")
        if category:
            print(f"   Category filter: {category}")
        if difficulty:
            print(f"   Difficulty filter: {difficulty}")
        if randomize:
            print(f"   Pool size: top {TOP_MATCH_POOL_SIZE}, then random sample + shuffle")

        profile = self.db.get_candidate_profile(candidate_id)
        if not profile:
            print(f"❌ Profile not found for: {candidate_id}")
            return []

        profile_vector = profile['profile_vector']

        try:
            validate_vector(profile_vector, "profile_vector")
        except ValueError as e:
            print(f"❌ Invalid profile vector: {e}")
            return []

        self._load_questions()
        questions = self._filter_questions(self._question_cache, difficulty, category)

        print(f"📊 Comparing with {len(questions)} questions after filters...")

        if not questions:
            print("❌ No questions match the selected filters")
            return []

        question_embeddings = [q['embedding'] for q in questions]
        similarities = batch_cosine_similarity(profile_vector, question_embeddings)

        scored_questions = []
        for q, sim in zip(questions, similarities):
            q_with_score = q.copy()
            q_with_score['similarity_score'] = round(sim, 4)
            scored_questions.append(q_with_score)

        scored_questions.sort(key=lambda x: x['similarity_score'], reverse=True)

        top_pool = scored_questions[:TOP_MATCH_POOL_SIZE]
        pick_count = min(max_questions, len(top_pool))

        if pick_count == 0:
            print("❌ No questions available in match pool")
            return []

        if randomize and len(top_pool) > pick_count:
            results = random.sample(top_pool, pick_count)
            random.shuffle(results)
        else:
            results = top_pool[:pick_count]
            if randomize:
                random.shuffle(results)

        print(f"✅ Selected {len(results)} questions (requested {max_questions})")
        if results:
            print(f"   Top pool score range: {top_pool[0]['similarity_score']:.4f} – {top_pool[-1]['similarity_score']:.4f}")

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
        
        # Get questions (stable top matches for dashboard recommendations)
        questions = self.retrieve_questions(
            candidate_id, max_questions=10, randomize=False
        )
        
        # Topic relevance: % of resume-matched questions that include each topic
        topic_question_counts = {}
        for q in questions:
            for topic in set(q.get('topics') or []):
                topic_question_counts[topic] = topic_question_counts.get(topic, 0) + 1

        total_matches = len(questions)
        recommended_topics = {}
        if total_matches:
            recommended_topics = {
                topic: round((count / total_matches) * 100, 1)
                for topic, count in sorted(
                    topic_question_counts.items(),
                    key=lambda item: item[1],
                    reverse=True,
                )
            }
        
        return {
            'candidate_id': candidate_id,
            'experience_level': metadata.get('experience_level', 'Unknown'),
            'primary_domain': metadata.get('primary_domain', 'Unknown'),
            'total_matches': total_matches,
            'top_questions': questions[:5],
            'recommended_topics': recommended_topics,
            'average_similarity': round(sum(q['similarity_score'] for q in questions) / len(questions), 4) if questions else 0
        }
