"""
Question Manager - Person C
Manages question database creation and updates
"""

import uuid
import json
import pandas as pd
from typing import Dict, List
from database import DatabaseManager
from utils import embedding_service
from utils.vector_operations import validate_vector


class QuestionManager:
    """Manage interview questions database"""
    
    def __init__(self):
        self.db = DatabaseManager()
    
    def add_question(self, question_text: str,
                    category: str,
                    difficulty: str,
                    topics: List[str],
                    job_roles: List[str],
                    ideal_keywords: List[str] = None) -> str:
        """
        Add single question with auto-generated embedding
        
        Args:
            question_text: The interview question
            category: 'technical'|'behavioral'|'situational'
            difficulty: 'easy'|'medium'|'hard'
            topics: List of relevant topics
            job_roles: List of relevant job roles
            ideal_keywords: Optional keywords for ideal answer
        
        Returns:
            question_id
        """
        print(f"🔄 Adding question: {question_text[:50]}...")
        
        # Generate embedding
        embedding = embedding_service.embed_text(question_text)
        
        # Validate
        try:
            validate_vector(embedding, "question_embedding")
        except ValueError as e:
            print(f"❌ Embedding validation failed: {e}")
            raise
        
        # Create question data
        question_data = {
            'question_text': question_text,
            'category': category,
            'difficulty': difficulty,
            'topics': topics,
            'job_roles': job_roles,
            'embedding': embedding,
            'ideal_keywords': ideal_keywords or []
        }
        
        # Insert to database
        question_id = self.db.insert_question(question_data)
        print(f"✅ Question added with ID: {question_id}")
        
        return question_id
    
    def bulk_add_questions(self, questions: List[Dict]) -> List[str]:
        """
        Add multiple questions efficiently
        13:30    Args:
        questions: List of question dicts (without embeddings)
    
        Returns:
            List of question_ids
        """
        print(f"🔄 Bulk adding {len(questions)} questions...")
        
        # Extract texts for batch embedding
        texts = [q['question_text'] for q in questions]
        
        # Generate all embeddings at once (faster)
        embeddings = embedding_service.embed_batch(texts)
        print(f"✅ Generated {len(embeddings)} embeddings")
        
        # Add embeddings to question dicts
        for q, emb in zip(questions, embeddings):
            q['embedding'] = emb
            if 'ideal_keywords' not in q:
                q['ideal_keywords'] = []
        
        # Bulk insert
        question_ids = self.db.bulk_insert_questions(questions)
        print(f"✅ Inserted {len(question_ids)} questions")
        
        return question_ids
    
    def load_questions_from_file(self, filepath: str) -> List[str]:
        """
        Load questions from JSON or CSV file
        
        Args:
            filepath: Path to file
        
        Returns:
            List of question_ids
        """
        if filepath.endswith('.json'):
            with open(filepath, 'r') as f:
                questions = json.load(f)
        elif filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
            questions = df.to_dict('records')
        else:
            raise ValueError("Unsupported file format. Use JSON or CSV")
        
        return self.bulk_add_questions(questions)
    

    def get_database_summary(self) -> Dict:
        """
        Get summary of question database
        
        Returns:
            Statistics dict
        """
        all_questions = self.db.get_all_questions()
        
        # Count by category
        categories = {}
        difficulties = {}
        topics = {}
        
        for q in all_questions:
            # Categories
            cat = q['category']
            categories[cat] = categories.get(cat, 0) + 1
            
            # Difficulties
            diff = q['difficulty']
            difficulties[diff] = difficulties.get(diff, 0) + 1
            
            # Topics
            for topic in q['topics']:
                topics[topic] = topics.get(topic, 0) + 1
        
        return {
            'total_questions': len(all_questions),
            'by_category': categories,
            'by_difficulty': difficulties,
            'top_topics': dict(sorted(topics.items(), key=lambda x: x[1], reverse=True)[:10])
        }

    def update_question(self, question_id: str, **kwargs) -> bool:
        """
        Update question properties
        Note: If question_text is updated, embedding will be regenerated
        
        Args:
            question_id: Question identifier
            **kwargs: Fields to update
        
        Returns:
            True if updated successfully
        """
        question = self.db.get_question_by_id(question_id)
        if not question:
            print(f"❌ Question not found: {question_id}")
            return False
        
        # If text changed, regenerate embedding
        if 'question_text' in kwargs:
            new_embedding = embedding_service.embed_text(kwargs['question_text'])
            kwargs['embedding'] = new_embedding
        
        # Update in database (would need additional DB method)
        # For now, delete and re-insert
        print(f"⚠️  Update functionality to be implemented")
        return False