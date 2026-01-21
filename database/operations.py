"""
Complete database operations for all 4 team members
"""

import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

class DatabaseManager:
    """Centralized database operations"""
    
    def __init__(self, db_path='interview_system.db'):
        self.db_path = db_path
    
    def get_connection(self):
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Access columns by name
        return conn
    
    # ============================================================
    # PERSON A: CANDIDATE PROFILE VECTOR CREATION
    # ============================================================
    
    def insert_parsed_resume(self, candidate_id: str, resume_data: Dict) -> str:
        """
        Insert parsed resume data
        
        Args:
            candidate_id: Unique candidate identifier
            resume_data: Dict with keys: personal_info, skills, experience, 
                        projects, education, raw_text
        
        Returns:
            candidate_id
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO parsed_resumes VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            candidate_id,
            json.dumps(resume_data.get('personal_info', {})),
            json.dumps(resume_data.get('skills', [])),
            json.dumps(resume_data.get('experience', [])),
            json.dumps(resume_data.get('projects', [])),
            json.dumps(resume_data.get('education', [])),
            resume_data.get('raw_text', ''),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        return candidate_id
    
    def get_parsed_resume(self, candidate_id: str) -> Optional[Dict]:
        """Get parsed resume by candidate ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM parsed_resumes WHERE candidate_id = ?', 
                      (candidate_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'candidate_id': row['candidate_id'],
                'personal_info': json.loads(row['personal_info']),
                'skills': json.loads(row['skills']),
                'experience': json.loads(row['experience']),
                'projects': json.loads(row['projects']),
                'education': json.loads(row['education']),
                'raw_text': row['raw_text'],
                'created_at': row['created_at']
            }
        return None
    
    def insert_candidate_profile(self, candidate_id: str, 
                                 profile_vector: List[float], 
                                 metadata: Dict) -> str:
        """
        Insert initial candidate profile with vector
        
        Args:
            candidate_id: Unique identifier
            profile_vector: 384-dim normalized vector
            metadata: Dict with skills, experience_level, domain
        
        Returns:
            candidate_id
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT OR REPLACE INTO candidate_profiles 
            VALUES (?, ?, ?, 1, ?, ?)
        ''', (
            candidate_id,
            json.dumps(profile_vector),
            json.dumps(metadata),
            now,
            now
        ))
        
        conn.commit()
        conn.close()
        return candidate_id
    
    # ============================================================
    # PERSON B: PROFILE VECTOR UPDATION
    # ============================================================
    
    def get_candidate_profile(self, candidate_id: str) -> Optional[Dict]:
        """Get candidate profile with vector"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM candidate_profiles WHERE candidate_id = ?', 
                      (candidate_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'candidate_id': row['candidate_id'],
                'profile_vector': json.loads(row['profile_vector']),
                'metadata': json.loads(row['metadata']),
                'version': row['version'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            }
        return None
    
    def update_profile_vector(self, candidate_id: str, 
                            new_vector: List[float],
                            metadata: Optional[Dict] = None) -> bool:
        """
        Update candidate profile vector (after interview response)
        
        Args:
            candidate_id: Candidate identifier
            new_vector: Updated 384-dim normalized vector
            metadata: Optional updated metadata
        
        Returns:
            True if updated successfully
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if metadata:
            cursor.execute('''
                UPDATE candidate_profiles 
                SET profile_vector = ?, 
                    metadata = ?,
                    version = version + 1,
                    updated_at = ?
                WHERE candidate_id = ?
            ''', (
                json.dumps(new_vector),
                json.dumps(metadata),
                datetime.now().isoformat(),
                candidate_id
            ))
        else:
            cursor.execute('''
                UPDATE candidate_profiles 
                SET profile_vector = ?, 
                    version = version + 1,
                    updated_at = ?
                WHERE candidate_id = ?
            ''', (
                json.dumps(new_vector),
                datetime.now().isoformat(),
                candidate_id
            ))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def get_candidate_history(self, candidate_id: str, 
                            limit: int = 50) -> List[Dict]:
        """
        Get interview history for profile updates
        
        Args:
            candidate_id: Candidate identifier
            limit: Maximum number of records
        
        Returns:
            List of history records
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM interview_history 
            WHERE candidate_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (candidate_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'history_id': row['history_id'],
            'candidate_id': row['candidate_id'],
            'question_id': row['question_id'],
            'answer_text': row['answer_text'],
            'knowledge_score': row['knowledge_score'],
            'speech_score': row['speech_score'],
            'total_score': row['total_score'],
            'timestamp': row['timestamp']
        } for row in rows]
    
    # ============================================================
    # PERSON C: DATABASE CREATION (QUESTIONS)
    # ============================================================
    
    def insert_question(self, question_data: Dict) -> str:
        """
        Insert question with pre-computed embedding
        
        Args:
            question_data: Dict with keys:
                - question_text (str)
                - category (str): 'technical'|'behavioral'|'situational'
                - difficulty (str): 'easy'|'medium'|'hard'
                - topics (List[str])
                - job_roles (List[str])
                - embedding (List[float]): 384-dim vector
                - ideal_keywords (List[str], optional)
        
        Returns:
            question_id
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        question_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO questions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            question_id,
            question_data['question_text'],
            question_data['category'],
            question_data['difficulty'],
            json.dumps(question_data['topics']),
            json.dumps(question_data['job_roles']),
            json.dumps(question_data['embedding']),
            json.dumps(question_data.get('ideal_keywords', [])),
            now,
            now
        ))
        
        conn.commit()
        conn.close()
        return question_id
    
    def bulk_insert_questions(self, questions: List[Dict]) -> List[str]:
        """
        Bulk insert multiple questions (faster for large datasets)
        
        Args:
            questions: List of question_data dicts
        
        Returns:
            List of question_ids
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        question_ids = []
        now = datetime.now().isoformat()
        
        for q in questions:
            qid = str(uuid.uuid4())
            question_ids.append(qid)
            
            cursor.execute('''
                INSERT INTO questions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                qid,
                q['question_text'],
                q['category'],
                q['difficulty'],
                json.dumps(q['topics']),
                json.dumps(q['job_roles']),
                json.dumps(q['embedding']),
                json.dumps(q.get('ideal_keywords', [])),
                now,
                now
            ))
        
        conn.commit()
        conn.close()
        return question_ids
    
    def get_all_questions(self) -> List[Dict]:
        """Get ALL questions with embeddings (for retrieval system)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM questions')
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'question_id': row['question_id'],
            'question_text': row['question_text'],
            'category': row['category'],
            'difficulty': row['difficulty'],
            'topics': json.loads(row['topics']),
            'job_roles': json.loads(row['job_roles']),
            'embedding': json.loads(row['embedding']),
            'ideal_keywords': json.loads(row['ideal_keywords']),
            'created_at': row['created_at']
        } for row in rows]
    
    def get_questions_by_filter(self, category: Optional[str] = None,
                               difficulty: Optional[str] = None,
                               topic: Optional[str] = None) -> List[Dict]:
        """
        Get filtered questions
        
        Args:
            category: Filter by category
            difficulty: Filter by difficulty
            topic: Filter by topic (searches in topics JSON array)
        
        Returns:
            List of matching questions
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM questions WHERE 1=1'
        params = []
        
        if category:
            query += ' AND category = ?'
            params.append(category)
        
        if difficulty:
            query += ' AND difficulty = ?'
            params.append(difficulty)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        questions = [{
            'question_id': row['question_id'],
            'question_text': row['question_text'],
            'category': row['category'],
            'difficulty': row['difficulty'],
            'topics': json.loads(row['topics']),
            'job_roles': json.loads(row['job_roles']),
            'embedding': json.loads(row['embedding']),
            'ideal_keywords': json.loads(row['ideal_keywords'])
        } for row in rows]
        
        # Filter by topic if specified
        if topic:
            questions = [q for q in questions if topic in q['topics']]
        
        return questions
    
    # ============================================================
    # PERSON D: QUESTION RETRIEVAL
    # ============================================================
    
    def get_question_by_id(self, question_id: str) -> Optional[Dict]:
        """Get single question by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM questions WHERE question_id = ?', 
                      (question_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'question_id': row['question_id'],
                'question_text': row['question_text'],
                'category': row['category'],
                'difficulty': row['difficulty'],
                'topics': json.loads(row['topics']),
                'job_roles': json.loads(row['job_roles']),
                'embedding': json.loads(row['embedding']),
                'ideal_keywords': json.loads(row['ideal_keywords'])
            }
        return None
    
    def cache_retrieval_results(self, candidate_id: str,
                               question_ids: List[str],
                               similarity_scores: List[float],
                               expiry_minutes: int = 5) -> str:
        """
        Cache retrieval results for performance
        
        Args:
            candidate_id: Candidate identifier
            question_ids: Retrieved question IDs
            similarity_scores: Corresponding similarity scores
            expiry_minutes: Cache expiry time
        
        Returns:
            cache_id
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cache_id = str(uuid.uuid4())
        now = datetime.now()
        expires = now + timedelta(minutes=expiry_minutes)
        
        cursor.execute('''
            INSERT INTO retrieval_cache VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            cache_id,
            candidate_id,
            json.dumps(question_ids),
            json.dumps(similarity_scores),
            now.isoformat(),
            expires.isoformat()
        ))
        
        conn.commit()
        conn.close()
        return cache_id
    
    def get_cached_retrieval(self, candidate_id: str) -> Optional[Dict]:
        """Get cached retrieval results if not expired"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        cursor.execute('''
            SELECT * FROM retrieval_cache 
            WHERE candidate_id = ? AND expires_at > ?
            ORDER BY created_at DESC
            LIMIT 1
        ''', (candidate_id, now))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'cache_id': row['cache_id'],
                'candidate_id': row['candidate_id'],
                'question_ids': json.loads(row['retrieved_questions']),
                'similarity_scores': json.loads(row['similarity_scores']),
                'created_at': row['created_at']
            }
        return None
    
    # ============================================================
    # COMMON: INTERVIEW HISTORY (All team members use this)
    # ============================================================
    
    def add_interview_response(self, candidate_id: str,
                              question_id: str,
                              answer_text: str,
                              knowledge_score: float,
                              speech_score: float,
                              total_score: float) -> int:
        """
        Record interview response
        
        Args:
            candidate_id: Candidate identifier
            question_id: Question identifier
            answer_text: Candidate's answer
            knowledge_score: Content score (0-1)
            speech_score: Delivery score (0-1)
            total_score: Combined score (0-1)
        
        Returns:
            history_id
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO interview_history 
            (candidate_id, question_id, answer_text, knowledge_score, 
             speech_score, total_score, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            candidate_id,
            question_id,
            answer_text,
            knowledge_score,
            speech_score,
            total_score,
            datetime.now().isoformat()
        ))
        
        history_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return history_id
    
    def get_candidate_statistics(self, candidate_id: str) -> Dict:
        """Get performance statistics for a candidate"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_questions,
                AVG(knowledge_score) as avg_knowledge,
                AVG(speech_score) as avg_speech,
                AVG(total_score) as avg_total,
                MAX(total_score) as best_score,
                MIN(total_score) as worst_score
            FROM interview_history
            WHERE candidate_id = ?
        ''', (candidate_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        return {
            'total_questions': row['total_questions'],
            'avg_knowledge_score': round(row['avg_knowledge'], 2) if row['avg_knowledge'] else 0,
            'avg_speech_score': round(row['avg_speech'], 2) if row['avg_speech'] else 0,
            'avg_total_score': round(row['avg_total'], 2) if row['avg_total'] else 0,
            'best_score': round(row['best_score'], 2) if row['best_score'] else 0,
            'worst_score': round(row['worst_score'], 2) if row['worst_score'] else 0
        }
    
    # ============================================================
    # UTILITY FUNCTIONS
    # ============================================================
    
    def clear_expired_cache(self):
        """Remove expired cache entries"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        cursor.execute('DELETE FROM retrieval_cache WHERE expires_at <= ?', (now,))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        cursor.execute('SELECT COUNT(*) as count FROM questions')
        stats['total_questions'] = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM candidate_profiles')
        stats['total_candidates'] = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM interview_history')
        stats['total_responses'] = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM retrieval_cache')
        stats['cached_retrievals'] = cursor.fetchone()['count']
        
        conn.close()
        return stats