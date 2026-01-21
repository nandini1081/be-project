"""
Resume Parser - Person A
Extracts structured information from resume
"""

import re
import spacy
from typing import Dict, List
import PyPDF2
from io import BytesIO

class ResumeParser:
    """Parse resumes and extract structured data"""
    
    def __init__(self):
        """Initialize spaCy model"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("⚠️  Downloading spaCy model...")
            import os
            os.system("python -m spacy download en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")
        
        # Common skills keywords
        self.common_skills = {
            'Python', 'Java', 'JavaScript', 'C++', 'C#', 'Ruby', 'Go', 'Rust',
            'React', 'Angular', 'Vue', 'Node.js', 'Django', 'Flask', 'Spring',
            'Machine Learning', 'ML', 'AI', 'Deep Learning', 'NLP', 'Computer Vision',
            'SQL', 'MongoDB', 'PostgreSQL', 'MySQL', 'Redis', 'Elasticsearch',
            'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP', 'Git', 'CI/CD',
            'TensorFlow', 'PyTorch', 'Scikit-learn', 'Pandas', 'NumPy',
            'REST API', 'GraphQL', 'Microservices', 'Agile', 'Scrum'
        }
    
    def parse_pdf(self, pdf_file) -> str:
        """
        Extract text from PDF file
        
        Args:
            pdf_file: PDF file object or bytes
        
        Returns:
            Extracted text
        """
        try:
            if isinstance(pdf_file, bytes):
                pdf_file = BytesIO(pdf_file)
            
            reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            
            for page in reader.pages:
                text += page.extract_text()
            
            return text
        except Exception as e:
            print(f"❌ Error parsing PDF: {e}")
            return ""
    
    def extract_email(self, text: str) -> str:
        """Extract email address"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        return emails[0] if emails else ""
    
    def extract_phone(self, text: str) -> str:
        """Extract phone number"""
        phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phones = re.findall(phone_pattern, text)
        return phones[0] if phones else ""
    
    def extract_skills(self, text: str) -> List[str]:
        """
        Extract skills from text
        
        Args:
            text: Resume text
        
        Returns:
            List of identified skills
        """
        text_upper = text.upper()
        found_skills = []
        
        for skill in self.common_skills:
            if skill.upper() in text_upper:
                found_skills.append(skill)
        
        return list(set(found_skills))
    
    def extract_education(self, text: str) -> List[Dict]:
        """
        Extract education information
        
        Args:
            text: Resume text
        
        Returns:
            List of education entries
        """
        education = []
        
        # Common degree patterns
        degree_patterns = [
            r'(B\.?Tech|Bachelor|B\.?E\.?|B\.?S\.?|M\.?Tech|Master|M\.?S\.?|M\.?E\.?|PhD|Ph\.?D\.?)[\s\w]*',
            r'(Computer|Software|Electrical|Mechanical|Civil)[\s]+(Engineering|Science)'
        ]
        
        for pattern in degree_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                edu_entry = {
                    'degree': match.group(0).strip(),
                    'institution': '',
                    'year': ''
                }
                
                # Try to extract year near the degree
                year_pattern = r'(19|20)\d{2}'
                context = text[max(0, match.start()-100):min(len(text), match.end()+100)]
                years = re.findall(year_pattern, context)
                if years:
                    edu_entry['year'] = years[-1]
                
                education.append(edu_entry)
        
        return education[:3]  # Limit to 3 entries
    
    def extract_experience(self, text: str) -> List[Dict]:
        """
        Extract work experience
        
        Args:
            text: Resume text
        
        Returns:
            List of experience entries
        """
        experience = []
        
        # Look for common job title patterns
        job_titles = [
            'Software Engineer', 'Developer', 'Data Scientist', 'Analyst',
            'Manager', 'Intern', 'Consultant', 'Architect', 'Lead'
        ]
        
        doc = self.nlp(text)
        
        for ent in doc.ents:
            if ent.label_ == "ORG":
                # Found organization, create experience entry
                exp_entry = {
                    'company': ent.text,
                    'role': '',
                    'duration': '',
                    'description': ''
                }
                
                # Extract surrounding context for role and duration
                context = text[max(0, ent.start_char-200):min(len(text), ent.start_char+200)]
                
                # Find job title
                for title in job_titles:
                    if title.lower() in context.lower():
                        exp_entry['role'] = title
                        break
                
                # Find year range
                year_pattern = r'(19|20)\d{2}\s*[-–]\s*(19|20)\d{2}|(19|20)\d{2}\s*[-–]\s*Present'
                years = re.search(year_pattern, context, re.IGNORECASE)
                if years:
                    exp_entry['duration'] = years.group(0)
                
                if exp_entry['role']:  # Only add if we found a role
                    experience.append(exp_entry)
        
        return experience[:5]  # Limit to 5 entries
    
    def extract_projects(self, text: str) -> List[Dict]:
        """
        Extract project information
        
        Args:
            text: Resume text
        
        Returns:
            List of project entries
        """
        projects = []
        
        # Look for "Project" keyword
        project_pattern = r'(?:Project|PROJECT)[\s:]*([^\n]+)'
        matches = re.finditer(project_pattern, text)
        
        for match in matches:
            project_name = match.group(1).strip()
            
            # Extract technologies from surrounding context
            context_start = match.start()
            context_end = min(len(text), match.end() + 300)
            context = text[context_start:context_end]
            
            technologies = []
            for skill in self.common_skills:
                if skill.upper() in context.upper():
                    technologies.append(skill)
            
            projects.append({
                'name': project_name[:100],  # Limit length
                'technologies': technologies[:10],  # Limit to 10 techs
                'description': context[:200]  # Limit description
            })
        
        return projects[:5]  # Limit to 5 projects
    
    def parse_resume(self, resume_text: str = None, pdf_file=None) -> Dict:
        """
        Main parsing function
        
        Args:
            resume_text: Plain text resume (optional)
            pdf_file: PDF file object (optional)
        
        Returns:
            Structured resume data
        """
        # Get text
        if pdf_file:
            text = self.parse_pdf(pdf_file)
        elif resume_text:
            text = resume_text
        else:
            raise ValueError("Either resume_text or pdf_file must be provided")
        
        if not text:
            raise ValueError("Could not extract text from resume")
        
        # Extract all components
        parsed_data = {
            'personal_info': {
                'name': '',  # Can be extracted with more sophisticated NER
                'email': self.extract_email(text),
                'phone': self.extract_phone(text)
            },
            'skills': self.extract_skills(text),
            'experience': self.extract_experience(text),
            'projects': self.extract_projects(text),
            'education': self.extract_education(text),
            'raw_text': text
        }
        
        return parsed_data