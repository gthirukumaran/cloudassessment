"""
FastAPI dependencies for authentication and database access
"""
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.scan_service import ScanService
from app.services.chatbot_service import ChatbotService
from app.services.report_service import ReportService
from app.services.compliance_service import ComplianceService

# Create service instances
auth_service = AuthService()
scan_service = ScanService()
chatbot_service = ChatbotService()
report_service = ReportService()


def get_current_user(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
) -> User:
    """Get current authenticated user"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    try:
        # Extract token from Authorization header
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme"
            )
        
        return auth_service.get_current_user(db, token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def require_permission(permission: str):
    """Dependency to require specific permission"""
    def permission_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if not current_user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return current_user
    return permission_checker


def require_role(role: str):
    """Dependency to require specific role"""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role != role and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required"
            )
        return current_user
    return role_checker


def get_auth_service() -> AuthService:
    """Get authentication service instance"""
    return auth_service


def get_scan_service() -> ScanService:
    """Get scan service instance"""
    return scan_service


def get_chatbot_service() -> ChatbotService:
    """Get chatbot service instance"""
    return chatbot_service


def get_report_service() -> ReportService:
    """Get report service instance"""
    return report_service


def get_compliance_service(db: Session = Depends(get_db)) -> ComplianceService:
    """Get compliance service instance"""
    return ComplianceService(db)
