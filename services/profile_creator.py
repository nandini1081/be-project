"""
Profile Creator - Person A
Creates candidate profile vector from parsed resume
"""

import uuid
from typing import Dict, List
from database import DatabaseManager
from utils.embedding_service import embedding_service
from utils.vector_operations import validate_vector
from config import VECTOR_DIMENSION


class ProfileCreator:
    """Create candidate profile vectors"""
    
    def __init__(self):
        self.db = DatabaseManager()
    
    def create_metadata(self, resume_data: Dict) -> Dict:
        """
        Create metadata from resume data
        
        Args:
            resume_data: Parsed resume
        
        Returns:
            Metadata dict
        """
        # Determine experience level
        exp_count = len(resume_data.get('experience', []))
        if exp_count == 0:
            exp_level = 'Fresher'
        elif exp_count <= 2:
            exp_level = 'Junior'
        elif exp_count <= 4:
            exp_level = 'Mid'
        else:
            exp_level = 'Senior'
        
        # Determine primary domain from skills
        skills = resume_data.get('skills', [])
        domains = {
            'Machine Learning': ['Machine Learning', 'ML', 'AI', 'Deep Learning', 'TensorFlow', 'PyTorch'],
            'Web Development': ['React', 'Angular', 'Vue', 'Node.js', 'Django', 'Flask'],
            'Data Science': ['Pandas', 'NumPy', 'SQL', 'Data Analysis'],
            'Cloud/DevOps': ['AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes'],
            'Backend': ['Java', 'Spring', 'Microservices', 'REST API']
        }
        
        domain_scores = {}
        for domain, keywords in domains.items():
            score = sum(1 for skill in skills if skill in keywords)
            if score > 0:
                domain_scores[domain] = score
        
        primary_domain = max(domain_scores, key=domain_scores.get) if domain_scores else 'General'
        
        return {
            'skills': skills,
            'experience_level': exp_level,
            'primary_domain': primary_domain,
            'total_projects': len(resume_data.get('projects', [])),
            'total_experience': exp_count
        }
    
    def create_profile(self, resume_data: Dict, candidate_id: str = None) -> Dict:
        """
        Create complete candidate profile with vector
        
        Args:
            resume_data: Parsed resume data
            candidate_id: Optional candidate ID (auto-generated if not provided)
        
        Returns:
            Dict with candidate_id, profile_vector, metadata
        """
        if not candidate_id:
            candidate_id = str(uuid.uuid4())
        
        print(f"🔄 Creating profile for candidate: {candidate_id}")
        
        # Step 1: Save parsed resume
        self.db.insert_parsed_resume(candidate_id, resume_data)
        print("✅ Parsed resume saved")
        
        # Step 2: Generate embedding vector
        profile_vector = embedding_service.embed_resume(resume_data)
        
        # Validate vector
        try:
            validate_vector(profile_vector, "profile_vector")
            print(f"✅ Profile vector created ({VECTOR_DIMENSION} dimensions)")
        except ValueError as e:
            print(f"❌ Vector validation failed: {e}")
            raise
        
        # Step 3: Create metadata
        metadata = self.create_metadata(resume_data)
        print(f"✅ Metadata created: {metadata['experience_level']} {metadata['primary_domain']}")
        
        # Step 4: Save to database
        self.db.insert_candidate_profile(candidate_id, profile_vector, metadata)
        print("✅ Profile saved to database")
        
        return {
            'candidate_id': candidate_id,
            'profile_vector': profile_vector,
            'metadata': metadata
        }
    
    def get_or_create_profile(self, resume_data: Dict, candidate_id: str = None) -> Dict:
        """
        Get existing profile or create new one
        
        Args:
            resume_data: Parsed resume data
            candidate_id: Optional candidate ID
        
        Returns:
            Profile dict
        """
        if candidate_id:
            # Check if profile exists
            existing = self.db.get_candidate_profile(candidate_id)
            if existing:
                print(f"ℹ️  Found existing profile for: {candidate_id}")
                return existing
        
        # Create new profile
        return self.create_profile(resume_data, candidate_id)