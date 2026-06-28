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
        self._ensure_schema()
    
    def _ensure_schema(self):
        """Apply lightweight migrations for existing databases."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('PRAGMA table_info(interview_history)')
        columns = {row[1] for row in cursor.fetchall()}
        if 'interview_session_id' not in columns:
            cursor.execute(
                'ALTER TABLE interview_history ADD COLUMN interview_session_id TEXT'
            )
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_history_session '
                'ON interview_history(interview_session_id)'
            )
            conn.commit()

        cursor.execute('PRAGMA table_info(questions)')
        question_columns = {row[1] for row in cursor.fetchall()}
        if question_columns:
            if 'question_group' not in question_columns:
                cursor.execute(
                    'ALTER TABLE questions ADD COLUMN question_group TEXT'
                )
            if 'followup_order' not in question_columns:
                cursor.execute(
                    'ALTER TABLE questions ADD COLUMN followup_order INTEGER DEFAULT 1'
                )
            if 'parent_question_id' not in question_columns:
                cursor.execute(
                    'ALTER TABLE questions ADD COLUMN parent_question_id TEXT'
                )
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_question_group '
                'ON questions(question_group)'
            )
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_question_group_order '
                'ON questions(question_group, followup_order)'
            )
            conn.commit()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                candidate_id TEXT UNIQUE,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (candidate_id) REFERENCES candidate_profiles(candidate_id)
            )
        ''')
        cursor.execute(
            'CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)'
        )
        cursor.execute(
            'CREATE INDEX IF NOT EXISTS idx_users_candidate ON users(candidate_id)'
        )
        conn.commit()
        conn.close()
    
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
            SELECT 
                    ih.history_id,
                    ih.candidate_id,
                    ih.question_id,
                    q.question_text,
                    ih.answer_text,
                    ih.knowledge_score,
                    ih.speech_score,
                    ih.total_score,
                    ih.interview_session_id,
                    ih.timestamp
                FROM interview_history ih
                JOIN questions q 
                    ON ih.question_id = q.question_id
                WHERE ih.candidate_id = ?
                ORDER BY ih.timestamp DESC
                LIMIT ?
        ''', (candidate_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'history_id': row['history_id'],
            'candidate_id': row['candidate_id'],
            'question_id': row['question_id'],
            'question_text': row['question_text'],   # ✅ ADD THIS
            'answer_text': row['answer_text'],
            'knowledge_score': row['knowledge_score'],
            'speech_score': row['speech_score'],
            'total_score': row['total_score'],
            'interview_session_id': row['interview_session_id'],
            'timestamp': row['timestamp']
        } for row in rows]

    def _group_history_by_gap(self, history: List[Dict], gap_minutes: int = 30) -> List[List[Dict]]:
        """Legacy grouping for rows without interview_session_id."""
        if not history:
            return []

        sorted_asc = sorted(history, key=lambda h: h['timestamp'])
        sessions = [[sorted_asc[0]]]
        gap = timedelta(minutes=gap_minutes)

        for item in sorted_asc[1:]:
            prev_ts = datetime.fromisoformat(sessions[-1][-1]['timestamp'])
            curr_ts = datetime.fromisoformat(item['timestamp'])
            if curr_ts - prev_ts > gap:
                sessions.append([item])
            else:
                sessions[-1].append(item)

        return sessions

    def _group_history_into_sessions(self, history: List[Dict], gap_minutes: int = 30) -> List[List[Dict]]:
        """Group responses into interview sessions by session id, with gap fallback."""
        if not history:
            return []

        with_session_id = [h for h in history if h.get('interview_session_id')]
        without_session_id = [h for h in history if not h.get('interview_session_id')]

        sessions: List[List[Dict]] = []
        session_map: Dict[str, List[Dict]] = {}

        for item in with_session_id:
            sid = item['interview_session_id']
            session_map.setdefault(sid, []).append(item)

        for items in session_map.values():
            sessions.append(sorted(items, key=lambda h: h['timestamp']))

        if without_session_id:
            sessions.extend(self._group_history_by_gap(without_session_id, gap_minutes))

        sessions.sort(key=lambda s: s[-1]['timestamp'])
        return sessions

    def get_interview_sessions(self, candidate_id: str, limit: int = 10) -> List[Dict]:
        """Summarize recent interview sessions for dashboard display."""
        history = self.get_candidate_history(candidate_id, limit=500)
        sessions = self._group_history_into_sessions(history)
        summaries = []

        for index, session in enumerate(reversed(sessions), start=1):
            scores = [h['total_score'] for h in session]
            summaries.append({
                'session_number': len(sessions) - index + 1,
                'started_at': session[0]['timestamp'],
                'ended_at': session[-1]['timestamp'],
                'question_count': len(session),
                'avg_score': round(sum(scores) / len(scores), 2),
                'responses': session
            })

        return summaries[:limit]
    
    # ============================================================
    # PERSON C: DATABASE CREATION (QUESTIONS)
    # ============================================================
    
    def _parse_question_row(self, row) -> Dict:
        """Normalize a questions table row into a dict."""
        return {
            'question_id': row['question_id'],
            'question_text': row['question_text'],
            'category': row['category'],
            'difficulty': row['difficulty'],
            'topics': json.loads(row['topics']),
            'job_roles': json.loads(row['job_roles']),
            'embedding': json.loads(row['embedding']),
            'ideal_keywords': json.loads(row['ideal_keywords']),
            'ideal_answer_embedding': (
                json.loads(row['ideal_answer_embedding'])
                if row['ideal_answer_embedding']
                else None
            ),
            'question_group': row['question_group'],
            'followup_order': row['followup_order'] if row['followup_order'] is not None else 1,
            'parent_question_id': row['parent_question_id'],
            'created_at': row['created_at'],
        }

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
            INSERT INTO questions 
            (question_id, question_text, category, difficulty, topics, job_roles, embedding,
             ideal_keywords, ideal_answer_embedding, question_group, followup_order,
             parent_question_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            question_id,
            question_data['question_text'],
            question_data['category'],
            question_data['difficulty'],
            json.dumps(question_data['topics']),
            json.dumps(question_data['job_roles']),
            json.dumps(question_data['embedding']),
            json.dumps(question_data.get('ideal_keywords', [])),
            None,
            question_data.get('question_group'),
            question_data.get('followup_order', 1),
            question_data.get('parent_question_id'),
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
                INSERT INTO questions 
                (question_id, question_text, category, difficulty, topics, job_roles, embedding,
                 ideal_keywords, ideal_answer_embedding, question_group, followup_order,
                 parent_question_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                qid,
                q['question_text'],
                q['category'],
                q['difficulty'],
                json.dumps(q['topics']),
                json.dumps(q['job_roles']),
                json.dumps(q['embedding']),
                json.dumps(q.get('ideal_keywords', [])),
                None,
                q.get('question_group'),
                q.get('followup_order', 1),
                q.get('parent_question_id'),
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
        
        return [self._parse_question_row(row) for row in rows]
    
    def get_questions_by_group(self, question_group: str) -> List[Dict]:
        """Get all questions in a group ordered by followup_order."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM questions
            WHERE question_group = ?
            ORDER BY followup_order ASC
        ''', (question_group,))
        rows = cursor.fetchall()
        conn.close()
        return [self._parse_question_row(row) for row in rows]

    def get_next_followup_question(
        self, question_group: str, after_order: int, max_order: int = 4
    ) -> Optional[Dict]:
        """Get the next question in a cross-question chain."""
        next_order = after_order + 1
        if next_order > max_order:
            return None
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM questions
            WHERE question_group = ? AND followup_order = ?
            LIMIT 1
        ''', (question_group, next_order))
        row = cursor.fetchone()
        conn.close()
        return self._parse_question_row(row) if row else None
    
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
            return self._parse_question_row(row)
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
                              total_score: float,
                              interview_session_id: Optional[str] = None) -> int:
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
             speech_score, total_score, interview_session_id, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            candidate_id,
            question_id,
            answer_text,
            knowledge_score,
            speech_score,
            total_score,
            interview_session_id,
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

        history = self.get_candidate_history(candidate_id, limit=500)
        sessions = self._group_history_into_sessions(history)
        total_interviews = len(sessions)

        if sessions:
            session_avgs = [
                sum(h['total_score'] for h in session) / len(session)
                for session in sessions
            ]
            avg_total_score = round(sum(session_avgs) / len(session_avgs), 2)
        else:
            avg_total_score = 0
        
        return {
            'total_questions': row['total_questions'],
            'total_interviews': total_interviews,
            'avg_knowledge_score': round(row['avg_knowledge'], 2) if row['avg_knowledge'] else 0,
            'avg_speech_score': round(row['avg_speech'], 2) if row['avg_speech'] else 0,
            'avg_total_score': avg_total_score,
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

    # ============================================================
    # AUTH: USER ACCOUNTS
    # ============================================================

    def create_user(self, email: str, password_hash: str) -> Dict:
        """Create a new user account."""
        user_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (user_id, email, password_hash, candidate_id, created_at, updated_at)
            VALUES (?, ?, ?, NULL, ?, ?)
        ''', (user_id, email.lower().strip(), password_hash, now, now))
        conn.commit()
        conn.close()
        return {
            'user_id': user_id,
            'email': email.lower().strip(),
            'candidate_id': None,
            'created_at': now,
            'updated_at': now,
        }

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email.lower().strip(),))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def set_user_candidate_id(self, user_id: str, candidate_id: str) -> None:
        now = datetime.now().isoformat()
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users SET candidate_id = ?, updated_at = ? WHERE user_id = ?
        ''', (candidate_id, now, user_id))
        conn.commit()
        conn.close()