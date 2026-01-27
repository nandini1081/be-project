"""
Main Flask Application
"""

from flask import Flask, jsonify, send_from_directory
from routes import create_routes
from database import DatabaseManager
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
def create_app():
    """Create and configure Flask app"""
    app = Flask(
        __name__,
        static_folder=FRONTEND_DIR,
        static_url_path=""
    )
    
    # Configuration
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    app.config['JSON_SORT_KEYS'] = False
    
    # Initialize database
    db_path = os.getenv('DATABASE_PATH', 'interview_system.db')
    if not os.path.exists(db_path):
        print("🔄 Initializing database...")
        from database.init_db import init_database
        init_database(db_path)
    
    # Register routes
    api_routes = create_routes()
    app.register_blueprint(api_routes, url_prefix='/api')
    
    # Root endpoint
    @app.route('/')
    def index():
        return send_from_directory(FRONTEND_DIR, "index.html")
        return jsonify({
            'service': 'AI Interview Preparation System',
            'version': '1.0.0',
            'endpoints': {
                'health': '/api/health',
                'stats': '/api/stats',
                'parse_resume': '/api/parse-resume [POST]',
                'create_profile': '/api/create-profile [POST]',
                'retrieve_questions': '/api/retrieve-questions/<candidate_id> [GET]',
                'record_response': '/api/record-response [POST]',
                'add_question': '/api/add-question [POST]'
            }
        })
    
    @app.route("/<path:path>")
    def serve_static(path):
        return send_from_directory(FRONTEND_DIR, path)

    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    print("\n🚀 Starting AI Interview System...")
    print("📝 API Documentation available at: http://localhost:5000/")
    app.run(debug=True, host='0.0.0.0', port=5000)