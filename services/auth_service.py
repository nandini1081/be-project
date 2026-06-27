"""
User authentication service
"""

import re
from typing import Dict, Optional

from werkzeug.security import check_password_hash, generate_password_hash

from database import DatabaseManager


class AuthService:
    """Register and authenticate application users."""

    EMAIL_PATTERN = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')

    def __init__(self):
        self.db = DatabaseManager()

    def _normalize_email(self, email: str) -> str:
        return email.strip().lower()

    def validate_email(self, email: str) -> bool:
        return bool(self.EMAIL_PATTERN.match(self._normalize_email(email)))

    def validate_password(self, password: str) -> Optional[str]:
        if not password or len(password) < 6:
            return 'Password must be at least 6 characters'
        return None

    def register(self, email: str, password: str) -> Dict:
        email = self._normalize_email(email)
        if not self.validate_email(email):
            raise ValueError('Invalid email address')

        password_error = self.validate_password(password)
        if password_error:
            raise ValueError(password_error)

        if self.db.get_user_by_email(email):
            raise ValueError('An account with this email already exists')

        password_hash = generate_password_hash(password)
        user = self.db.create_user(email, password_hash)
        return self._public_user(user)

    def authenticate(self, email: str, password: str) -> Optional[Dict]:
        email = self._normalize_email(email)
        user = self.db.get_user_by_email(email)
        if not user:
            return None
        if not check_password_hash(user['password_hash'], password):
            return None
        return self._public_user(user)

    def get_user(self, user_id: str) -> Optional[Dict]:
        user = self.db.get_user_by_id(user_id)
        if not user:
            return None
        return self._public_user(user)

    def _public_user(self, user: Dict) -> Dict:
        return {
            'user_id': user['user_id'],
            'email': user['email'],
            'has_profile': bool(user.get('candidate_id')),
            'created_at': user.get('created_at'),
        }
