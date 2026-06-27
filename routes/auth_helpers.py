"""
Authentication helpers for Flask session-based routes
"""

from functools import wraps
from typing import Callable, Dict, Optional, Tuple

from flask import jsonify, session

from database import DatabaseManager


def login_required(view: Callable):
    """Require a logged-in user."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('user_id'):
            return jsonify({'error': 'Authentication required'}), 401
        return view(*args, **kwargs)

    return wrapped


def get_current_user(db: Optional[DatabaseManager] = None) -> Optional[Dict]:
    user_id = session.get('user_id')
    if not user_id:
        return None
    db = db or DatabaseManager()
    return db.get_user_by_id(user_id)


def get_current_candidate_id(
    db: Optional[DatabaseManager] = None,
    require_profile: bool = False,
) -> Tuple[Optional[str], Optional[Tuple[Dict, int]]]:
    """
    Resolve the candidate_id for the logged-in user.

    Returns (candidate_id, error_response) where error_response is (jsonify_dict, status).
    """
    user = get_current_user(db)
    if not user:
        return None, ({'error': 'Authentication required'}, 401)

    candidate_id = user.get('candidate_id')
    if require_profile and not candidate_id:
        return None, ({
            'error': 'Upload your resume first to use this feature'
        }, 400)

    return candidate_id, None
