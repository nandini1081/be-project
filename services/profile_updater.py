"""
Profile Updater - Person B
Updates candidate profile based on interview performance
"""

from typing import Dict, List, Optional
from database import DatabaseManager
from utils.embedding_service import embedding_service
from utils.vector_operations import weighted_vector_update, validate_vector
from config import UPDATE_OLD_WEIGHT, UPDATE_NEW_WEIGHT, HISTORY_LIMIT

class ProfileUpdater:
    """Update candidate profiles based on interview history"""
    
    def __init__(self):
        self.db = DatabaseManager()
    
    def calculate_performance_vector(self, history: List[Dict]) -> List[float]:
        """
        Calculate performance-weighted vector from history
        
        Args:
            history: List of interview responses
        
        Returns:
            Performance vector
        """
        if not history:
            return None
        
        # Get recent high-performing questions
        high_performers = [h for h in history if h['total_score'] >= 0.7]
        
        if not high_performers:
            return None
        
        # Get question texts
        question_texts = []
        for h in high_performers[:10]:  # Top 10 recent
            question = self.db.get_question_by_id(h['question_id'])
            if question:
                question_texts.append(question['question_text'])
        
        if not question_texts:
            return None
        
        # Create embedding from successful questions
        combined_text = ' '.join(question_texts)
        return embedding_service.embed_text(combined_text)
    
    def update_profile(self, candidate_id: str, 
                      force_recalculate: bool = False) -> Optional[Dict]:
        """
        Update candidate profile based on interview history
        
        Args:
            candidate_id: Candidate identifier
            force_recalculate: Force recalculation even if no new history
        
        Returns:
            Updated profile or None if no update needed
        """
        print(f"🔄 Updating profile for: {candidate_id}")
        
        # Get current profile
        profile = self.db.get_candidate_profile(candidate_id)
        if not profile:
            print(f"❌ Profile not found for: {candidate_id}")
            return None
        
        # Get interview history
        history = self.db.get_candidate_history(candidate_id, limit=HISTORY_LIMIT)
        
        if not history:
            print("ℹ️  No interview history found, no update needed")
            return profile
        
        print(f"📊 Found {len(history)} interview responses")
        
        # Calculate performance vector
        perf_vector = self.calculate_performance_vector(history)
        
        if perf_vector is None:
            print("ℹ️  Not enough high-performing responses for update")
            return profile
        
        # Get current vector
        old_vector = profile['profile_vector']
        
        # Calculate updated vector
        new_vector = weighted_vector_update(
            old_vector,
            perf_vector,
            old_weight=UPDATE_OLD_WEIGHT,
            new_weight=UPDATE_NEW_WEIGHT
        )
        
        # Validate
        try:
            validate_vector(new_vector, "updated_vector")
        except ValueError as e:
            print(f"❌ Updated vector validation failed: {e}")
            return None
        
        # Update metadata with latest stats
        stats = self.db.get_candidate_statistics(candidate_id)
        metadata = profile['metadata']
        metadata['avg_score'] = stats['avg_total_score']
        metadata['total_interviews'] = stats['total_questions']
        
        # Save updated vector
        success = self.db.update_profile_vector(candidate_id, new_vector, metadata)
        
        if success:
            print(f"✅ Profile updated (version {profile['version'] + 1})")
            return {
                'candidate_id': candidate_id,
                'profile_vector': new_vector,
                'metadata': metadata,
                'version': profile['version'] + 1
            }
        else:
            print("❌ Failed to update profile")
            return None
    
    def update_after_response(self, candidate_id: str,
                            question_id: str,
                            answer_text: str,
                            knowledge_score: float,
                            speech_score: float) -> bool:
        """
        Record response and trigger profile update
        
        Args:
            candidate_id: Candidate identifier
            question_id: Question identifier
            answer_text: Candidate's answer
            knowledge_score: Content score (0-1)
            speech_score: Delivery score (0-1)
        
        Returns:
            True if successfully recorded and updated
        """
        from config import KNOWLEDGE_WEIGHT, SPEECH_WEIGHT
        
        # Calculate total score
        total_score = (knowledge_score * KNOWLEDGE_WEIGHT + 
                      speech_score * SPEECH_WEIGHT)
        
        # Record response
        history_id = self.db.add_interview_response(
            candidate_id=candidate_id,
            question_id=question_id,
            answer_text=answer_text,
            knowledge_score=knowledge_score,
            speech_score=speech_score,
            total_score=total_score
        )
        
        print(f"✅ Response recorded (ID: {history_id}, Score: {total_score:.2f})")
        
        # Trigger profile update (async in production)
        updated_profile = self.update_profile(candidate_id)
        
        return updated_profile is not None
    
    def get_performance_summary(self, candidate_id: str) -> Dict:
        """
        Get performance summary for candidate
        
        Args:
            candidate_id: Candidate identifier
        
        Returns:
            Performance statistics
        """
        stats = self.db.get_candidate_statistics(candidate_id)
        history = self.db.get_candidate_history(candidate_id, limit=10)
        
        # Calculate trends
        if len(history) >= 5:
            recent_scores = [h['total_score'] for h in history[:5]]
            older_scores = [h['total_score'] for h in history[5:10]] if len(history) > 5 else []
            
            recent_avg = sum(recent_scores) / len(recent_scores)
            older_avg = sum(older_scores) / len(older_scores) if older_scores else recent_avg
            
            trend = "improving" if recent_avg > older_avg else "declining" if recent_avg < older_avg else "stable"
        else:
            trend = "insufficient_data"
        
        return {
            **stats,
            'trend': trend,
            'recent_responses': len(history)
        }