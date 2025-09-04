from enum import Enum
from typing import Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings


class AppMode(str, Enum):
    SINGLE_USER = "single_user"
    MULTI_USER = "multi_user"


class Settings(BaseSettings):
    # Application Configuration
    app_mode: AppMode = AppMode.SINGLE_USER
    app_name: str = "FastAPI Multi-Mode App"
    debug: bool = False
    
    # Database
    database_url: str = "sqlite:///./app.db"
    
    # Security
    secret_key: str = "your-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # GitHub OAuth Configuration
    github_client_id: Optional[str] = None
    github_client_secret: Optional[str] = None
    github_redirect_uri: str = "http://localhost:8000/auth/github/callback"
    
    # Single User Mode Settings
    enable_su_auth: bool = False  # Enable GitHub OAuth for single user protection
    su_github_username: Optional[str] = None  # Allowed user in SU auth mode
    default_github_token: Optional[str] = None  # Default token for GitHub operations
    
    # Multi User Mode Settings
    mu_admin_github_username: Optional[str] = None  # Initial admin user
    
    @field_validator('github_client_id', 'github_client_secret')
    @classmethod
    def validate_github_oauth(cls, v, info):
        """Validate GitHub OAuth configuration based on mode and auth settings"""
        if info.data:
            app_mode = info.data.get('app_mode')
            enable_su_auth = info.data.get('enable_su_auth', False)
            
            # GitHub OAuth is required for MU mode or when SU auth is enabled
            if app_mode == AppMode.MULTI_USER or enable_su_auth:
                if not v:
                    raise ValueError(
                        f"GitHub OAuth credentials required for mode: {app_mode} "
                        f"or when SU auth is enabled"
                    )
        return v
    
    @field_validator('su_github_username')
    @classmethod
    def validate_su_username(cls, v, info):
        """Validate SU username when SU auth is enabled"""
        if info.data and info.data.get('enable_su_auth') and not v:
            raise ValueError("SU GitHub username required when SU auth is enabled")
        return v
    
    @field_validator('mu_admin_github_username')
    @classmethod
    def validate_mu_admin(cls, v, info):
        """Validate MU admin username"""
        if info.data and info.data.get('app_mode') == AppMode.MULTI_USER and not v:
            raise ValueError("MU admin GitHub username required for multi-user mode")
        return v
    
    @property
    def requires_auth(self) -> bool:
        """Check if the current configuration requires authentication"""
        return (
            self.app_mode == AppMode.MULTI_USER or 
            (self.app_mode == AppMode.SINGLE_USER and self.enable_su_auth)
        )
    
    @property
    def is_single_user_mode(self) -> bool:
        return self.app_mode == AppMode.SINGLE_USER
    
    @property
    def is_multi_user_mode(self) -> bool:
        return self.app_mode == AppMode.MULTI_USER
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }


# Global settings instance
settings = Settings()