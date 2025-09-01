"""
Chatbot-related Pydantic schemas
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

from app.models.chatbot import MessageType


class ChatSessionCreate(BaseModel):
    """Chat session creation request schema"""
    title: Optional[str] = Field(None, description="Session title")
    scan_id: Optional[uuid.UUID] = Field(None, description="Associated scan identifier")
    finding_id: Optional[uuid.UUID] = Field(None, description="Associated finding identifier")
    context_data: Optional[Dict[str, Any]] = Field(None, description="Additional context data")


class ChatSessionResponse(BaseModel):
    """Chat session response schema"""
    id: uuid.UUID = Field(..., description="Session unique identifier")
    user_id: uuid.UUID = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier string")
    
    # Session metadata
    title: Optional[str] = Field(None, description="Session title")
    is_active: bool = Field(..., description="Whether session is active")
    
    # Context information
    scan_id: Optional[uuid.UUID] = Field(None, description="Associated scan identifier")
    finding_id: Optional[uuid.UUID] = Field(None, description="Associated finding identifier")
    context_data: Optional[Dict[str, Any]] = Field(None, description="Additional context data")
    
    # Statistics
    message_count: int = Field(..., description="Number of messages in session")
    total_tokens: int = Field(..., description="Total tokens used")
    
    # Timestamps
    created_at: datetime = Field(..., description="Session creation time")
    updated_at: datetime = Field(..., description="Last update time")
    last_activity: datetime = Field(..., description="Last activity time")
    
    class Config:
        from_attributes = True


class ChatMessageCreate(BaseModel):
    """Chat message creation request schema"""
    content: str = Field(..., description="Message content", min_length=1)
    message_type: MessageType = Field(default=MessageType.USER, description="Message type")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ChatMessageResponse(BaseModel):
    """Chat message response schema"""
    id: uuid.UUID = Field(..., description="Message unique identifier")
    session_id: uuid.UUID = Field(..., description="Session identifier")
    
    # Message content
    message_type: MessageType = Field(..., description="Message type")
    content: str = Field(..., description="Message content")
    
    # AI-specific fields
    tokens_used: Optional[int] = Field(None, description="Number of tokens used")
    model_used: Optional[str] = Field(None, description="AI model used")
    response_time_ms: Optional[int] = Field(None, description="Response time in milliseconds")
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    created_at: datetime = Field(..., description="Message creation time")
    
    class Config:
        from_attributes = True


class ChatQueryRequest(BaseModel):
    """Chat query request schema"""
    query: str = Field(..., description="User query", min_length=1)
    session_id: Optional[str] = Field(None, description="Existing session identifier")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    scan_id: Optional[uuid.UUID] = Field(None, description="Associated scan identifier")
    finding_id: Optional[uuid.UUID] = Field(None, description="Associated finding identifier")


class ChatQueryResponse(BaseModel):
    """Chat query response schema"""
    response: str = Field(..., description="AI response")
    session_id: str = Field(..., description="Session identifier")
    message_id: uuid.UUID = Field(..., description="Message identifier")
    tokens_used: int = Field(..., description="Total tokens used")
    model_used: str = Field(..., description="AI model used")
    response_time_ms: int = Field(..., description="Response time in milliseconds")
    confidence_score: Optional[float] = Field(None, description="AI confidence score")
    suggested_actions: Optional[List[str]] = Field(None, description="Suggested actions")
    created_at: datetime = Field(..., description="Response creation time")


class ChatHistoryResponse(BaseModel):
    """Chat history response schema"""
    session: ChatSessionResponse = Field(..., description="Session information")
    messages: List[ChatMessageResponse] = Field(..., description="Session messages")
    total_messages: int = Field(..., description="Total number of messages")
    total_tokens: int = Field(..., description="Total tokens used")


class ChatSessionListResponse(BaseModel):
    """Chat session list response schema"""
    sessions: List[ChatSessionResponse] = Field(..., description="List of chat sessions")
    total: int = Field(..., description="Total number of sessions")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total number of pages")
