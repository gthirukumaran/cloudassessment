"""
Chatbot models for AI-powered security assistance
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, JSON, Enum, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.database import Base


class MessageType(enum.Enum):
    """Message type enumeration"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatSession(Base):
    """Chat session model for AI chatbot conversations"""
    
    __tablename__ = "chat_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Session metadata
    title = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Context information
    scan_id = Column(UUID(as_uuid=True), ForeignKey("scans.id"), nullable=True)
    finding_id = Column(UUID(as_uuid=True), ForeignKey("findings.id"), nullable=True)
    context_data = Column(JSON, nullable=True)
    
    # Statistics
    message_count = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ChatSession(id={self.id}, session_id='{self.session_id}', user_id={self.user_id})>"


class ChatMessage(Base):
    """Chat message model for individual messages in conversations"""
    
    __tablename__ = "chat_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False)
    
    # Message content
    message_type = Column(Enum(MessageType), nullable=False)
    content = Column(Text, nullable=False)
    
    # AI-specific fields
    tokens_used = Column(Integer, nullable=True)
    model_used = Column(String(100), nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    
    # Message metadata
    message_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    
    def __repr__(self):
        return f"<ChatMessage(id={self.id}, type='{self.message_type.value}', session_id={self.session_id})>"
