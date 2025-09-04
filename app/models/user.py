from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True)
    
    # GitHub Integration
    github_id = Column(Integer, unique=True, index=True)
    github_username = Column(String(100), unique=True, index=True)
    github_avatar_url = Column(String(500))
    github_token = Column(Text)  # Encrypted GitHub token
    
    # Multi-User Mode Fields
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    organization_id = Column(Integer, index=True)  # For multi-tenant support
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))


# Pydantic Models for API
class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    github_username: Optional[str] = None


class UserCreate(UserBase):
    github_id: Optional[int] = None
    github_avatar_url: Optional[str] = None


class UserUpdate(BaseModel):
    email: Optional[str] = None
    github_avatar_url: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    github_id: Optional[int] = None
    github_avatar_url: Optional[str] = None
    is_admin: bool = False
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


class UserWithToken(UserResponse):
    """User model that includes GitHub token (for authorized requests only)"""
    has_github_token: bool = False  # Don't expose the actual token


class GitHubUser(BaseModel):
    """GitHub user data from OAuth"""
    id: int
    login: str
    email: Optional[str] = None
    name: Optional[str] = None
    avatar_url: Optional[str] = None