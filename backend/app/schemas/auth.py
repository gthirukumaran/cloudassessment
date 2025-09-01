"""
Authentication schemas for Azure OAuth2 and JWT tokens
"""
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class LoginRequest(BaseModel):
    """Azure OAuth2 login request schema"""
    azure_code: str = Field(..., description="Authorization code from Azure OAuth2")
    redirect_uri: str = Field(..., description="Redirect URI used in OAuth2 flow")


class UserResponse(BaseModel):
    """User response schema for authentication"""
    id: uuid.UUID = Field(..., description="User unique identifier")
    email: str = Field(..., description="User email address")
    first_name: Optional[str] = Field(None, description="User first name")
    last_name: Optional[str] = Field(None, description="User last name")
    role: str = Field(..., description="User role")
    organization_id: Optional[uuid.UUID] = Field(None, description="Organization identifier")
    is_active: bool = Field(..., description="Whether user is active")
    created_at: datetime = Field(..., description="User creation timestamp")
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """JWT token response schema"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: UserResponse = Field(..., description="User information")
    
    class Config:
        from_attributes = True


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str = Field(..., description="JWT refresh token")


class LogoutRequest(BaseModel):
    """Logout request schema"""
    refresh_token: str = Field(..., description="JWT refresh token to invalidate")


class PasswordResetRequest(BaseModel):
    """Password reset request schema"""
    email: str = Field(..., description="User email address")


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema"""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., description="New password", min_length=8)
