from typing import Optional
from datetime import datetime
from fastapi import Request
from app.core.auth.strategies.base import AuthStrategy
from app.models.user import User


class NoAuthStrategy(AuthStrategy):
    """No authentication required - for single user mode without auth"""

    async def authenticate(self, request: Request) -> Optional[User]:
        """
        No authentication required. Return a default user or None.
        In single user mode without auth, we can create a virtual user.
        """
        # Create a virtual single user with proper datetime
        virtual_user = User()
        virtual_user.id = 1
        virtual_user.username = "single_user"
        virtual_user.email = "user@localhost"
        virtual_user.github_username = None
        virtual_user.github_id = None
        virtual_user.is_admin = True
        virtual_user.is_active = True
        virtual_user.created_at = datetime.utcnow()
        virtual_user.updated_at = datetime.utcnow()
        virtual_user.last_login = None
        return virtual_user

    def get_login_url(self) -> Optional[str]:
        """No login URL needed"""
        return None

    def requires_auth(self) -> bool:
        """No authentication required"""
        return False
