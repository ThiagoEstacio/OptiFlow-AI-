"""
AI Chatbot API Endpoints

Endpoints for conversational AI assistant:
- Chat message processing
- Conversation management
- Context-aware responses
- Command execution
- Analytics
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.chat import Conversation, ChatMessage, ChatTemplate
from app.services.ai_chatbot import get_chatbot_service
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Pydantic Schemas
# ============================================================================

class ChatMessageRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    include_context: bool = True


class ChatMessageResponse(BaseModel):
    conversation_id: str
    message: str
    timestamp: str
    context_used: bool
    relevant_tags: List[str]
    is_command: Optional[bool] = False


class ConversationCreate(BaseModel):
    title: Optional[str] = None
    context_tags: List[str] = []
    settings: dict = {}


class ConversationResponse(BaseModel):
    id: str
    title: Optional[str]
    message_count: int
    last_message_at: Optional[str]
    is_active: bool
    created_at: str


class ConversationWithMessages(BaseModel):
    id: str
    title: Optional[str]
    message_count: int
    is_active: bool
    created_at: str
    messages: List[dict]


class MessageFeedback(BaseModel):
    feedback: str  # helpful, not_helpful
    comment: Optional[str] = None


class TemplateResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    category: Optional[str]
    system_prompt: str
    example_questions: List[str]
    recommended_settings: dict


# ============================================================================
# Chat Endpoints
# ============================================================================

@router.post("/chat", response_model=ChatMessageResponse)
async def send_chat_message(
    request: ChatMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send a message to the AI chatbot

    Processes the message and returns an AI-generated response with context
    """
    try:
        # Get chatbot service
        chatbot = get_chatbot_service()

        # Get or create conversation
        conversation = None
        if request.conversation_id:
            conversation = db.query(Conversation).filter(
                Conversation.id == request.conversation_id,
                Conversation.user_id == current_user.id
            ).first()

            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
        else:
            # Create new conversation
            conversation = Conversation(
                user_id=current_user.id,
                title=request.message[:50] + "..." if len(request.message) > 50 else request.message,
                settings={"include_context": request.include_context}
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

        # Process message
        start_time = datetime.utcnow()

        response = chatbot.chat(
            user_id=str(current_user.id),
            message=request.message,
            db=db,
            conversation_id=str(conversation.id),
            include_context=request.include_context
        )

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        # Save user message
        user_message = ChatMessage(
            conversation_id=conversation.id,
            role="user",
            content=request.message,
            metadata={
                "include_context": request.include_context
            }
        )
        db.add(user_message)

        # Save assistant response
        assistant_message = ChatMessage(
            conversation_id=conversation.id,
            role="assistant",
            content=response["message"],
            metadata={
                "context_used": response.get("context_used", False),
                "relevant_tags": response.get("relevant_tags", []),
                "processing_time_ms": int(processing_time)
            }
        )
        db.add(assistant_message)

        # Update conversation
        conversation.message_count += 2
        conversation.last_message_at = datetime.utcnow()

        db.commit()

        return ChatMessageResponse(
            conversation_id=str(conversation.id),
            message=response["message"],
            timestamp=response["timestamp"],
            context_used=response.get("context_used", False),
            relevant_tags=response.get("relevant_tags", []),
            is_command=response.get("is_command", False)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    active_only: bool = Query(True, description="Show only active conversations"),
    limit: int = Query(50, description="Maximum conversations to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List user's conversations

    Returns list of conversations sorted by most recent activity
    """
    try:
        query = db.query(Conversation).filter(
            Conversation.user_id == current_user.id
        )

        if active_only:
            query = query.filter(Conversation.is_active == True)

        conversations = query.order_by(
            Conversation.last_message_at.desc().nullslast(),
            Conversation.created_at.desc()
        ).limit(limit).all()

        return [
            ConversationResponse(
                id=str(conv.id),
                title=conv.title,
                message_count=conv.message_count,
                last_message_at=conv.last_message_at.isoformat() if conv.last_message_at else None,
                is_active=conv.is_active,
                created_at=conv.created_at.isoformat()
            )
            for conv in conversations
        ]

    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: str,
    message_limit: int = Query(100, description="Maximum messages to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get conversation with full message history

    Returns conversation details and messages
    """
    try:
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        ).first()

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Get messages
        messages = db.query(ChatMessage).filter(
            ChatMessage.conversation_id == conversation_id
        ).order_by(
            ChatMessage.created_at.desc()
        ).limit(message_limit).all()

        # Reverse to show oldest first
        messages = list(reversed(messages))

        return ConversationWithMessages(
            id=str(conversation.id),
            title=conversation.title,
            message_count=conversation.message_count,
            is_active=conversation.is_active,
            created_at=conversation.created_at.isoformat(),
            messages=[
                {
                    "id": str(msg.id),
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.created_at.isoformat(),
                    "metadata": msg.metadata,
                    "feedback": msg.feedback
                }
                for msg in messages
            ]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    request: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new conversation

    Creates a new conversation session for the chatbot
    """
    try:
        conversation = Conversation(
            user_id=current_user.id,
            title=request.title or "New Conversation",
            context_tags=request.context_tags,
            settings=request.settings
        )

        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        return ConversationResponse(
            id=str(conversation.id),
            title=conversation.title,
            message_count=0,
            last_message_at=None,
            is_active=True,
            created_at=conversation.created_at.isoformat()
        )

    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a conversation

    Permanently deletes a conversation and all its messages
    """
    try:
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        ).first()

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        db.delete(conversation)
        db.commit()

        return {"message": "Conversation deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/conversations/{conversation_id}")
async def update_conversation(
    conversation_id: str,
    title: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update conversation settings

    Updates conversation title or active status
    """
    try:
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        ).first()

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        if title is not None:
            conversation.title = title

        if is_active is not None:
            conversation.is_active = is_active

        db.commit()
        db.refresh(conversation)

        return ConversationResponse(
            id=str(conversation.id),
            title=conversation.title,
            message_count=conversation.message_count,
            last_message_at=conversation.last_message_at.isoformat() if conversation.last_message_at else None,
            is_active=conversation.is_active,
            created_at=conversation.created_at.isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Message Feedback Endpoints
# ============================================================================

@router.post("/messages/{message_id}/feedback")
async def submit_message_feedback(
    message_id: str,
    feedback: MessageFeedback,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit feedback for a message

    Allows users to rate assistant responses
    """
    try:
        # Get message and verify ownership
        message = db.query(ChatMessage).join(Conversation).filter(
            ChatMessage.id == message_id,
            Conversation.user_id == current_user.id
        ).first()

        if not message:
            raise HTTPException(status_code=404, detail="Message not found")

        if message.role != "assistant":
            raise HTTPException(status_code=400, detail="Can only provide feedback on assistant messages")

        # Update feedback
        message.feedback = feedback.feedback
        message.feedback_comment = feedback.comment

        db.commit()

        return {"message": "Feedback submitted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Template Endpoints
# ============================================================================

@router.get("/templates", response_model=List[TemplateResponse])
async def list_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List available chat templates

    Returns predefined templates for common use cases
    """
    try:
        query = db.query(ChatTemplate).filter(ChatTemplate.is_active == True)

        if category:
            query = query.filter(ChatTemplate.category == category)

        templates = query.order_by(ChatTemplate.usage_count.desc()).all()

        return [
            TemplateResponse(
                id=str(template.id),
                name=template.name,
                description=template.description,
                category=template.category,
                system_prompt=template.system_prompt,
                example_questions=template.example_questions,
                recommended_settings=template.recommended_settings
            )
            for template in templates
        ]

    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Helper Commands Endpoint
# ============================================================================

@router.get("/commands")
async def list_commands(
    current_user: User = Depends(get_current_user)
):
    """
    List available chatbot commands

    Returns list of special commands and their usage
    """
    return {
        "commands": [
            {
                "command": "/analyze <tag_name>",
                "description": "Detailed analysis of a specific tag",
                "example": "/analyze reactor_temperature"
            },
            {
                "command": "/forecast <tag_name>",
                "description": "Generate 24-hour forecast for a tag",
                "example": "/forecast production_rate"
            },
            {
                "command": "/anomalies",
                "description": "List recent anomalies detected",
                "example": "/anomalies"
            },
            {
                "command": "/insights",
                "description": "Get latest AI insights",
                "example": "/insights"
            },
            {
                "command": "/maintenance",
                "description": "Check equipment health status",
                "example": "/maintenance"
            },
            {
                "command": "/optimize",
                "description": "Get optimization recommendations",
                "example": "/optimize"
            },
            {
                "command": "/help",
                "description": "Show help message with all commands",
                "example": "/help"
            }
        ]
    }


# ============================================================================
# Analytics Endpoint
# ============================================================================

@router.get("/analytics")
async def get_chat_analytics(
    days: int = Query(7, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get chat usage analytics for the user

    Returns statistics about chat usage
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Get user's conversations
        conversations = db.query(Conversation).filter(
            Conversation.user_id == current_user.id,
            Conversation.created_at >= cutoff_date
        ).all()

        # Get user's messages
        conversation_ids = [str(conv.id) for conv in conversations]

        total_messages = db.query(ChatMessage).filter(
            ChatMessage.conversation_id.in_(conversation_ids)
        ).count()

        user_messages = db.query(ChatMessage).filter(
            ChatMessage.conversation_id.in_(conversation_ids),
            ChatMessage.role == "user"
        ).count()

        # Get feedback stats
        feedback_messages = db.query(ChatMessage).filter(
            ChatMessage.conversation_id.in_(conversation_ids),
            ChatMessage.feedback.isnot(None)
        ).all()

        helpful_count = sum(1 for m in feedback_messages if m.feedback == "helpful")
        not_helpful_count = sum(1 for m in feedback_messages if m.feedback == "not_helpful")

        return {
            "period_days": days,
            "total_conversations": len(conversations),
            "active_conversations": sum(1 for c in conversations if c.is_active),
            "total_messages": total_messages,
            "user_messages": user_messages,
            "assistant_messages": total_messages - user_messages,
            "avg_messages_per_conversation": total_messages / len(conversations) if conversations else 0,
            "feedback": {
                "helpful": helpful_count,
                "not_helpful": not_helpful_count,
                "total": len(feedback_messages),
                "satisfaction_rate": (helpful_count / len(feedback_messages) * 100) if feedback_messages else 0
            }
        }

    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
