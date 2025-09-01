"""
User model for authentication and authorization
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class User(Base):
    """User model for authentication and authorization"""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    azure_id = Column(String(255), unique=True, nullable=True, index=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    role = Column(String(50), default="user", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    scans = relationship("Scan", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")
    reports = relationship("Report", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
    
    @property
    def full_name(self) -> str:
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        else:
            return self.email
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        role_permissions = {
            "user": ["read_own_scans", "create_own_scans", "read_own_reports"],
            "security_analyst": ["read_all_scans", "create_scans", "read_reports", "generate_reports"],
            "security_admin": ["read_all_scans", "create_scans", "read_reports", "generate_reports", "manage_users"],
            "admin": ["*"]  # All permissions
        }
        
        user_permissions = role_permissions.get(self.role, [])
        return "*" in user_permissions or permission in user_permissions
