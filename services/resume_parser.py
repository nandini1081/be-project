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
        'TECHNICAL SKILLS AND INTERESTS': 'SKILLS',
        'CORE SKILLS': 'SKILLS',
        'KEY SKILLS': 'SKILLS',
        'PROJECT': 'PROJECTS',
        'ACADEMIC PROJECTS': 'PROJECTS',
        'PERSONAL PROJECTS': 'PROJECTS',
        'WORK EXPERIENCE': 'EXPERIENCE',
        'PROFESSIONAL EXPERIENCE': 'EXPERIENCE',
        'EMPLOYMENT': 'EXPERIENCE',
        'EMPLOYMENT HISTORY': 'EXPERIENCE',
        'INTERNSHIP': 'EXPERIENCE',
        'INTERNSHIPS': 'EXPERIENCE',
        'INTERNSHIP EXPERIENCE': 'EXPERIENCE',
    }

    SECTION_TITLES = [
        'EDUCATION', 'TECHNICAL SKILLS AND INTERESTS', 'TECHNICAL SKILLS', 'CORE SKILLS', 'KEY SKILLS', 'SKILLS',
        'ACADEMIC PROJECTS', 'PERSONAL PROJECTS', 'PROJECTS', 'PROJECT',
        'WORK EXPERIENCE', 'PROFESSIONAL EXPERIENCE', 'EXPERIENCE', 'EMPLOYMENT',
        'EMPLOYMENT HISTORY', 'INTERNSHIP EXPERIENCE', 'INTERNSHIPS', 'INTERNSHIP',
        'ACHIEVEMENTS', 'EXTRA-CURRICULAR ACTIVITIES', 'LEADERSHIP',
        'CERTIFICATIONS', 'PUBLICATIONS', 'AWARDS', 'HOBBIES', 'OBJECTIVE',
        'SUMMARY', 'PROFILE', 'CONTACT', 'REFERENCES',
    ]

    MAX_TITLE_WORDS = 8

    DESCRIPTION_VERBS = {
        'built', 'developed', 'implemented', 'designed', 'used', 'created',
        'worked', 'deployed', 'maintained', 'integrated', 'led', 'managed',
        'collaborated', 'achieved', 'improved', 'optimized', 'automated',
        'conducted', 'performed', 'assisted', 'supported', 'delivered',
    }

    ENTRY_LABEL_BLACKLIST = {
        'languages', 'language', 'tools', 'tool', 'technologies', 'technology',
        'tech stack', 'frameworks', 'framework', 'skills', 'skill',
        'duration', 'role', 'responsibilities', 'description', 'platform',
        'database', 'features', 'key features', 'environment', 'libraries',
        'stack', 'frontend', 'backend', 'summary', 'location', 'company',
        'achievements', 'highlights', 'cgpa', 'percentage', 'coursework',
    }

    SKILLS_FOOTER_LABELS = {
        'languages', 'libraries/frameworks', 'cloud/databases', 'coursework',
        'libraries', 'interests',
    }

    PROJECT_SECTION_STARTS = {
        'personal projects', 'academic projects', 'projects', 'project',
    }

    HARD_STOP_SECTIONS = {
        'achievements', 'education', 'certifications', 'experience',
        'work experience', 'professional experience', 'employment',
        'references', 'publications',
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
        self._section_header_lookup = self._build_section_header_lookup()

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
        """Extract jobs/internships only from an experience section."""
        sections = self.split_sections(text)
        experience_text = sections.get('EXPERIENCE', '').strip()

        if not experience_text:
            return []

        experience_text = self._truncate_at_next_section(experience_text)
        entries = self._choose_section_entries(experience_text, entry_type='experience')
        experience = []
        seen_keys: Set[str] = set()

        for entry in entries:
            fields = self._extract_experience_fields(entry)
            title_key = fields['role'].lower()
            if not title_key or title_key in seen_keys:
                continue
            if not self._entry_has_valid_title(entry, 'experience'):
                continue

            seen_keys.add(title_key)
            experience.append(fields)

        return experience

    def _build_section_header_lookup(self) -> Set[str]:
        lookup: Set[str] = set()
        for title in self.SECTION_TITLES:
            lookup.add(self._normalize_heading(title))
        for alias in self.SECTION_ALIASES:
            lookup.add(self._normalize_heading(alias))
        return lookup

    def split_sections(self, text: str) -> Dict[str, str]:
        titles_sorted = sorted(self.SECTION_TITLES, key=len, reverse=True)
        pattern = (
            r'(?im)^(?P<header>' +
            '|'.join(re.escape(title) for title in titles_sorted) +
            r')\s*:?\s*(?P<tail>.*)$'
        )
        matches = list(re.finditer(pattern, text))

        sections: Dict[str, str] = {}

        for i, match in enumerate(matches):
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

            section_name = match.group('header').upper().strip()
            section_name = self.SECTION_ALIASES.get(section_name, section_name)
            section_content = text[start:end].strip()
            inline_tail = (match.group('tail') or '').strip()
            if inline_tail:
                section_content = (
                    f'{inline_tail}\n{section_content}'.strip()
                    if section_content else inline_tail
                )

            if section_name in sections:
                sections[section_name] = (
                    sections[section_name].rstrip() + '\n\n' + section_content
                ).strip()
            else:
                sections[section_name] = section_content

        return sections

    def _normalize_heading(self, line: str) -> str:
        return re.sub(r'\s+', ' ', line.strip().lower().rstrip(':'))

    def _match_section_start(self, line: str, section_starts: set[str]) -> tuple[bool, str]:
        """Detect a section header line, including PDF-style inline headers."""
        stripped = line.strip()
        if not stripped:
            return False, ''

        normalized = self._normalize_heading(stripped)
        if normalized in section_starts:
            return True, ''

        for header in sorted(section_starts, key=len, reverse=True):
            prefix = header + ' '
            if normalized.startswith(prefix):
                remainder = re.sub(
                    rf'(?i)^{re.escape(header)}\s*:?\s*',
                    '',
                    stripped,
                    count=1,
                ).strip()
                return True, remainder

        return False, ''

    def _is_list_marker_line(self, line: str) -> bool:
        return bool(re.match(
            r'^(?:[-•●▪◦*\u2022\u2023\u00b7\uf0b7\u2219]\s+|\d+[\.)]\s+)',
            line.strip(),
        ))

    def _is_section_header_line(self, line: str) -> bool:
        normalized = self._normalize_heading(line)
        return normalized in self._section_header_lookup

    def _truncate_at_next_section(self, section_text: str) -> str:
        """Stop parsing when another resume section header appears inline."""
        kept_lines: List[str] = []
        for line in section_text.split('\n'):
            if self._is_section_header_line(line):
                break
            kept_lines.append(line)
        return '\n'.join(kept_lines).strip()

    def _is_label_line(self, line: str) -> bool:
        stripped = line.strip()
        if ':' in stripped:
            label_part = self._normalize_heading(stripped.split(':', 1)[0])
            if label_part in self.ENTRY_LABEL_BLACKLIST:
                return True

        normalized = self._normalize_heading(stripped)
        if normalized in self.ENTRY_LABEL_BLACKLIST:
            return True
        return bool(re.match(
            r'^(languages?|tools?|technologies?|skills?|frameworks?|stack|duration)\b',
            normalized
        ))

    def _clean_entry_line(self, line: str) -> str:
        line = line.strip()
        line = re.sub(
            r'^(?:[-•●▪◦*\u2022\u2023\u00b7\uf0b7\u2219]\s+|\d+[\.)]\s+)',
            '',
            line,
        )
        line = re.sub(r'^\*\*(.+?)\*\*$', r'\1', line)
        return line.strip()

    def _looks_like_skill_list_line(self, line: str) -> bool:
        """Comma-separated skill/tool lists (not project descriptions)."""
        stripped = line.strip()
        if not stripped or ':' in stripped:
            return False
        if self._is_list_marker_line(stripped):
            return False
        if stripped.count(',') < 2:
            return False
        cleaned = self._clean_entry_line(stripped)
        if self._starts_with_description_verb(cleaned):
            return False
        words = cleaned.split()
        return len(words) <= 14

    def _is_sentence_fragment_line(self, line: str) -> bool:
        """Wrapped description tails — not standalone project titles."""
        cleaned = self._clean_entry_line(line.strip())
        if not cleaned:
            return True
        if cleaned[0].isdigit():
            return True
        if cleaned.endswith('.') and len(cleaned.split()) <= 4:
            if cleaned == cleaned.lower() or cleaned[0].islower():
                return True
            if re.fullmatch(r'[\d,+%]+.*\.', cleaned):
                return True
        if re.fullmatch(r'[a-z][\w\s,+%()-]*\.', cleaned) and len(cleaned.split()) <= 6:
            return True
        return False

    def _looks_like_project_title_text(self, text: str) -> bool:
        """Project names are short Title Case phrases, not sentence fragments."""
        cleaned = text.strip()
        if not cleaned or self._is_sentence_fragment_line(cleaned):
            return False
        if cleaned.endswith('.') and len(cleaned.split()) <= 4:
            return False
        words = [w for w in cleaned.split() if w]
        if not words or len(words) > self.MAX_TITLE_WORDS:
            return False
        if words[0][0].islower():
            return False
        title_case = sum(1 for w in words if w[0].isupper())
        return title_case >= max(1, len(words) // 2)

    def _looks_like_title_case_name(self, text: str) -> bool:
        words = [word for word in text.split() if word]
        if len(words) < 2:
            return False
        capped = sum(1 for word in words if word[0].isupper())
        return capped >= max(2, len(words) - 1)

    def _starts_with_description_verb(self, line: str) -> bool:
        cleaned = self._clean_entry_line(line)
        if not cleaned:
            return False
        if self._looks_like_title_case_name(cleaned):
            return False
        first_word = re.split(r'\s+', cleaned.lower())[0]
        if first_word in self.DESCRIPTION_VERBS:
            return True

        doc = self.nlp(cleaned)
        if doc and doc[0].pos_ == 'VERB':
            return True
        return False

    def _is_skills_footer_line(self, line: str) -> bool:
        stripped = line.strip()
        if not stripped:
            return False
        label = self._normalize_heading(stripped.split(':', 1)[0])
        if label in self.SKILLS_FOOTER_LABELS:
            return True
        return bool(re.match(
            r'(?i)^(languages|libraries/frameworks|cloud/databases|coursework)\s*:',
            stripped,
        ))

    def _is_project_date_line(self, line: str) -> bool:
        stripped = line.strip()
        if re.fullmatch(
            r'(?i)(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}',
            stripped,
        ):
            return True
        if re.fullmatch(r'^(19|20)\d{2}\s*[-–]\s*(19|20)\d{2}$', stripped):
            return True
        return False

    def _is_project_metadata_colon_title(self, title: str) -> bool:
        if re.search(r'(?i)tools?\s*&\s*technologies?', title):
            return True
        if re.search(
            r'(?i)\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}\b',
            title,
        ):
            return True
        return False

    def _gather_project_section_text(self, text: str) -> str:
        """
        Collect project content from PERSONAL PROJECTS onward.
        PDFs often insert TECHNICAL SKILLS or education lines before project bodies.
        """
        lines = text.splitlines()
        start_idx = None
        inline_first_line = ''
        for index, line in enumerate(lines):
            matched, remainder = self._match_section_start(line, self.PROJECT_SECTION_STARTS)
            if matched:
                start_idx = index + 1
                inline_first_line = remainder
                break

        if start_idx is None:
            sections = self.split_sections(text)
            return sections.get('PROJECTS', '').strip()

        kept: List[str] = []
        if inline_first_line:
            kept.append(inline_first_line)
        for line in lines[start_idx:]:
            stripped = line.strip()
            if not stripped:
                if kept and kept[-1] != '':
                    kept.append('')
                continue

            normalized = self._normalize_heading(stripped)
            if normalized in self.HARD_STOP_SECTIONS:
                break
            if self._is_skills_footer_line(stripped):
                break
            if self._is_section_header_line(stripped):
                if 'skill' in normalized or normalized in ('skills', 'key skills', 'core skills'):
                    continue
                if normalized in self.HARD_STOP_SECTIONS:
                    break

            if self._is_junk_line(stripped, 'project'):
                continue
            if self._is_sentence_fragment_line(stripped) and kept:
                kept[-1] = f'{kept[-1]} {stripped}'
                continue
            kept.append(stripped)

        return '\n'.join(kept).strip()

    def _is_junk_line(self, line: str, entry_type: str = 'project') -> bool:
        """Skip years, skill lists, and metadata labels inside a section."""
        stripped = line.strip()
        if not stripped:
            return True
        if self._is_section_header_line(stripped):
            return True
        if self._is_label_line(stripped):
            return True
        if re.fullmatch(r'(?i)expected\s+(19|20)\d{2}', stripped):
            return True
        if re.fullmatch(r'^(19|20)\d{2}$', stripped):
            return True
        if re.fullmatch(r'^(19|20)\d{2}\s*[-–]\s*(19|20)\d{2}$', stripped):
            return True
        if re.search(r'(?i)\b(?:cgpa|percentage)\b', stripped):
            return True
        if re.fullmatch(r'[•●▪◦*\-–]+', stripped):
            return True
        if entry_type == 'project' and self._is_project_date_line(stripped):
            return True
        if entry_type == 'project' and self._extract_colon_title(stripped, 'project'):
            return False
        if entry_type == 'project' and self._looks_like_skill_list_line(stripped):
            return True
        return False

    def _clean_section_text(self, section_text: str, entry_type: str = 'project') -> str:
        section_text = self._truncate_at_next_section(section_text)
        kept: List[str] = []
        for line in section_text.split('\n'):
            stripped = line.strip()
            if not stripped:
                if kept and kept[-1] != '':
                    kept.append('')
                continue
            if self._is_section_header_line(stripped):
                break
            if self._is_junk_line(stripped, entry_type):
                continue
            kept.append(stripped)
        return '\n'.join(kept).strip()

    def _validates_project_colon_title(self, title: str) -> bool:
        title = title.strip()
        if len(title) < 3 or len(title.split()) > self.MAX_TITLE_WORDS:
            return False
        if not self._looks_like_project_title_text(title):
            return False
        if self._is_label_line(title):
            return False
        if self._starts_with_description_verb(title):
            return False
        if self._ner_validates_entry_title(title, 'project'):
            return True

        doc = self.nlp(title)
        words = title.split()
        title_case_words = sum(1 for word in words if word[:1].isupper())
        has_noun = any(token.pos_ in ('NOUN', 'PROPN', 'ADJ') for token in doc) if doc else False

        # Multi-word Title Case names (e.g. "Automated Video Transcription To Summarized Text")
        if len(words) >= 3 and title_case_words >= max(3, len(words) - 1) and has_noun:
            return True

        if not doc or doc[0].pos_ == 'VERB':
            return False
        return has_noun and (title_case_words >= 2 or len(words) <= 4)

    def _extract_colon_title(self, line: str, entry_type: str = 'project') -> str:
        """
        Parse 'Project Name : description' lines — title is the text before the colon.
        Ignores metadata labels like Languages: or Tools:.
        """
        stripped = line.strip()
        if not stripped or ':' not in stripped:
            return ''
        if self._is_list_marker_line(stripped):
            return ''

        left, _right = stripped.split(':', 1)
        title = left.strip()
        if not title or self._is_label_line(stripped):
            return ''
        if self._is_project_metadata_colon_title(title):
            return ''
        if len(title.split()) > self.MAX_TITLE_WORDS:
            return ''
        if self._starts_with_description_verb(title):
            return ''

        if entry_type == 'project':
            if self._validates_project_colon_title(title):
                return title
            return ''

        if self._ner_validates_entry_title(title, entry_type):
            return title
        return ''

    def _is_valid_project_name(self, name: str) -> bool:
        if not name or self._is_label_line(name):
            return False
        return (
            self._validates_project_colon_title(name)
            or self._ner_validates_entry_title(name, 'project')
        )

    def _is_metadata_line(self, line: str) -> bool:
        """Date/location lines that belong inside an experience entry, not as titles."""
        stripped = line.strip()
        if not stripped:
            return True
        if re.search(
            r'\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b',
            stripped,
            re.IGNORECASE,
        ) and re.search(r'\b(19|20)\d{2}\b', stripped):
            return True
        if re.fullmatch(
            r'(?i)(?:\d{1,2}/\d{4}|\w+\s+\d{4})\s*[-–]\s*(?:(?:\d{1,2}/\d{4}|\w+\s+\d{4})|present|current)',
            stripped,
        ):
            return True
        if re.fullmatch(r'(?i)(19|20)\d{2}\s*[-–]\s*(?:(19|20)\d{2}|present|current)', stripped):
            return True
        return False

    def _ner_validates_entry_title(self, title: str, entry_type: str = 'project') -> bool:
        title = title.strip()
        if len(title) < 3 or len(title.split()) > self.MAX_TITLE_WORDS:
            return False
        if self._is_label_line(title):
            return False
        if self._starts_with_description_verb(title):
            return False

        doc = self.nlp(title)
        if not doc:
            return False

        if entry_type == 'experience':
            if any(ent.label_ in ('ORG', 'PRODUCT') for ent in doc.ents):
                return True
            return any(token.pos_ in ('NOUN', 'PROPN') for token in doc)

        if any(ent.label_ in ('WORK_OF_ART', 'PRODUCT') for ent in doc.ents):
            return True

        has_noun = any(token.pos_ in ('NOUN', 'PROPN') for token in doc)
        starts_with_verb = doc[0].pos_ == 'VERB'
        mostly_nouns = sum(
            1 for token in doc if token.pos_ in ('NOUN', 'PROPN', 'ADJ')
        ) >= max(1, len(doc) // 2)

        return has_noun and not starts_with_verb and mostly_nouns

    def _is_entry_title_line(self, line: str, entry_type: str = 'project') -> bool:
        stripped = line.strip()
        if not stripped or self._is_section_header_line(stripped):
            return False
        if self._is_label_line(stripped):
            return False
        if entry_type == 'experience' and self._is_metadata_line(stripped):
            return False

        if entry_type == 'project':
            if self._is_sentence_fragment_line(stripped):
                return False
            colon_title = self._extract_colon_title(stripped, entry_type)
            if colon_title:
                return True

        cleaned = self._clean_entry_line(stripped)
        if not cleaned or len(cleaned) < 3:
            return False
        if len(cleaned.split()) > self.MAX_TITLE_WORDS:
            return False
        if self._starts_with_description_verb(cleaned):
            return False

        has_list_marker = self._is_list_marker_line(stripped)
        if has_list_marker:
            if entry_type == 'project' and not self._extract_colon_title(stripped, entry_type):
                return False
            return self._ner_validates_entry_title(cleaned, entry_type)

        if cleaned.endswith('.') and len(cleaned.split()) > 5:
            return False

        return self._ner_validates_entry_title(cleaned, entry_type)

    def _is_standalone_project_title_line(self, line: str) -> bool:
        """Title on its own line (no colon), followed by description paragraphs."""
        stripped = line.strip()
        if not stripped or self._is_section_header_line(stripped):
            return False
        if self._is_label_line(stripped) or self._is_junk_line(stripped, 'project'):
            return False
        if self._extract_colon_title(stripped, 'project'):
            return False
        if self._is_list_marker_line(stripped):
            return False

        cleaned = self._clean_entry_line(stripped)
        if not cleaned or len(cleaned.split()) > self.MAX_TITLE_WORDS:
            return False
        if self._starts_with_description_verb(cleaned):
            return False
        if self._is_project_date_line(cleaned):
            return False
        if self._is_sentence_fragment_line(cleaned):
            return False
        if re.search(r'(?i)tools?\s*&\s*technologies?', cleaned):
            return False
        if cleaned.endswith('.') and len(cleaned.split()) > 5:
            return False

        return self._validates_project_colon_title(cleaned)

    def _entry_has_valid_title(self, entry: str, entry_type: str = 'project') -> bool:
        entry = entry.strip()
        if len(entry) < 12:
            return False

        first_line = entry.split('\n', 1)[0].strip()
        title = self._extract_entry_title(entry, entry_type)
        if not title or self._is_label_line(title):
            return False
        if self._starts_with_description_verb(title):
            return False
        if entry_type == 'project':
            if not self._is_valid_project_name(title):
                return False
        elif not self._ner_validates_entry_title(title, entry_type):
            return False

        lines = [line.strip() for line in entry.split('\n') if line.strip()]
        if len(lines) == 1 and self._starts_with_description_verb(first_line):
            return False

        return True

    def _split_by_colon_titles(self, section_text: str, entry_type: str) -> List[str]:
        """Split on 'Title : description' lines common in student resumes."""
        section_text = self._clean_section_text(section_text, entry_type)
        lines = section_text.split('\n')
        entries: List[str] = []
        current: List[str] = []

        def flush():
            if not current:
                return
            block = '\n'.join(current).strip()
            if self._entry_has_valid_title(block, entry_type):
                entries.append(block)
            current.clear()

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if self._is_section_header_line(stripped):
                break

            colon_title = self._extract_colon_title(stripped, entry_type)
            if colon_title and current:
                flush()
            if colon_title:
                current.append(stripped)
            elif current:
                current.append(stripped)

        flush()
        return entries

    def _split_by_standalone_titles(self, section_text: str, entry_type: str) -> List[str]:
        section_text = self._clean_section_text(section_text, entry_type)
        lines = section_text.split('\n')
        entries: List[str] = []
        current: List[str] = []

        def flush():
            if not current:
                return
            block = '\n'.join(current).strip()
            if self._entry_has_valid_title(block, entry_type):
                entries.append(block)
            current.clear()

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if self._is_section_header_line(stripped) or self._is_skills_footer_line(stripped):
                break
            if self._is_sentence_fragment_line(stripped) and current:
                current.append(stripped)
                continue
            if self._is_standalone_project_title_line(stripped) and current:
                flush()
            if self._is_standalone_project_title_line(stripped) or current:
                current.append(stripped)

        flush()
        return entries

    def _split_by_blank_lines(self, section_text: str, entry_type: str) -> List[str]:
        section_text = self._clean_section_text(section_text, entry_type)
        entries: List[str] = []
        for block in re.split(r'\n\s*\n+', section_text):
            block = block.strip()
            if not block or self._is_section_header_line(block):
                continue
            if self._entry_has_valid_title(block, entry_type):
                entries.append(block)
        return entries

    def _split_by_title_lines(self, section_text: str, entry_type: str) -> List[str]:
        section_text = self._clean_section_text(section_text, entry_type)
        lines = section_text.split('\n')
        entries: List[str] = []
        current: List[str] = []

        def flush():
            if not current:
                return
            block = '\n'.join(current).strip()
            if self._entry_has_valid_title(block, entry_type):
                entries.append(block)
            current.clear()

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if self._is_section_header_line(stripped):
                break
            if entry_type == 'project' and self._is_sentence_fragment_line(stripped) and current:
                current.append(stripped)
                continue
            if self._is_entry_title_line(stripped, entry_type) and current:
                flush()
            current.append(stripped)

        flush()
        return entries

    def _split_by_list_markers(self, section_text: str, entry_type: str) -> List[str]:
        """New entry only when a bullet/number line is a title (not a description verb)."""
        section_text = self._clean_section_text(section_text, entry_type)
        lines = section_text.split('\n')
        entries: List[str] = []
        current: List[str] = []

        def flush():
            if not current:
                return
            block = '\n'.join(current).strip()
            if self._entry_has_valid_title(block, entry_type):
                entries.append(block)
            current.clear()

        for line in lines:
            stripped = line.strip()
            if not stripped:
                flush()
                continue
            if self._is_section_header_line(stripped):
                break

            if (
                entry_type == 'project'
                and self._is_standalone_project_title_line(stripped)
                and current
            ):
                flush()

            is_marker_line = self._is_list_marker_line(stripped)
            if entry_type == 'project' and self._is_sentence_fragment_line(stripped):
                if current:
                    current.append(stripped)
                continue
            if is_marker_line and self._is_entry_title_line(stripped, entry_type):
                flush()
                current.append(self._clean_entry_line(stripped))
            else:
                current.append(stripped)

        flush()
        return entries

    def _score_section_entries(self, entries: List[str], entry_type: str) -> float:
        if not entries:
            return 0.0

        validated = sum(
            1 for entry in entries
            if self._entry_has_valid_title(entry, entry_type)
        )
        fragment_penalty = sum(
            3.0 for entry in entries
            if not self._looks_like_project_title_text(
                self._extract_entry_title(entry, entry_type)
            )
        ) if entry_type == 'project' else 0.0
        over_split_penalty = max(0, len(entries) - 8) * 1.5
        invalid_penalty = (len(entries) - validated) * 2.0
        return validated * 3.0 - over_split_penalty - invalid_penalty - fragment_penalty

    def _choose_section_entries(self, section_text: str, entry_type: str = 'project') -> List[str]:
        strategies = [
            self._split_by_colon_titles,
            self._split_by_standalone_titles,
            self._split_by_title_lines,
            self._split_by_list_markers,
            self._split_by_blank_lines,
        ]

        best_entries: List[str] = []
        best_score = float('-inf')

        for strategy in strategies:
            entries = strategy(section_text, entry_type)
            score = self._score_section_entries(entries, entry_type)
            if score > best_score:
                best_score = score
                best_entries = entries

        return best_entries

    def _extract_entry_title(self, entry: str, entry_type: str = 'project') -> str:
        first_line_raw = entry.split('\n', 1)[0].strip()

        colon_title = self._extract_colon_title(first_line_raw, entry_type)
        if colon_title:
            return colon_title[:100]

        first_line = self._clean_entry_line(first_line_raw)

        if self._ner_validates_entry_title(first_line, entry_type):
            return first_line[:100]

        doc = self.nlp(first_line)
        noun_chunks = list(doc.noun_chunks)
        if noun_chunks:
            chunk = noun_chunks[0].text.strip()
            if self._ner_validates_entry_title(chunk, entry_type):
                return chunk[:100]

        title_tokens = [
            token.text for token in doc
            if token.pos_ in ('PROPN', 'NOUN', 'ADJ') and not token.is_stop
        ]
        if title_tokens:
            candidate = ' '.join(title_tokens[:self.MAX_TITLE_WORDS])
            if self._ner_validates_entry_title(candidate, entry_type):
                return candidate[:100]

        return first_line[:100]

    def _extract_experience_fields(self, entry: str) -> Dict:
        title = self._extract_entry_title(entry, 'experience')
        duration_match = re.search(
            r'(?i)(?:'
            r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}'
            r'|\d{1,2}/\d{4}'
            r'|\d{4}'
            r')\s*[-–]\s*'
            r'(?:'
            r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}'
            r'|\d{1,2}/\d{4}'
            r'|\d{4}'
            r'|present|current'
            r')',
            entry,
        )
        duration = duration_match.group(0).strip() if duration_match else ''

        role = title
        company = ''
        if '|' in title:
            parts = [part.strip() for part in title.split('|') if part.strip()]
            if parts:
                role = parts[0]
            if len(parts) > 1:
                company = parts[1]
        elif re.search(r'\bat\b', title, re.IGNORECASE):
            parts = re.split(r'\bat\b', title, maxsplit=1, flags=re.IGNORECASE)
            role = parts[0].strip()
            company = parts[1].strip() if len(parts) > 1 else ''

        return {
            'company': company or title,
            'role': role,
            'duration': duration,
            'description': entry[:500],
        }

    def extract_projects(self, text: str) -> List[Dict]:
        project_text = self._gather_project_section_text(text)

        if not project_text:
            return []

        project_entries = self._choose_section_entries(project_text, entry_type='project')
        projects = []
        seen_names: Set[str] = set()

        for entry in project_entries:
            name = self._extract_entry_title(entry, 'project')
            if not self._is_valid_project_name(name):
                continue

            name_key = name.lower()
            if name_key in seen_names:
                continue
            seen_names.add(name_key)

            technologies = self._find_skills_in_text(entry)
            projects.append({
                'name': name[:100],
                'technologies': technologies[:10],
                'description': entry[:500],
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