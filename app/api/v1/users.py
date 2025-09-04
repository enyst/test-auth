from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.auth.dependencies import require_auth, require_admin, require_mu_mode
from app.models.user import User, UserResponse, UserUpdate
from datetime import datetime

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of users to return"),
    active_only: bool = Query(True, description="Only return active users"),
    _: bool = Depends(require_mu_mode),  # Only available in MU mode
    current_user: User = Depends(require_admin),  # Requires admin
    db: Session = Depends(get_db)
):
    """List all users (MU mode only, admin required)"""
    
    query = db.query(User)
    
    if active_only:
        query = query.filter(User.is_active == True)
    
    users = query.offset(skip).limit(limit).all()
    return [UserResponse.from_orm(user) for user in users]


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: User = Depends(require_auth)
):
    """Get current user information"""
    
    return UserResponse.from_orm(current_user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    _: bool = Depends(require_mu_mode),  # Only available in MU mode
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get user by ID (MU mode only)"""
    
    # Users can view their own profile, admins can view any profile
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.from_orm(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    _: bool = Depends(require_mu_mode),  # Only available in MU mode
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Update user (MU mode only)"""
    
    # Users can update their own profile, admins can update any profile
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields
    update_data = user_update.dict(exclude_unset=True)
    
    # Only admins can change is_active status
    if "is_active" in update_data and not current_user.is_admin:
        del update_data["is_active"]
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    return UserResponse.from_orm(user)


@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    _: bool = Depends(require_mu_mode),  # Only available in MU mode
    current_user: User = Depends(require_admin),  # Admin only
    db: Session = Depends(get_db)
):
    """Deactivate user (MU mode only, admin required)"""
    
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = False
    user.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": f"User {user.username} deactivated successfully"}


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: int,
    _: bool = Depends(require_mu_mode),  # Only available in MU mode
    current_user: User = Depends(require_admin),  # Admin only
    db: Session = Depends(get_db)
):
    """Activate user (MU mode only, admin required)"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = True
    user.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": f"User {user.username} activated successfully"}


@router.post("/{user_id}/make-admin")
async def make_admin(
    user_id: int,
    _: bool = Depends(require_mu_mode),  # Only available in MU mode
    current_user: User = Depends(require_admin),  # Admin only
    db: Session = Depends(get_db)
):
    """Grant admin privileges to user (MU mode only, admin required)"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already an admin"
        )
    
    user.is_admin = True
    user.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": f"User {user.username} granted admin privileges"}


@router.post("/{user_id}/remove-admin")
async def remove_admin(
    user_id: int,
    _: bool = Depends(require_mu_mode),  # Only available in MU mode
    current_user: User = Depends(require_admin),  # Admin only
    db: Session = Depends(get_db)
):
    """Remove admin privileges from user (MU mode only, admin required)"""
    
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove admin privileges from your own account"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not an admin"
        )
    
    user.is_admin = False
    user.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": f"Admin privileges removed from user {user.username}"}


@router.get("/stats/summary")
async def get_user_stats(
    _: bool = Depends(require_mu_mode),  # Only available in MU mode
    current_user: User = Depends(require_admin),  # Admin only
    db: Session = Depends(get_db)
):
    """Get user statistics summary (MU mode only, admin required)"""
    
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    admin_users = db.query(User).filter(User.is_admin == True).count()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": total_users - active_users,
        "admin_users": admin_users
    }