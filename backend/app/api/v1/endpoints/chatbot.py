"""
Chatbot endpoints for AI-powered security assistance
"""
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.chatbot import (
    ChatSessionCreate, ChatSessionResponse, ChatQueryRequest, 
    ChatQueryResponse, ChatHistoryResponse, ChatSessionListResponse
)
from app.services.chatbot_service import ChatbotService
from app.core.dependencies import get_current_active_user, get_chatbot_service

router = APIRouter()


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_session(
    session_data: ChatSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
):
    """Create a new chat session"""
    session = chatbot_service.create_session(db, session_data, current_user)
    return ChatSessionResponse.from_orm(session)


@router.get("/sessions", response_model=ChatSessionListResponse)
async def get_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
):
    """Get user's chat sessions"""
    sessions = chatbot_service.get_user_sessions(db, current_user, skip, limit)
    return ChatSessionListResponse(
        sessions=[ChatSessionResponse.from_orm(session) for session in sessions],
        total=len(sessions),
        skip=skip,
        limit=limit
    )


@router.get("/sessions/{session_id}/messages", response_model=ChatHistoryResponse)
async def get_session_messages(
    session_id: str,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
):
    """Get messages for a chat session"""
    messages = chatbot_service.get_session_messages(db, session_id, current_user, limit)
    return ChatHistoryResponse(
        session_id=session_id,
        messages=[{"id": str(msg.id), "content": msg.content, "type": msg.message_type.value} for msg in messages]
    )


@router.post("/sessions/{session_id}/query", response_model=ChatQueryResponse)
async def process_query(
    session_id: str,
    query_data: ChatQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
):
    """Process a user query and get AI response"""
    response = await chatbot_service.process_query(db, session_id, query_data, current_user)
    return ChatQueryResponse(**response)


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
):
    """Delete a chat session"""
    chatbot_service.delete_session(db, session_id, current_user)
    return {"message": "Chat session deleted successfully"}
