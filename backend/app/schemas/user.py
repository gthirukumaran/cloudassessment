"""
User-related Pydantic schemas
"""
from typing import Optional
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
import uuid


class UserCreate(BaseModel):
    """User creation request schema"""
    email: EmailStr = Field(..., description="User email address")
    first_name: Optional[str] = Field(None, description="User first name", max_length=100)
    last_name: Optional[str] = Field(None, description="User last name", max_length=100)
    role: str = Field(default="user", description="User role")
    organization_id: Optional[uuid.UUID] = Field(None, description="Organization identifier")


class UserUpdate(BaseModel):
    """User update request schema"""
    first_name: Optional[str] = Field(None, description="User first name", max_length=100)
    last_name: Optional[str] = Field(None, description="User last name", max_length=100)
    role: Optional[str] = Field(None, description="User role")
    is_active: Optional[bool] = Field(None, description="Whether user is active")
    organization_id: Optional[uuid.UUID] = Field(None, description="Organization identifier")


class UserProfile(BaseModel):
    """User profile response schema"""
    id: uuid.UUID = Field(..., description="User unique identifier")
    email: str = Field(..., description="User email address")
    first_name: Optional[str] = Field(None, description="User first name")
    last_name: Optional[str] = Field(None, description="User last name")
    role: str = Field(..., description="User role")
    organization_id: Optional[uuid.UUID] = Field(None, description="Organization identifier")
    is_active: bool = Field(..., description="Whether user is active")
    created_at: datetime = Field(..., description="User creation time")
    updated_at: datetime = Field(..., description="Last update time")
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """User list response schema"""
    users: list[UserProfile] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total number of pages")


class ChangePasswordRequest(BaseModel):
    """Change password request schema"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., description="New password", min_length=8)


class UserStatsResponse(BaseModel):
    """User statistics response schema"""
    total_users: int = Field(..., description="Total number of users")
    active_users: int = Field(..., description="Number of active users")
    users_by_role: dict[str, int] = Field(..., description="Users count by role")
    recent_signups: int = Field(..., description="Number of recent signups (last 30 days)")
    avg_scans_per_user: float = Field(..., description="Average scans per user")
