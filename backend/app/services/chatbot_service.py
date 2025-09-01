"""
Chatbot service for AI-powered security assistance
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
import uuid

from app.models.chatbot import ChatSession, ChatMessage, MessageType
from app.models.user import User
from app.schemas.chatbot import ChatSessionCreate, ChatMessageCreate, ChatQueryRequest
from app.services.ai_service import AIService
from app.core.exceptions import ResourceNotFoundError


class ChatbotService:
    """Service for managing AI chatbot conversations"""
    
    def __init__(self):
        self.ai_service = AIService()
    
    def create_session(self, db: Session, session_data: ChatSessionCreate, user: User) -> ChatSession:
        """Create a new chat session"""
        session = ChatSession(
            user_id=user.id,
            session_id=str(uuid.uuid4()),
            title=session_data.title,
            scan_id=session_data.scan_id,
            finding_id=session_data.finding_id,
            context_data=session_data.context_data
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        return session
    
    def get_session(self, db: Session, session_id: str, user: User) -> ChatSession:
        """Get a chat session by ID"""
        session = db.query(ChatSession).filter(
            and_(
                ChatSession.session_id == session_id,
                ChatSession.user_id == user.id
            )
        ).first()
        
        if not session:
            raise ResourceNotFoundError(f"Chat session {session_id} not found")
        
        return session
    
    def get_user_sessions(
        self, 
        db: Session, 
        user: User, 
        skip: int = 0, 
        limit: int = 50
    ) -> List[ChatSession]:
        """Get chat sessions for a user"""
        return db.query(ChatSession).filter(
            ChatSession.user_id == user.id
        ).order_by(desc(ChatSession.last_activity)).offset(skip).limit(limit).all()
    
    def add_message(
        self, 
        db: Session, 
        session_id: str, 
        message_data: ChatMessageCreate, 
        user: User
    ) -> ChatMessage:
        """Add a message to a chat session"""
        session = self.get_session(db, session_id, user)
        
        message = ChatMessage(
            session_id=session.id,
            message_type=message_data.message_type,
            content=message_data.content,
            tokens_used=message_data.tokens_used,
            model_used=message_data.model_used,
            response_time_ms=message_data.response_time_ms,
            message_metadata=message_data.metadata
        )
        
        db.add(message)
        
        # Update session statistics
        session.message_count += 1
        session.total_tokens += message_data.tokens_used or 0
        session.last_activity = datetime.utcnow()
        
        db.commit()
        db.refresh(message)
        
        return message
    
    def get_session_messages(
        self, 
        db: Session, 
        session_id: str, 
        user: User, 
        limit: int = 100
    ) -> List[ChatMessage]:
        """Get messages for a chat session"""
        session = self.get_session(db, session_id, user)
        
        return db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).order_by(ChatMessage.created_at).limit(limit).all()
    
    async def process_query(
        self, 
        db: Session, 
        session_id: str, 
        query_data: ChatQueryRequest, 
        user: User
    ) -> Dict[str, Any]:
        """Process a user query and generate AI response"""
        session = self.get_session(db, session_id, user)
        
        # Add user message
        user_message = ChatMessage(
            session_id=session.id,
            message_type=MessageType.USER,
            content=query_data.query,
            message_metadata=query_data.context
        )
        db.add(user_message)
        
        # Get chat history for context
        history = self.get_session_messages(db, session_id, user, limit=20)
        
        # Generate AI response
        start_time = datetime.utcnow()
        ai_response = await self.ai_service.generate_chat_response(
            query=query_data.query,
            chat_history=history,
            context=query_data.context
        )
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Add AI response
        ai_message = ChatMessage(
            session_id=session.id,
            message_type=MessageType.ASSISTANT,
            content=ai_response["response"],
            tokens_used=ai_response.get("tokens_used"),
            model_used=ai_response.get("model_used"),
            response_time_ms=int(response_time),
            message_metadata=ai_response.get("metadata")
        )
        db.add(ai_message)
        
        # Update session statistics
        session.message_count += 2  # User + AI message
        session.total_tokens += (ai_response.get("tokens_used") or 0)
        session.last_activity = datetime.utcnow()
        
        db.commit()
        db.refresh(ai_message)
        
        return {
            "response": ai_response["response"],
            "tokens_used": ai_response.get("tokens_used"),
            "model_used": ai_response.get("model_used"),
            "response_time_ms": int(response_time),
            "message_id": str(ai_message.id)
        }
    
    def delete_session(self, db: Session, session_id: str, user: User) -> bool:
        """Delete a chat session"""
        session = self.get_session(db, session_id, user)
        
        db.delete(session)
        db.commit()
        
        return True
    
    def update_session_title(self, db: Session, session_id: str, title: str, user: User) -> ChatSession:
        """Update the title of a chat session"""
        session = self.get_session(db, session_id, user)
        
        session.title = title
        db.commit()
        db.refresh(session)
        
        return session
