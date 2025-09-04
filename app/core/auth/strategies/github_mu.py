from typing import Optional
from fastapi import Request, HTTPException, status
from sqlalchemy.orm import Session
from app.core.auth.strategies.base import AuthStrategy
from app.core.config import settings
from app.models.user import User
from app.core.security import decode_access_token


class GitHubMUStrategy(AuthStrategy):
    """GitHub OAuth for Multi User mode - allows multiple users with role management"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    async def authenticate(self, request: Request) -> Optional[User]:
        """
        Authenticate using JWT token from GitHub OAuth.
        Allows multiple users with proper role management.
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
            github_id = payload.get("github_id")
            
            if not username:
                return None
            
            # Get user from database
            user = self.db.query(User).filter(User.github_username == username).first()
            
            if not user:
                # In MU mode, create new users automatically but as non-admin
                is_admin = username == settings.mu_admin_github_username
                
                user = User(
                    username=username,
                    github_username=username,
                    github_id=github_id,
                    is_admin=is_admin,
                    is_active=True
                )
                self.db.add(user)
                self.db.commit()
                self.db.refresh(user)
            
            # Check if user is active
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is deactivated. Contact administrator."
                )
            
            return user
            
        except HTTPException:
            raise
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
            "state=mu_mode"
        ]
        
        return f"{base_url}?{'&'.join(params)}"
    
    def requires_auth(self) -> bool:
        """Authentication is always required in MU mode"""
        return True