from typing import Optional
from fastapi import Request, HTTPException, status
from sqlalchemy.orm import Session
from app.core.auth.strategies.base import AuthStrategy
from app.core.config import settings
from app.models.user import User
from app.core.security import decode_access_token


class GitHubSUStrategy(AuthStrategy):
    """GitHub OAuth for Single User mode - only allows specific user"""

    def __init__(self, db_session: Session):
        self.db = db_session

    async def authenticate(self, request: Request) -> Optional[User]:
        """
        Authenticate using JWT token from GitHub OAuth.
        Only allows the configured SU user.
        """
        # Get token from Authorization header or cookie
        token = None

        # Try Authorization header first
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

        # Try cookie as fallback
        if not token:
            token = request.cookies.get("access_token")

        if not token:
            return None

        try:
            # Decode JWT token
            payload = decode_access_token(token)
            username = payload.get("sub")

            if not username:
                return None

            # In SU mode, only allow the configured user
            if username != settings.su_github_username:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Only {settings.su_github_username} is allowed."
                )

            # Get or create user from database
            user = self.db.query(User).filter(User.github_username == username).first()

            if not user:
                # Create user if doesn't exist (first login)
                user = User(
                    username=username,
                    github_username=username,
                    is_admin=True,  # SU user is always admin
                    is_active=True
                )
                self.db.add(user)
                self.db.commit()
                self.db.refresh(user)

            return user

        except Exception:
            return None

    def get_login_url(self) -> Optional[str]:
        """Get GitHub OAuth login URL"""
        if not settings.github_client_id:
            return None

        base_url = "https://github.com/login/oauth/authorize"
        params = [
            f"client_id={settings.github_client_id}",
            f"redirect_uri={settings.github_redirect_uri}",
            "scope=user:email,repo",
            "state=su_mode"
        ]

        return f"{base_url}?{'&'.join(params)}"

    def requires_auth(self) -> bool:
        """Authentication is required in SU auth mode"""
        return True
