"""
Question Retriever - Person D
Retrieves personalized questions based on candidate profile and question groups.
"""

import math
import random
from collections import defaultdict
from typing import Dict, List, Optional, Set
from database import DatabaseManager
from utils import batch_cosine_similarity
from utils.vector_operations import validate_vector
from config import (
    TOP_MATCH_POOL_SIZE,
    MAX_FOLLOWUPS_PER_GROUP,
    MAX_QUESTIONS_PER_GROUP,
    MAX_BEHAVIORAL_RATIO,
)


class QuestionRetriever:
    """Retrieve personalized questions for candidates"""

    def __init__(self):
        self.db = DatabaseManager()
        self._question_cache = None

    def _load_questions(self, force_reload: bool = False):
        """Load all questions into memory (cache)"""
        if self._question_cache is None or force_reload:
            print("🔄 Loading questions from database...")
            self._question_cache = self.db.get_all_questions()
            print(f"✅ Loaded {len(self._question_cache)} questions")

    def _filter_questions(
        self,
        questions: List[Dict],
        difficulty: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[Dict]:
        """Apply optional difficulty and category filters."""
        filtered = [q for q in questions if q]
        if difficulty:
            filtered = [q for q in filtered if q.get('difficulty') == difficulty]
        if category:
            filtered = [q for q in filtered if q.get('category') == category]
        return filtered

    def _index_question_groups(self, questions: List[Dict]) -> tuple:
        """
        Build group chains and entry-point questions (followup_order == 1).
        Entry points are used for resume-similarity matching; follow-ups stay in-group.
        """
        groups: Dict[str, List[Dict]] = defaultdict(list)
        entry_points: List[Dict] = []

        for q in questions:
            group_id = q.get('question_group')
            order = q.get('followup_order') or 1
            if group_id:
                groups[group_id].append(q)
            if order == 1:
                entry_points.append(q)

        for group_id in groups:
            groups[group_id] = [
                q for q in groups[group_id]
                if (q.get('followup_order') or 1) <= MAX_QUESTIONS_PER_GROUP
            ]
            groups[group_id].sort(key=lambda item: item.get('followup_order') or 1)

        return groups, entry_points

    @staticmethod
    def _is_behavioral(question: Dict) -> bool:
        return question.get('category') == 'behavioral'

    def _max_behavioral_allowed(
        self, max_questions: int, category: Optional[str] = None
    ) -> Optional[int]:
        """Return behavioral cap for mixed interviews; None when filter overrides."""
        if category == 'behavioral':
            return max_questions
        if category in ('technical', 'situational'):
            return 0
        return math.floor(max_questions * MAX_BEHAVIORAL_RATIO)

    def _expand_group_chains(
        self,
        scored_entries: List[Dict],
        groups: Dict[str, List[Dict]],
        max_questions: int,
        exclude_groups: Optional[Set[str]] = None,
        randomize_groups: bool = False,
        category: Optional[str] = None,
        behavioral_budget: Optional[int] = None,
    ) -> List[Dict]:
        """Expand top-matched entry points into ordered cross-question chains."""
        exclude_groups = exclude_groups or set()
        ordered_entries = list(scored_entries)
        if randomize_groups:
            random.shuffle(ordered_entries)

        results: List[Dict] = []
        used_groups: Set[str] = set()
        behavioral_count = 0
        max_behavioral = (
            behavioral_budget
            if behavioral_budget is not None
            else self._max_behavioral_allowed(max_questions, category)
        )

        for entry in ordered_entries:
            group_id = entry.get('question_group')
            group_score = entry.get('similarity_score', 0.0)

            if group_id:
                if group_id in used_groups or group_id in exclude_groups:
                    continue
                chain = groups.get(group_id, [entry])[:MAX_QUESTIONS_PER_GROUP]
                used_groups.add(group_id)
            else:
                chain = [entry]

            chain_added = False
            for q in chain:
                if len(results) >= max_questions:
                    break
                if max_behavioral is not None and self._is_behavioral(q):
                    if behavioral_count >= max_behavioral:
                        break
                q_with_score = q.copy()
                q_with_score['similarity_score'] = group_score
                results.append(q_with_score)
                chain_added = True
                if max_behavioral is not None and self._is_behavioral(q):
                    behavioral_count += 1

            if not chain_added and group_id:
                used_groups.discard(group_id)

            if len(results) >= max_questions:
                break

        return results

    def retrieve_questions(
        self,
        candidate_id: str,
        max_questions: int = 15,
        difficulty: Optional[str] = None,
        category: Optional[str] = None,
        randomize: bool = True,
        exclude_behavioral: bool = False,
    ) -> List[Dict]:
        """
        Retrieve personalized questions for candidate.

        Uses cosine similarity on entry-point questions (followup_order=1), then
        expands each selected group into its full cross-question chain in order.
        """
        print(f"🔄 Retrieving questions for candidate: {candidate_id}")
        print(f"   Requested count: {max_questions}")
        if category:
            print(f"   Category filter: {category}")
        if difficulty:
            print(f"   Difficulty filter: {difficulty}")
        if randomize:
            print(
                f"   Group pool: top {TOP_MATCH_POOL_SIZE} entry points, "
                f"max {MAX_FOLLOWUPS_PER_GROUP} follow-ups, "
                f"behavioral cap {self._max_behavioral_allowed(max_questions, category)}"
            )

        profile = self.db.get_candidate_profile(candidate_id)
        if not profile:
            print(f"❌ Profile not found for: {candidate_id}")
            return []

        profile_vector = profile['profile_vector']

        try:
            validate_vector(profile_vector, "profile_vector")
        except ValueError as e:
            print(f"❌ Invalid profile vector: {e}")
            return []

        self._load_questions()
        questions = self._filter_questions(self._question_cache, difficulty, category)
        if exclude_behavioral:
            questions = [q for q in questions if not self._is_behavioral(q)]
        groups, entry_points = self._index_question_groups(questions)

        if not entry_points:
            print("❌ No entry-point questions available after filters")
            return []

        print(f"📊 Matching {len(entry_points)} entry points across {len(groups)} groups...")

        similarities = batch_cosine_similarity(
            profile_vector, [q['embedding'] for q in entry_points]
        )

        scored_entries = []
        for entry, sim in zip(entry_points, similarities):
            entry_with_score = entry.copy()
            entry_with_score['similarity_score'] = round(sim, 4)
            scored_entries.append(entry_with_score)

        scored_entries.sort(key=lambda x: x['similarity_score'], reverse=True)
        top_pool = scored_entries[:TOP_MATCH_POOL_SIZE]

        results = self._expand_group_chains(
            top_pool,
            groups,
            max_questions,
            randomize_groups=randomize,
            category=category,
        )

        if not results:
            print("❌ No questions available in match pool")
            return []

        print(f"✅ Selected {len(results)} questions in {len({q.get('question_group') for q in results if q.get('question_group')})} group chain(s)")
        if top_pool:
            print(
                f"   Top entry score range: {top_pool[0]['similarity_score']:.4f} – "
                f"{top_pool[-1]['similarity_score']:.4f}"
            )

        return results

    def retrieve_next_question(
        self,
        candidate_id: str,
        last_question_id: Optional[str] = None,
        asked_question_ids: Optional[List[str]] = None,
        difficulty: Optional[str] = None,
        category: Optional[str] = None,
    ) -> Optional[Dict]:
        """
        Retrieve the next interview question.

        If last_question_id belongs to a group with remaining follow-ups, return the
        next question in that group. Otherwise pick a new group via profile similarity.
        """
        asked = set(asked_question_ids or [])
        if last_question_id:
            asked.add(last_question_id)

        last_question = (
            self.db.get_question_by_id(last_question_id) if last_question_id else None
        )

        if last_question and last_question.get('question_group'):
            group_id = last_question['question_group']
            order = last_question.get('followup_order') or 1
            if order < MAX_QUESTIONS_PER_GROUP:
                next_q = self.db.get_next_followup_question(group_id, order)
                if next_q and next_q['question_id'] not in asked:
                    asked_behavioral = sum(
                        1 for qid in asked
                        if (q := self.db.get_question_by_id(qid)) and self._is_behavioral(q)
                    )
                    max_behavioral = self._max_behavioral_allowed(
                        TOP_MATCH_POOL_SIZE, category
                    )
                    if (
                        max_behavioral is not None
                        and self._is_behavioral(next_q)
                        and asked_behavioral >= max_behavioral
                    ):
                        next_q = None
                    if next_q:
                        if difficulty and next_q.get('difficulty') != difficulty:
                            pass
                        elif category and next_q.get('category') != category:
                            pass
                        else:
                            next_q = next_q.copy()
                            next_q['similarity_score'] = last_question.get('similarity_score')
                            return next_q

        asked_behavioral = 0
        for qid in asked:
            q = self.db.get_question_by_id(qid)
            if q and self._is_behavioral(q):
                asked_behavioral += 1

        max_behavioral = self._max_behavioral_allowed(TOP_MATCH_POOL_SIZE, category)
        exclude_behavioral = (
            max_behavioral is not None and asked_behavioral >= max_behavioral
        )

        batch = self.retrieve_questions(
            candidate_id=candidate_id,
            max_questions=TOP_MATCH_POOL_SIZE,
            difficulty=difficulty,
            category=category,
            randomize=False,
            exclude_behavioral=exclude_behavioral,
        )

        for q in batch:
            if q['question_id'] not in asked:
                return q

        return None

    def retrieve_adaptive_questions(
        self,
        candidate_id: str,
        last_score: Optional[float] = None,
        max_questions: int = 5,
    ) -> List[Dict]:
        """Retrieve questions with adaptive difficulty using group chains."""
        if last_score is None:
            difficulty = 'medium'
        elif last_score >= 0.8:
            difficulty = 'hard'
        elif last_score >= 0.5:
            difficulty = 'medium'
        else:
            difficulty = 'easy'

        print(f"🎯 Adaptive retrieval - difficulty: {difficulty}")

        return self.retrieve_questions(
            candidate_id=candidate_id,
            max_questions=max_questions,
            difficulty=difficulty,
        )

    def get_diverse_questions(
        self,
        candidate_id: str,
        questions_per_category: int = 3,
    ) -> List[Dict]:
        """Get diverse questions across categories, preserving group chains."""
        categories = ['technical', 'behavioral', 'situational']
        all_questions = []

        for cat in categories:
            questions = self.retrieve_questions(
                candidate_id=candidate_id,
                max_questions=questions_per_category,
                category=cat,
            )
            all_questions.extend(questions)

        print(f"✅ Retrieved {len(all_questions)} diverse questions")
        return all_questions

    def get_question_recommendations(self, candidate_id: str) -> Dict:
        """Get question recommendations with explanations."""
        profile = self.db.get_candidate_profile(candidate_id)
        if not profile:
            return {'error': 'Profile not found'}

        metadata = profile['metadata']

        questions = self.retrieve_questions(
            candidate_id, max_questions=10, randomize=False
        )

        recommended_topics = {}
        for q in questions[:5]:
            for topic in q['topics']:
                recommended_topics[topic] = recommended_topics.get(topic, 0) + 1

        return {
            'candidate_id': candidate_id,
            'experience_level': metadata.get('experience_level', 'Unknown'),
            'primary_domain': metadata.get('primary_domain', 'Unknown'),
            'total_matches': len(questions),
            'top_questions': questions[:5],
            'recommended_topics': dict(
                sorted(recommended_topics.items(), key=lambda x: x[1], reverse=True)
            ),
            'average_similarity': (
                round(sum(q['similarity_score'] for q in questions) / len(questions), 4)
                if questions
                else 0
            ),
        }
