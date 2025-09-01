"""
Authentication service for Azure OAuth2 and JWT token management
"""
import jwt
import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.config import settings
from app.models.user import User
from app.models.organization import Organization
from app.schemas.auth import TokenResponse, UserResponse


class AuthService:
    """Authentication service for Azure OAuth2 and JWT token management"""
    
    def __init__(self):
        self.azure_token_url = f"https://login.microsoftonline.com/{settings.azure_tenant_id}/oauth2/v2.0/token"
        self.azure_user_info_url = "https://graph.microsoft.com/v1.0/me"
    
    async def authenticate_azure_user(self, azure_code: str, redirect_uri: str) -> Dict[str, Any]:
        """Authenticate user with Azure OAuth2"""
        try:
            # Exchange authorization code for access token
            token_data = await self._exchange_code_for_token(azure_code, redirect_uri)
            
            # Get user information from Microsoft Graph
            user_info = await self._get_azure_user_info(token_data["access_token"])
            
            return {
                "azure_id": user_info["id"],
                "email": user_info["mail"] or user_info["userPrincipalName"],
                "first_name": user_info.get("givenName"),
                "last_name": user_info.get("surname"),
                "display_name": user_info.get("displayName")
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Azure authentication failed: {str(e)}"
            )
    
    async def _exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.azure_token_url,
                data={
                    "client_id": settings.azure_client_id,
                    "client_secret": settings.azure_client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code"
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Token exchange failed: {response.text}")
            
            return response.json()
    
    async def _get_azure_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from Microsoft Graph"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.azure_user_info_url,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to get user info: {response.text}")
            
            return response.json()
    
    def create_access_token(self, user_id: str, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "type": "access"
        }
        
        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create JWT refresh token"""
        expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
        
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "type": "refresh"
        }
        
        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    def get_or_create_user(self, db: Session, azure_user_data: Dict[str, Any]) -> User:
        """Get existing user or create new user from Azure data"""
        # Try to find user by Azure ID first
        user = db.query(User).filter(User.azure_id == azure_user_data["azure_id"]).first()
        
        if not user:
            # Try to find user by email
            user = db.query(User).filter(User.email == azure_user_data["email"]).first()
            
            if user:
                # Update existing user with Azure ID
                user.azure_id = azure_user_data["azure_id"]
                user.first_name = azure_user_data.get("first_name") or user.first_name
                user.last_name = azure_user_data.get("last_name") or user.last_name
            else:
                # Create new user
                user = User(
                    azure_id=azure_user_data["azure_id"],
                    email=azure_user_data["email"],
                    first_name=azure_user_data.get("first_name"),
                    last_name=azure_user_data.get("last_name"),
                    role="user"  # Default role
                )
                
                # Create or get default organization
                organization = self._get_or_create_default_organization(db, azure_user_data["email"])
                user.organization_id = organization.id
                
                db.add(user)
        
        db.commit()
        db.refresh(user)
        return user
    
    def _get_or_create_default_organization(self, db: Session, email: str) -> Organization:
        """Get or create default organization for user"""
        # Extract domain from email
        domain = email.split("@")[1] if "@" in email else None
        
        if domain:
            organization = db.query(Organization).filter(Organization.domain == domain).first()
            if organization:
                return organization
        
        # Create new organization
        organization = Organization(
            name=f"Organization for {email}",
            domain=domain,
            subscription_tier="basic"
        )
        db.add(organization)
        db.commit()
        db.refresh(organization)
        return organization
    
    def create_token_response(self, user: User) -> TokenResponse:
        """Create complete token response with user data"""
        access_token = self.create_access_token(str(user.id))
        refresh_token = self.create_refresh_token(str(user.id))
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            user=UserResponse.from_orm(user)
        )
    
    def get_current_user(self, db: Session, token: str) -> User:
        """Get current user from JWT token"""
        payload = self.verify_token(token)
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user"
            )
        
        return user
