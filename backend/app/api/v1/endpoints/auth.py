"""
Authentication endpoints for Azure OAuth2
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import LoginRequest, TokenResponse, RefreshTokenRequest
from app.core.dependencies import get_auth_service

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Login with Azure OAuth2 authorization code
    """
    try:
        # Authenticate with Azure
        azure_user_data = await auth_service.authenticate_azure_user(
            login_data.azure_code,
            login_data.redirect_uri
        )
        
        # Get or create user
        user = auth_service.get_or_create_user(db, azure_user_data)
        
        # Create token response
        return auth_service.create_token_response(user)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Refresh access token using refresh token
    """
    try:
        # Verify refresh token
        payload = auth_service.verify_token(refresh_data.refresh_token)
        
        # Check if it's a refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        # Get user
        user_id = payload.get("sub")
        user = auth_service.get_current_user(db, refresh_data.refresh_token)
        
        # Create new token response
        return auth_service.create_token_response(user)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token refresh failed: {str(e)}"
        )


@router.post("/logout")
async def logout(
    refresh_data: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Logout and invalidate refresh token
    """
    try:
        # Verify refresh token
        payload = auth_service.verify_token(refresh_data.refresh_token)
        
        # In a production environment, you would add the token to a blacklist
        # For now, we'll just return success
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Logout failed: {str(e)}"
        )


@router.get("/me", response_model=TokenResponse)
async def get_current_user_info(
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
    authorization: str = Depends(lambda x: x.headers.get("authorization"))
):
    """
    Get current user information
    """
    try:
        # Extract token from Authorization header
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme"
            )
        
        # Get current user
        user = auth_service.get_current_user(db, token)
        
        # Create token response (without new tokens)
        return TokenResponse(
            access_token=token,
            refresh_token="",  # Not provided in this endpoint
            token_type="bearer",
            expires_in=0,  # Not calculated in this endpoint
            user=user
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Failed to get user info: {str(e)}"
        )
