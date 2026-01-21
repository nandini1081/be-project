"""
Generate sample data for testing
Run: python -m database.sample_data
"""

from database.operations import DatabaseManager
import numpy as np

def generate_sample_data():
    """Generate sample questions and candidate for testing"""
    db = DatabaseManager()
    
    print("🔄 Generating sample data...")
    
    # Sample questions
    sample_questions = [
        {
            'question_text': 'Explain the difference between supervised and unsupervised learning.',
            'category': 'technical',
            'difficulty': 'medium',
            'topics': ['Machine Learning', 'AI'],
            'job_roles': ['Data Scientist', 'ML Engineer'],
            'embedding': np.random.rand(384).tolist(),  # Random for demo
            'ideal_keywords': ['supervised', 'labeled', 'unsupervised', 'clustering']
        },
        {
            'question_text': 'Tell me about a time you faced a difficult challenge in a project.',
            'category': 'behavioral',
            'difficulty': 'easy',
            'topics': ['Problem Solving', 'Teamwork'],
            'job_roles': ['Software Engineer', 'Product Manager'],
            'embedding': np.random.rand(384).tolist(),
            'ideal_keywords': ['challenge', 'solution', 'teamwork']
        },
        {
            'question_text': 'How would you optimize a slow database query?',
            'category': 'technical',
            'difficulty': 'hard',
            'topics': ['Databases', 'SQL', 'Optimization'],
            'job_roles': ['Backend Engineer', 'Database Administrator'],
            'embedding': np.random.rand(384).tolist(),
            'ideal_keywords': ['indexing', 'query plan', 'normalization']
        }
    ]
    
    question_ids = db.bulk_insert_questions(sample_questions)
    print(f"✅ Inserted {len(question_ids)} sample questions")
    
    # Sample candidate
    candidate_id = 'test-candidate-001'
    resume_data = {
        'personal_info': {'name': 'John Doe', 'email': 'john@example.com'},
        'skills': ['Python', 'Machine Learning', 'SQL', 'Flask'],
        'experience': [
            {
                'company': 'Tech Corp',
                'role': 'Software Engineer',
                'duration': '2021-2023',
                'description': 'Built ML models for recommendation system'
            }
        ],
        'projects': [
            {
                'name': 'ChatBot Project',
                'technologies': ['Python', 'NLP', 'Flask'],
                'description': 'Built an AI chatbot using transformers'
            }
        ],
        'education': [
            {
                'degree': 'B.Tech Computer Engineering',
                'institution': 'PICT',
                'year': '2021'
            }
        ],
        'raw_text': 'Python Machine Learning SQL Flask Software Engineer...'
    }
    
    db.insert_parsed_resume(candidate_id, resume_data)
    print(f"✅ Inserted sample candidate: {candidate_id}")
    
    # Sample profile vector
    profile_vector = np.random.rand(384).tolist()
    metadata = {
        'skills': ['Python', 'ML'],
        'experience_level': 'Mid',
        'primary_domain': 'Machine Learning'
    }
    
    db.insert_candidate_profile(candidate_id, profile_vector, metadata)
    print(f"✅ Created profile vector for: {candidate_id}")
    
    # Sample interview response
    db.add_interview_response(
        candidate_id=candidate_id,
        question_id=question_ids[0],
        answer_text='Supervised learning uses labeled data...',
        knowledge_score=0.85,
        speech_score=0.75,
        total_score=0.80
    )
    print(f"✅ Added sample interview response")
    
    # Show stats
    stats = db.get_database_stats()
    print("\n📊 Database Statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")

if __name__ == "__main__":
    generate_sample_data()