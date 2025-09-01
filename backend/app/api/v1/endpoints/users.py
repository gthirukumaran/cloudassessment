"""
User endpoints for user management
"""
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserProfile, UserListResponse, UserStatsResponse
from app.core.dependencies import get_current_active_user, require_role

router = APIRouter()


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user profile"""
    return UserProfile.from_orm(current_user)


@router.get("/", response_model=UserListResponse)
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Get all users (admin only)"""
    # TODO: Implement user listing logic
    return UserListResponse(
        users=[],
        total=0,
        skip=skip,
        limit=limit
    )


@router.get("/stats", response_model=UserStatsResponse)
async def get_user_stats(
    current_user: User = Depends(get_current_active_user)
):
    """Get user statistics"""
    # TODO: Implement user stats logic
    return UserStatsResponse(
        total_scans=0,
        total_reports=0,
        total_chat_sessions=0
    )
