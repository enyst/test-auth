from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.core.config import settings
from app.core.database import get_db
from app.core.auth.dependencies import get_auth_strategy, get_current_user
from app.core.security import create_github_oauth_token, encrypt_token
from app.services.github_service import GitHubService
from app.models.user import User, UserResponse
from datetime import datetime

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/status")
async def auth_status(
    request: Request,
    current_user: User = Depends(get_current_user),
    auth_strategy = Depends(get_auth_strategy)
):
    """Get current authentication status and app configuration"""

    user_data = None
    if current_user:
        try:
            user_data = UserResponse.model_validate(current_user)
        except Exception:
            # Handle virtual user case
            user_data = {
                "id": current_user.id,
                "username": current_user.username,
                "email": current_user.email,
                "github_username": current_user.github_username,
                "github_id": current_user.github_id,
                "github_avatar_url": getattr(current_user, 'github_avatar_url', None),
                "is_admin": current_user.is_admin,
                "is_active": current_user.is_active,
                "created_at": current_user.created_at,
                "last_login": current_user.last_login
            }

    return {
        "app_mode": settings.app_mode,
        "requires_auth": auth_strategy.requires_auth(),
        "login_url": auth_strategy.get_login_url(),
        "authenticated": current_user is not None,
        "user": user_data
    }


@router.get("/login")
async def login():
    """Get login information"""

    if not settings.requires_auth:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authentication not required in current mode"
        )

    if not settings.github_client_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GitHub OAuth not configured"
        )

    # Build GitHub OAuth URL
    base_url = "https://github.com/login/oauth/authorize"
    params = [
        f"client_id={settings.github_client_id}",
        f"redirect_uri={settings.github_redirect_uri}",
        "scope=user:email,repo",
        f"state={settings.app_mode}"
    ]

    login_url = f"{base_url}?{'&'.join(params)}"

    return {
        "login_url": login_url,
        "app_mode": settings.app_mode
    }


@router.get("/github/callback")
async def github_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """Handle GitHub OAuth callback"""

    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code not provided"
        )

    try:
        # Exchange code for access token
        github_token = await GitHubService.exchange_code_for_token(
            settings.github_client_id,
            settings.github_client_secret,
            code
        )

        # Get user info from GitHub
        github_service = GitHubService(github_token)
        github_user = await github_service.get_authenticated_user()

        # Check authorization based on mode
        if settings.app_mode.value == "single_user" and settings.enable_su_auth:
            if github_user.login != settings.su_github_username:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Only {settings.su_github_username} is allowed."
                )

        # Get or create user in database
        user = db.query(User).filter(User.github_username == github_user.login).first()

        if not user:
            # Determine if user should be admin
            is_admin = False
            if settings.app_mode.value == "single_user":
                is_admin = True  # SU user is always admin
            elif settings.app_mode.value == "multi_user":
                is_admin = github_user.login == settings.mu_admin_github_username

            user = User(
                username=github_user.login,
                email=github_user.email,
                github_id=github_user.id,
                github_username=github_user.login,
                github_avatar_url=github_user.avatar_url,
                github_token=encrypt_token(github_token),
                is_admin=is_admin,
                is_active=True
            )
            db.add(user)
        else:
            # Update existing user
            user.email = github_user.email or user.email
            user.github_avatar_url = github_user.avatar_url
            user.github_token = encrypt_token(github_token)
            user.last_login = datetime.utcnow()

        db.commit()
        db.refresh(user)

        # Create JWT token
        github_user_data = {
            "id": github_user.id,
            "login": github_user.login,
            "email": github_user.email,
            "avatar_url": github_user.avatar_url
        }

        jwt_token = create_github_oauth_token(github_user_data, github_token)

        # Create response with token
        response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
        response.set_cookie(
            key="access_token",
            value=jwt_token,
            httponly=True,
            secure=True,
            samesite="lax"
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )


@router.post("/logout")
async def logout(response: Response):
    """Logout user"""

    response.delete_cookie(key="access_token")
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    try:
        return UserResponse.model_validate(current_user)
    except Exception:
        # Handle virtual user case
        return {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "github_username": current_user.github_username,
            "github_id": current_user.github_id,
            "github_avatar_url": getattr(current_user, 'github_avatar_url', None),
            "is_admin": current_user.is_admin,
            "is_active": current_user.is_active,
            "created_at": current_user.created_at,
            "last_login": current_user.last_login
        }
