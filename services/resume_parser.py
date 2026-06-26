"""
Resume Parser - Person A
Extracts structured information from resume
"""

import re
import spacy
from typing import Dict, List, Set
import PyPDF2
from io import BytesIO


class ResumeParser:
    """Parse resumes and extract structured data"""

    SECTION_ALIASES = {
        'TECHNICAL SKILLS': 'SKILLS',
        'CORE SKILLS': 'SKILLS',
        'KEY SKILLS': 'SKILLS',
        'PROJECT': 'PROJECTS',
        'ACADEMIC PROJECTS': 'PROJECTS',
        'PERSONAL PROJECTS': 'PROJECTS',
        'WORK EXPERIENCE': 'EXPERIENCE',
        'PROFESSIONAL EXPERIENCE': 'EXPERIENCE',
        'EMPLOYMENT': 'EXPERIENCE',
    }

    def __init__(self):
        """Initialize spaCy model"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("⚠️  Downloading spaCy model...")
            import os
            os.system("python -m spacy download en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")

        self.common_skills = {
            'Python', 'Java', 'JavaScript', 'C++', 'C#', 'Ruby', 'Go', 'Rust',
            'React', 'Angular', 'Vue', 'Node.js', 'Django', 'Flask', 'Spring',
            'Machine Learning', 'ML', 'AI', 'Deep Learning', 'NLP', 'Computer Vision',
            'SQL', 'MongoDB', 'PostgreSQL', 'MySQL', 'Redis', 'Elasticsearch',
            'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP', 'Git', 'CI/CD',
            'TensorFlow', 'PyTorch', 'Scikit-learn', 'Pandas', 'NumPy',
            'REST API', 'GraphQL', 'Microservices', 'Agile', 'Scrum'
        }

        self._skill_patterns = {
            skill: self._compile_skill_pattern(skill)
            for skill in self.common_skills
        }
        self._skills_by_length = sorted(self.common_skills, key=len, reverse=True)

    def _compile_skill_pattern(self, skill: str) -> re.Pattern:
        """Build a regex that matches whole skill tokens, not substrings."""
        escaped = re.escape(skill)
        if skill in ('C++', 'C#'):
            pattern = rf'(?<![A-Za-z0-9]){escaped}(?![A-Za-z0-9+#])'
        elif '.' in skill or '/' in skill or '+' in skill:
            pattern = rf'(?<![A-Za-z0-9]){escaped}(?![A-Za-z0-9])'
        else:
            pattern = rf'\b{escaped}\b'
        return re.compile(pattern, re.IGNORECASE)

    def _skill_in_text(self, skill: str, text: str) -> bool:
        return bool(self._skill_patterns[skill].search(text))

    def _find_skills_in_text(self, text: str) -> List[str]:
        found = []
        seen: Set[str] = set()

        for skill in self._skills_by_length:
            if self._skill_in_text(skill, text):
                key = skill.lower()
                if key not in seen:
                    seen.add(key)
                    found.append(skill)

        return found

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
        sections = self.split_sections(text)
        skills_text = sections.get('SKILLS', text)
        return self._find_skills_in_text(skills_text)

    def extract_education(self, text: str) -> List[Dict]:
        """
        Extract education information

        Args:
            text: Resume text

        Returns:
            List of education entries
        """
        education = []

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

                year_pattern = r'(19|20)\d{2}'
                context = text[max(0, match.start()-100):min(len(text), match.end()+100)]
                years = re.findall(year_pattern, context)
                if years:
                    edu_entry['year'] = years[-1]

                education.append(edu_entry)

        return education[:3]

    def extract_experience(self, text: str) -> List[Dict]:
        """
        Extract work experience

        Args:
            text: Resume text

        Returns:
            List of experience entries
        """
        experience = []

        job_titles = [
            'Software Engineer', 'Developer', 'Data Scientist', 'Analyst',
            'Manager', 'Intern', 'Consultant', 'Architect', 'Lead'
        ]

        doc = self.nlp(text)

        for ent in doc.ents:
            if ent.label_ == "ORG":
                exp_entry = {
                    'company': ent.text,
                    'role': '',
                    'duration': '',
                    'description': ''
                }

                context = text[max(0, ent.start_char-200):min(len(text), ent.start_char+200)]

                for title in job_titles:
                    if title.lower() in context.lower():
                        exp_entry['role'] = title
                        break

                year_pattern = r'(19|20)\d{2}\s*[-–]\s*(19|20)\d{2}|(19|20)\d{2}\s*[-–]\s*Present'
                years = re.search(year_pattern, context, re.IGNORECASE)
                if years:
                    exp_entry['duration'] = years.group(0)

                if exp_entry['role']:
                    experience.append(exp_entry)

        return experience[:5]

    def split_sections(self, text: str) -> Dict[str, str]:
        section_titles = [
            'EDUCATION', 'TECHNICAL SKILLS', 'CORE SKILLS', 'KEY SKILLS', 'SKILLS',
            'ACADEMIC PROJECTS', 'PERSONAL PROJECTS', 'PROJECTS', 'PROJECT',
            'WORK EXPERIENCE', 'PROFESSIONAL EXPERIENCE', 'EXPERIENCE', 'EMPLOYMENT',
            'ACHIEVEMENTS', 'EXTRA-CURRICULAR ACTIVITIES', 'LEADERSHIP',
            'CERTIFICATIONS', 'PUBLICATIONS'
        ]

        titles_sorted = sorted(section_titles, key=len, reverse=True)
        pattern = (
            r'(?im)^(?P<header>' +
            '|'.join(re.escape(title) for title in titles_sorted) +
            r')\s*:?\s*$'
        )
        matches = list(re.finditer(pattern, text))

        sections = {}

        for i, match in enumerate(matches):
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

            section_name = match.group('header').upper().strip()
            section_name = self.SECTION_ALIASES.get(section_name, section_name)
            section_content = text[start:end].strip()

            if section_name not in sections or len(section_content) > len(sections[section_name]):
                sections[section_name] = section_content

        return sections

    PROJECT_LABEL_BLACKLIST = {
        'languages', 'language', 'tools', 'tool', 'technologies', 'technology',
        'tech stack', 'frameworks', 'framework', 'skills', 'skill',
        'duration', 'role', 'responsibilities', 'description', 'platform',
        'database', 'features', 'key features', 'environment', 'libraries',
        'stack', 'frontend', 'backend', 'summary',
    }

    PROJECT_TITLE_VERBS = {
        'built', 'developed', 'implemented', 'created', 'designed', 'used',
        'worked', 'developed', 'deployed', 'maintained', 'integrated',
    }

    def _normalize_heading(self, line: str) -> str:
        return re.sub(r'\s+', ' ', line.strip().lower().rstrip(':'))

    def _is_label_line(self, line: str) -> bool:
        normalized = self._normalize_heading(line)
        if normalized in self.PROJECT_LABEL_BLACKLIST:
            return True
        return bool(re.match(
            r'^(languages?|tools?|technologies?|skills?|frameworks?|stack)\b',
            normalized
        ))

    def _clean_project_line(self, line: str) -> str:
        line = line.strip()
        line = re.sub(r'^[-•●▪◦*]\s+', '', line)
        line = re.sub(r'^\d+[\.)]\s+', '', line)
        line = re.sub(r'^\*\*(.+?)\*\*$', r'\1', line)
        return line.strip()

    def _ner_validates_project_title(self, title: str) -> bool:
        """Use spaCy POS/NER to check if text looks like a project name."""
        title = title.strip()
        if len(title) < 3 or len(title.split()) > 10:
            return False
        if self._is_label_line(title):
            return False
        if title.split()[0].lower() in self.PROJECT_TITLE_VERBS:
            return False

        doc = self.nlp(title)
        if not doc:
            return False

        if any(ent.label_ in ('WORK_OF_ART', 'PRODUCT') for ent in doc.ents):
            return True

        has_noun = any(token.pos_ in ('NOUN', 'PROPN') for token in doc)
        starts_with_verb = doc[0].pos_ == 'VERB'
        mostly_nouns = sum(1 for t in doc if t.pos_ in ('NOUN', 'PROPN', 'ADJ')) >= max(1, len(doc) // 2)

        return has_noun and not starts_with_verb and mostly_nouns

    def _looks_like_project_title_line(self, line: str) -> bool:
        """High-confidence project title line: bullet, number, or Title: description."""
        stripped = line.strip()
        if not stripped or self._is_label_line(stripped):
            return False

        if re.match(r'^[-•●▪◦*]\s+\S', stripped):
            return True
        if re.match(r'^\d+[\.)]\s+\S', stripped):
            return True

        colon_match = re.match(r'^(.+?):\s*(\S.*)?$', stripped)
        if colon_match:
            title = colon_match.group(1).strip()
            if len(title.split()) > 8 or len(title) < 3:
                return False
            return self._ner_validates_project_title(title)

        return False

    def _split_by_blank_lines(self, project_text: str) -> List[str]:
        return [
            block.strip()
            for block in re.split(r'\n\s*\n+', project_text)
            if len(block.strip()) >= 20
        ]

    def _split_by_bullets_or_numbers(self, project_text: str) -> List[str]:
        lines = project_text.split('\n')
        entries: List[str] = []
        current: List[str] = []

        def flush():
            if current:
                block = '\n'.join(current).strip()
                if len(block) >= 20:
                    entries.append(block)
                current.clear()

        for line in lines:
            stripped = line.strip()
            if not stripped:
                flush()
                continue

            if self._looks_like_project_title_line(stripped) and (
                re.match(r'^[-•●▪◦*]\s+', stripped) or re.match(r'^\d+[\.)]\s+', stripped)
            ):
                flush()
                current.append(self._clean_project_line(stripped))
            else:
                current.append(stripped)

        flush()
        return entries

    def _split_by_colon_titles(self, project_text: str) -> List[str]:
        lines = [line.strip() for line in project_text.split('\n') if line.strip()]
        entries: List[str] = []
        current: List[str] = []

        for line in lines:
            if self._looks_like_project_title_line(line) and ':' in line and current:
                entries.append('\n'.join(current))
                current = [line]
            else:
                current.append(line)

        if current:
            entries.append('\n'.join(current))

        return [entry.strip() for entry in entries if len(entry.strip()) >= 20]

    def _score_project_entries(self, entries: List[str]) -> float:
        if not entries:
            return 0.0

        validated = 0
        for entry in entries:
            title = self._extract_project_name(entry)
            if self._ner_validates_project_title(title):
                validated += 1

        over_split_penalty = max(0, len(entries) - 6) * 1.5
        invalid_penalty = (len(entries) - validated) * 2.0
        return validated * 3.0 - over_split_penalty - invalid_penalty

    def _choose_project_entries(self, project_text: str) -> List[str]:
        strategies = [
            self._split_by_blank_lines,
            self._split_by_bullets_or_numbers,
            self._split_by_colon_titles,
        ]

        best_entries: List[str] = []
        best_score = float('-inf')

        for strategy in strategies:
            entries = strategy(project_text)
            score = self._score_project_entries(entries)
            if score > best_score:
                best_score = score
                best_entries = entries

        if best_entries:
            return best_entries

        trimmed = project_text.strip()
        if len(trimmed) >= 20:
            return [trimmed]
        return []

    def _extract_project_name(self, entry: str) -> str:
        first_line = self._clean_project_line(entry.split('\n', 1)[0].strip())

        colon_match = re.match(r'^(.+?):\s*(.*)$', first_line)
        if colon_match:
            title = colon_match.group(1).strip()
            if self._ner_validates_project_title(title):
                return title[:100]

        doc = self.nlp(first_line)
        noun_chunks = list(doc.noun_chunks)
        if noun_chunks:
            chunk = noun_chunks[0].text.strip()
            if len(chunk) >= 3 and self._ner_validates_project_title(chunk):
                return chunk[:100]

        if self._ner_validates_project_title(first_line):
            return first_line[:100]

        title_tokens = [
            token.text for token in doc
            if token.pos_ in ('PROPN', 'NOUN', 'ADJ') and not token.is_stop
        ]
        if title_tokens:
            candidate = ' '.join(title_tokens[:6])
            if self._ner_validates_project_title(candidate):
                return candidate[:100]

        return first_line[:100]

    def extract_projects(self, text: str) -> List[Dict]:
        sections = self.split_sections(text)
        project_text = sections.get('PROJECTS', '')

        if not project_text:
            return []

        project_entries = self._choose_project_entries(project_text)
        projects = []
        seen_names: Set[str] = set()

        for entry in project_entries:
            entry = entry.strip()
            if len(entry) < 20:
                continue

            name = self._extract_project_name(entry)
            if not name or self._is_label_line(name):
                continue
            if not self._ner_validates_project_title(name):
                continue

            name_key = name.lower()
            if name_key in seen_names:
                continue
            seen_names.add(name_key)

            technologies = self._find_skills_in_text(entry)
            projects.append({
                'name': name[:100],
                'technologies': technologies[:10],
                'description': entry[:500]
            })

        return projects

    def parse_resume(self, resume_text: str = None, pdf_file=None) -> Dict:
        """
        Main parsing function

        Args:
            resume_text: Plain text resume (optional)
            pdf_file: PDF file object (optional)

        Returns:
            Structured resume data
        """
        if pdf_file:
            text = self.parse_pdf(pdf_file)
        elif resume_text:
            text = resume_text
        else:
            raise ValueError("Either resume_text or pdf_file must be provided")

        if not text:
            raise ValueError("Could not extract text from resume")

        parsed_data = {
            'personal_info': {
                'name': '',
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
