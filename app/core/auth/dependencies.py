from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.config import settings, AppMode
from app.core.auth.strategies.base import AuthStrategy
from app.core.auth.strategies.no_auth import NoAuthStrategy
from app.core.auth.strategies.github_su import GitHubSUStrategy
from app.core.auth.strategies.github_mu import GitHubMUStrategy
from app.models.user import User
from app.core.database import get_db

# HTTP Bearer for token extraction
security = HTTPBearer(auto_error=False)


def get_auth_strategy(db: Session = Depends(get_db)) -> AuthStrategy:
    """Get the appropriate authentication strategy based on app mode"""

    if settings.app_mode == AppMode.SINGLE_USER:
        if settings.enable_su_auth:
            return GitHubSUStrategy(db)
        else:
            return NoAuthStrategy()

    elif settings.app_mode == AppMode.MULTI_USER:
        return GitHubMUStrategy(db)

    else:
        raise ValueError(f"Unknown app mode: {settings.app_mode}")


async def get_current_user(
    request: Request,
    auth_strategy: AuthStrategy = Depends(get_auth_strategy)
) -> Optional[User]:
    """Get current authenticated user (optional)"""
    return await auth_strategy.authenticate(request)


async def require_auth(
    request: Request,
    auth_strategy: AuthStrategy = Depends(get_auth_strategy)
) -> User:
    """Require authentication - raises exception if not authenticated"""

    if not auth_strategy.requires_auth():
        # No auth required, return virtual user
        user = await auth_strategy.authenticate(request)
        if user:
            return user

    user = await auth_strategy.authenticate(request)

    if not user:
        login_url = auth_strategy.get_login_url()
        detail = "Authentication required"
        if login_url:
            detail = f"Authentication required. Login at: {login_url}"

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )

    return user


async def require_admin(
    current_user: User = Depends(require_auth)
) -> User:
    """Require admin privileges"""

    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )

    return current_user


def require_mu_mode():
    """Dependency that ensures multi-user mode is enabled"""
    def check_mu_mode():
        if settings.app_mode != AppMode.MULTI_USER:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="This endpoint is only available in multi-user mode"
            )
        return True

    return check_mu_mode


def require_su_mode():
    """Dependency that ensures single-user mode is enabled"""
    def check_su_mode():
        if settings.app_mode != AppMode.SINGLE_USER:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="This endpoint is only available in single-user mode"
            )
        return True

    return check_su_mode


async def get_github_token(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user)
) -> Optional[str]:
    """Get GitHub token for API operations"""

    # In SU mode without auth, use default token
    if (settings.app_mode == AppMode.SINGLE_USER and
        not settings.enable_su_auth and
        settings.default_github_token):
        return settings.default_github_token

    # If user is authenticated and has a token, use it
    if current_user and current_user.github_token:
        from app.core.security import decrypt_token
        return decrypt_token(current_user.github_token)

    # Check for token in request headers (for API usage)
    auth_header = request.headers.get("X-GitHub-Token")
    if auth_header:
        return auth_header

    return None


async def require_github_token(
    github_token: Optional[str] = Depends(get_github_token)
) -> str:
    """Require GitHub token for operations"""

    if not github_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub token required for this operation. "
                   "Either authenticate with GitHub OAuth or provide X-GitHub-Token header."
        )

    return github_token
