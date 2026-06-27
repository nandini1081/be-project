"""
API Routes - Complete REST API
"""

from flask import Blueprint, request, jsonify
from sentence_transformers import SentenceTransformer
# Load model once (global)
from services import (
    ResumeParser,
    ProfileCreator,
    ProfileUpdater,
    QuestionManager,
    QuestionRetriever
)
from database import DatabaseManager
import os
import traceback

# Load model once (global)
model = SentenceTransformer("all-MiniLM-L6-v2")

def create_routes():
    """Create and configure all routes"""
    api = Blueprint('api', __name__)
    
    # Initialize services
    resume_parser = ResumeParser()
    profile_creator = ProfileCreator()
    profile_updater = ProfileUpdater()
    question_manager = QuestionManager()
    question_retriever = QuestionRetriever()
    db = DatabaseManager()
    
    # ==================== PERSON A ROUTES ====================
    
    @api.route('/parse-resume', methods=['POST'])
    def parse_resume():
        try:
            # CASE 1: Resume sent as JSON text
            if request.is_json:
                data = request.get_json()
                resume_text = data.get('resume_text')

                if not resume_text:
                    return jsonify({'error': 'resume_text missing'}), 400

                parsed = resume_parser.parse_resume(resume_text=resume_text)

            # CASE 2: Resume sent as PDF file
            elif 'pdf_file' in request.files:
                pdf_file = request.files['pdf_file']

                if not pdf_file or pdf_file.filename == '':
                    return jsonify({'error': 'No PDF file provided'}), 400

                parsed = resume_parser.parse_resume(pdf_file=pdf_file)

            else:
                return jsonify({'error': 'No resume provided'}), 400

            return jsonify({
                'success': True,
                'data': parsed
            })

        except Exception as e:
            return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500

    
    @api.route('/create-profile', methods=['POST'])
    def create_profile():
        """Create candidate profile with vector"""
        try:
            data = request.get_json()
            resume_data = data.get('resume_data')
            candidate_id = data.get('candidate_id')
            
            if not resume_data:
                return jsonify({'error': 'resume_data required'}), 400
            
            profile = profile_creator.create_profile(resume_data, candidate_id)
            
            # Don't return full vector (too large), just metadata
            return jsonify({
                'success': True,
                'candidate_id': profile['candidate_id'],
                'metadata': profile['metadata'],
                'vector_dimensions': len(profile['profile_vector'])
            })
        
        except Exception as e:
            return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500
    
    @api.route('/full-resume-processing', methods=['POST'])
    def full_resume_processing():
        """Complete pipeline: parse + create profile"""
        try:
            # ✅ CASE 1: PDF upload
            if 'pdf_file' in request.files:
                pdf_file = request.files['pdf_file']
                parsed = resume_parser.parse_resume(pdf_file=pdf_file)

                candidate_id = request.form.get('candidate_id')

            # ✅ CASE 2: JSON text
            elif request.is_json:
                data = request.get_json()

                if 'resume_text' not in data:
                    return jsonify({'error': 'resume_text required'}), 400

                parsed = resume_parser.parse_resume(resume_text=data['resume_text'])
                candidate_id = data.get('candidate_id')

            else:
                return jsonify({'error': 'No resume provided'}), 400

            # Create profile
            profile = profile_creator.create_profile(parsed, candidate_id)

            return jsonify({
                'success': True,
                'candidate_id': profile['candidate_id'],
                'parsed_data': {
                    'skills': parsed['skills'],
                    'experience_count': len(parsed['experience']),
                    'project_count': len(parsed['projects'])
                },
                'metadata': profile['metadata'],
                'vector_dimensions': len(profile['profile_vector'])
            })
        
        except Exception as e:
            return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500
    
    # ==================== PERSON B ROUTES ====================
    
    @api.route('/update-profile/<candidate_id>', methods=['POST'])
    def update_profile(candidate_id):
        """Update candidate profile"""
        try:
            updated = profile_updater.update_profile(candidate_id)
            
            if updated:
                return jsonify({
                    'success': True,
                    'candidate_id': candidate_id,
                    'version': updated['version'],
                    'metadata': updated['metadata']
                })
            else:
                return jsonify({'error': 'Update failed'}), 400
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @api.route('/record-response', methods=['POST'])
    def record_response():
        """Record interview response and update profile"""
        try:
            data = request.get_json()
            
            required = ['candidate_id', 'question_id', 'answer_text', 
                       'knowledge_score', 'speech_score']
            if not all(k in data for k in required):
                return jsonify({'error': f'Required fields: {required}'}), 400
            
            success = profile_updater.update_after_response(
                candidate_id=data['candidate_id'],
                question_id=data['question_id'],
                answer_text=data['answer_text'],
                knowledge_score=data['knowledge_score'],
                speech_score=data['speech_score'],
                interview_session_id=data.get('interview_session_id')
            )
            
            return jsonify({'success': success})
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @api.route('/analyze-speech', methods=['POST'])
    def analyze_speech():
        """Analyze answer audio and return speech score breakdown."""
        try:
            if 'audio_file' not in request.files:
                return jsonify({'error': 'audio_file required'}), 400

            audio_file = request.files['audio_file']
            if not audio_file.filename and not audio_file.content_length:
                return jsonify({'error': 'Empty audio upload'}), 400

            reference_text = request.form.get('reference_text', '')
            audio_bytes = audio_file.read()
            filename = audio_file.filename or 'answer.webm'
            suffix = os.path.splitext(filename)[1] or '.webm'

            from services.speech_analyzer import speech_analyzer
            result = speech_analyzer.analyze(audio_bytes, reference_text, suffix=suffix)

            return jsonify({
                'success': True,
                **result
            })

        except Exception as e:
            print("Speech analysis error:", traceback.format_exc())
            return jsonify({'error': str(e)}), 500
    
    @api.route('/performance-summary/<candidate_id>', methods=['GET'])
    def performance_summary(candidate_id):
        """Get performance summary"""
        try:
            summary = profile_updater.get_performance_summary(candidate_id)
            return jsonify(summary)
        
        except Exception as e:
            print("ERROR:", str(e))  # 👈 ADD THIS
            return jsonify({'error': str(e)}), 500
    
    # ==================== PERSON C ROUTES ====================
    
    @api.route('/add-question', methods=['POST'])
    def add_question():
        """Add single question"""
        try:
            data = request.get_json()
            
            required = ['question_text', 'category', 'difficulty', 'topics', 'job_roles']
            if not all(k in data for k in required):
                return jsonify({'error': f'Required fields: {required}'}), 400
            
            question_id = question_manager.add_question(
                question_text=data['question_text'],
                category=data['category'],
                difficulty=data['difficulty'],
                topics=data['topics'],
                job_roles=data['job_roles'],
                ideal_keywords=data.get('ideal_keywords')
            )
            
            return jsonify({
                'success': True,
                'question_id': question_id
            })
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @api.route('/bulk-add-questions', methods=['POST'])
    def bulk_add_questions():
        """Add multiple questions"""
        try:
            data = request.get_json()
            questions = data.get('questions', [])
            
            if not questions:
                return jsonify({'error': 'questions array required'}), 400
            
            question_ids = question_manager.bulk_add_questions(questions)
            
            return jsonify({
                'success': True,
                'count': len(question_ids),
                'question_ids': question_ids
            })
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @api.route('/database-summary', methods=['GET'])
    def database_summary():
        """Get question database summary"""
        try:
            summary = question_manager.get_database_summary()
            return jsonify(summary)
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # ==================== PERSON D ROUTES ====================
    
    @api.route('/retrieve-questions/<candidate_id>', methods=['GET'])
    def retrieve_questions(candidate_id):
        """Retrieve personalized questions"""
        try:
            # Get query parameters
            max_questions = request.args.get('max_questions', 15, type=int)
            difficulty = request.args.get('difficulty')
            category = request.args.get('category')
            
            questions = question_retriever.retrieve_questions(
                candidate_id=candidate_id,
                max_questions=max_questions,
                difficulty=difficulty,
                category=category,
                randomize=True
            )
            
            return jsonify({
                'success': True,
                'count': len(questions),
                'questions': questions
            })
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @api.route('/adaptive-questions/<candidate_id>', methods=['GET'])
    def adaptive_questions(candidate_id):
        """Get adaptive difficulty questions"""
        try:
            last_score = request.args.get('last_score', type=float)
            max_questions = request.args.get('max_questions', 5, type=int)
            
            questions = question_retriever.retrieve_adaptive_questions(
                candidate_id=candidate_id,
                last_score=last_score,
                max_questions=max_questions
            )
            
            return jsonify({
                'success': True,
                'count': len(questions),
                'questions': questions
            })
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @api.route('/diverse-questions/<candidate_id>', methods=['GET'])
    def diverse_questions(candidate_id):
        """Get diverse questions across categories"""
        try:
            per_category = request.args.get('per_category', 3, type=int)
            
            questions = question_retriever.get_diverse_questions(
                candidate_id=candidate_id,
                questions_per_category=per_category
            )
            
            return jsonify({
                'success': True,
                'count': len(questions),
                'questions': questions
            })
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @api.route('/recommendations/<candidate_id>', methods=['GET'])
    def recommendations(candidate_id):
        """Get question recommendations"""
        try:
            recommendations = question_retriever.get_question_recommendations(candidate_id)
            return jsonify(recommendations)
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # ==================== COMMON ROUTES ====================
    
    @api.route('/candidate/<candidate_id>', methods=['GET'])
    def get_candidate(candidate_id):
        """Get candidate profile"""
        try:
            profile = db.get_candidate_profile(candidate_id)
            resume = db.get_parsed_resume(candidate_id)
            
            if not profile:
                return jsonify({'error': 'Candidate not found'}), 404
            
            return jsonify({
                'profile': {
                    'candidate_id': profile['candidate_id'],
                    'metadata': profile['metadata'],
                    'version': profile['version'],
                    'created_at': profile['created_at'],
                    'updated_at': profile['updated_at']
                },
                'resume': resume
            })
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @api.route('/stats', methods=['GET'])
    def get_stats():
        """Get database statistics"""
        try:
            stats = db.get_database_stats()
            return jsonify(stats)
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @api.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'service': 'AI Interview System'
        })
    
    @api.route('/get-embedding', methods=['POST'])
    def get_embedding():
        data = request.get_json()
        text = data.get('text', '')

        embedding = model.encode(text, normalize_embeddings=True).tolist()

        return jsonify({
            "embedding": embedding
        })
    
    return api