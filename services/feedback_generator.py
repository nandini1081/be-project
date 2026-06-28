"""
LLM-powered interview and resume feedback generator.
Falls back to rule-based feedback when no API key is configured or the LLM call fails.
"""

import json
import os
import re
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1").rstrip("/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "45"))


class FeedbackGenerator:
    """Generate post-interview feedback using an LLM with rule-based fallback."""

    ROLE_SKILL_MAP = {
        "data scientist": ["python", "machine learning", "statistics", "sql", "pandas", "numpy", "model evaluation"],
        "ml engineer": ["python", "machine learning", "deep learning", "tensorflow", "pytorch", "mlops", "deployment"],
        "software engineer": ["data structures", "algorithms", "system design", "oop", "git", "testing"],
        "backend engineer": ["apis", "database", "sql", "microservices", "scalability", "caching"],
        "frontend engineer": ["javascript", "html", "css", "react", "state management", "performance"],
        "product manager": ["product strategy", "metrics", "stakeholder management", "prioritization"],
    }

    def generate(self, answers: List[Dict], resume: Optional[Dict] = None, stats: Optional[Dict] = None) -> Dict:
        context = self._build_context(answers, resume or {}, stats or {})
        llm_result = self._call_llm(context)
        if llm_result:
            return llm_result
        return self._fallback_feedback(context)

    def _normalize(self, text: Any) -> str:
        return str(text or "").lower().strip()

    def _count_occurrences(self, items: List[str]) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for item in items or []:
            normalized = self._normalize(item)
            if not normalized:
                continue
            counts[normalized] = counts.get(normalized, 0) + 1
        return counts

    def _pick_top_keys(self, count_map: Dict[str, int], limit: int = 5) -> List[str]:
        return [
            key for key, _ in sorted((count_map or {}).items(), key=lambda item: item[1], reverse=True)[:limit]
        ]

    def _answer_includes_keyword(self, answer_text: str, keyword: str) -> bool:
        answer = self._normalize(answer_text)
        key = self._normalize(keyword)
        return bool(answer and key and key in answer)

    def _get_expected_keywords(self, answer: Dict) -> List[str]:
        ideal = answer.get("idealKeywords") or answer.get("ideal_keywords") or []
        if ideal:
            return ideal
        return answer.get("topics") or []

    def _get_missing_keywords(self, answer: Dict) -> List[str]:
        return [
            keyword
            for keyword in self._get_expected_keywords(answer)
            if not self._answer_includes_keyword(answer.get("answerText") or answer.get("answer_text") or "", keyword)
        ]

    def _build_context(self, answers: List[Dict], resume: Dict, stats: Dict) -> Dict:
        attempted = [a for a in (answers or []) if (a.get("answerText") or a.get("answer_text")) != "[Skipped]"]
        low_score = [a for a in attempted if float(a.get("knowledgeScore") or a.get("knowledge_score") or 0) < 0.6]

        weak_topics = self._pick_top_keys(
            self._count_occurrences([topic for a in low_score for topic in (a.get("topics") or [])]),
            5,
        )

        missing_keyword_counts: Dict[str, int] = {}
        for answer in attempted:
            for keyword in self._get_missing_keywords(answer):
                normalized = self._normalize(keyword)
                if not normalized:
                    continue
                missing_keyword_counts[normalized] = missing_keyword_counts.get(normalized, 0) + 1
        missing_keywords = self._pick_top_keys(missing_keyword_counts, 8)

        role_counts = self._count_occurrences([role for a in answers for role in (a.get("jobRoles") or a.get("job_roles") or [])])
        top_roles = self._pick_top_keys(role_counts, 3)
        primary_role = top_roles[0] if top_roles else ""

        resume_skills = [self._normalize(skill) for skill in (resume.get("skills") or [])]
        role_skills = self.ROLE_SKILL_MAP.get(primary_role, [])
        interview_topics = self._pick_top_keys(
            self._count_occurrences([topic for a in answers for topic in (a.get("topics") or [])]),
            8,
        )
        required_signals = list(dict.fromkeys([*role_skills, *[self._normalize(t) for t in interview_topics]]))
        missing_skills = [
            skill
            for skill in required_signals
            if skill and not any(rs in skill or skill in rs for rs in resume_skills)
        ]

        project_text = " ".join(
            f"{p.get('name', '')} {p.get('description', '')}" for p in (resume.get("projects") or [])
        ).lower()
        has_metrics = bool(re.search(r"\b(\d+(\.\d+)?%|accuracy|f1|auc|precision|recall|latency)\b", project_text))
        has_experience = len(resume.get("experience") or []) > 0
        role_looks_ml = "data scientist" in primary_role or "ml" in primary_role

        question_items = []
        for index, answer in enumerate(answers or []):
            question_items.append({
                "question_number": index + 1,
                "question_text": answer.get("questionText") or answer.get("question_text") or f"Question {index + 1}",
                "answer_text": answer.get("answerText") or answer.get("answer_text") or "",
                "knowledge_score": round(float(answer.get("knowledgeScore") or answer.get("knowledge_score") or 0), 2),
                "speech_score": round(float(answer.get("speechScore") or answer.get("speech_score") or 0), 2),
                "total_score": round(float(answer.get("totalScore") or answer.get("total_score") or 0), 2),
                "topics": answer.get("topics") or [],
                "ideal_keywords": self._get_expected_keywords(answer),
                "missing_keywords": self._get_missing_keywords(answer),
            })

        return {
            "stats": {
                "total_answers": stats.get("totalAnswers") or stats.get("total_answers") or len(answers or []),
                "average_score": round(float(stats.get("avgScore") or stats.get("average_score") or 0), 2),
                "skipped": stats.get("skipped") or 0,
            },
            "analysis": {
                "weak_topics": weak_topics,
                "missing_keywords": missing_keywords,
                "top_roles": top_roles,
                "primary_role": primary_role,
                "missing_skills": missing_skills[:8],
                "has_experience": has_experience,
                "has_metrics": has_metrics,
                "role_looks_ml": role_looks_ml,
            },
            "questions": question_items,
            "resume_summary": {
                "skills": resume.get("skills") or [],
                "experience_count": len(resume.get("experience") or []),
                "project_count": len(resume.get("projects") or []),
                "education_count": len(resume.get("education") or []),
            },
        }

    def _call_llm(self, context: Dict) -> Optional[Dict]:
        if not OPENAI_API_KEY:
            return None

        system_prompt = (
            "You are an expert interview coach and resume advisor. "
            "Given structured interview performance data and resume context, produce actionable, "
            "encouraging feedback. Be specific and reference the candidate's actual answers and gaps. "
            "Do not invent facts not present in the input. "
            "Return valid JSON only with this schema:\n"
            "{\n"
            '  "interview_summary": ["2-4 concise bullet points on overall interview performance and focus areas"],\n'
            '  "question_feedback": [\n'
            '    {"question_number": 1, "feedback": "1-3 sentences of constructive feedback for that Q&A"}\n'
            "  ],\n"
            '  "resume_summary": ["2-4 concise bullet points on resume improvements tied to interview gaps"],\n'
            '  "role_context": "one short sentence about target roles inferred from the interview, or empty string"\n'
            "}"
        )

        user_prompt = (
            "Generate post-interview feedback from this data:\n\n"
            f"{json.dumps(context, indent=2)}"
        )

        try:
            response = requests.post(
                f"{OPENAI_API_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": OPENAI_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.6,
                    "response_format": {"type": "json_object"},
                },
                timeout=LLM_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            return self._normalize_llm_response(parsed, context)
        except Exception as exc:
            print(f"LLM feedback generation failed: {exc}")
            return None

    def _normalize_llm_response(self, parsed: Dict, context: Dict) -> Dict:
        interview_summary = parsed.get("interview_summary") or []
        resume_summary = parsed.get("resume_summary") or []
        role_context = parsed.get("role_context") or ""

        question_feedback = []
        llm_by_number = {
            int(item.get("question_number", 0)): item.get("feedback", "")
            for item in (parsed.get("question_feedback") or [])
            if item.get("question_number") is not None
        }

        for item in context.get("questions") or []:
            number = item["question_number"]
            question_feedback.append({
                "questionNumber": number,
                "questionText": item["question_text"],
                "answerText": item["answer_text"],
                "feedback": llm_by_number.get(number) or self._question_fallback(item),
            })

        return {
            "source": "llm",
            "interviewFeedback": {
                "sentences": [s for s in interview_summary if s],
                "questionFeedback": question_feedback,
            },
            "resumeSuggestions": {
                "sentences": [s for s in resume_summary if s],
                "topRoles": context["analysis"]["top_roles"],
                "roleContext": role_context,
            },
        }

    def _question_fallback(self, item: Dict) -> str:
        missing = item.get("missing_keywords") or []
        if missing:
            return (
                f"Your answer could be stronger by explicitly covering concepts such as "
                f"{', '.join(missing[:4])}. Try structuring your response with a definition, example, and trade-off."
            )
        if item.get("knowledge_score", 0) >= 0.75:
            return "Solid coverage of the expected concepts. Add a concrete example or metric to make it interview-ready."
        return "Expand your answer with clearer terminology and a brief real-world example."

    def _fallback_feedback(self, context: Dict) -> Dict:
        analysis = context["analysis"]
        focus_areas = analysis["weak_topics"] or analysis["missing_keywords"][:4]

        interview_sentences = []
        if focus_areas:
            interview_sentences.append(
                f"Focus on strengthening your understanding of {', '.join(focus_areas)} based on your weaker responses."
            )
        else:
            interview_sentences.append(
                "Your performance is stable overall; keep practicing with deeper, structured explanations."
            )

        if analysis["missing_keywords"]:
            interview_sentences.append(
                f"When answering, explicitly mention key concepts such as {', '.join(analysis['missing_keywords'][:4])}."
            )
        else:
            interview_sentences.append(
                "Continue using precise technical terminology and concrete examples in your answers."
            )

        resume_sentences = []
        primary_role = analysis["primary_role"]
        if analysis["missing_skills"]:
            resume_sentences.append(
                f"For the {primary_role or 'target'} role, highlight skills like "
                f"{', '.join(analysis['missing_skills'][:6])} on your resume if you have them."
            )
        else:
            resume_sentences.append(
                "Your resume aligns reasonably well with the interview topics; keep skill names explicit for ATS matching."
            )

        if not analysis["has_experience"]:
            resume_sentences.append(
                "Add internship, freelance, or academic project experience to show practical application of your skills."
            )

        if analysis["role_looks_ml"] and not analysis["has_metrics"]:
            resume_sentences.append(
                "For ML projects, include measurable outcomes such as accuracy, F1-score, AUC, or latency improvements."
            )
        elif not analysis["has_metrics"]:
            resume_sentences.append(
                "Add measurable impact in projects (percent improvements, scale, or business outcomes) to strengthen your resume."
            )

        question_feedback = []
        for item in context.get("questions") or []:
            question_feedback.append({
                "questionNumber": item["question_number"],
                "questionText": item["question_text"],
                "answerText": item["answer_text"],
                "feedback": self._question_fallback(item),
            })

        role_context = ""
        if analysis["top_roles"]:
            role_context = f"Interview questions were aligned with roles such as {', '.join(analysis['top_roles'])}."

        return {
            "source": "fallback",
            "interviewFeedback": {
                "sentences": interview_sentences,
                "questionFeedback": question_feedback,
            },
            "resumeSuggestions": {
                "sentences": resume_sentences,
                "topRoles": analysis["top_roles"],
                "roleContext": role_context,
            },
        }
