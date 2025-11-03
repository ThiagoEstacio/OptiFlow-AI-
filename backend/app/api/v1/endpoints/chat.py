"""
Chat/Chatbot API endpoints
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from uuid import UUID

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.chat import Conversation, Message, MessageRole
from app.schemas.chat import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationListResponse,
    MessageCreate,
    MessageResponse,
    ChatRequest,
    ChatResponse,
    InsightRequest,
    InsightResponse
)
from app.services.ai_service import AIService


router = APIRouter()
ai_service = AIService()


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new conversation.
    """
    db_conversation = Conversation(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        title=conversation.title,
        context=conversation.context
    )
    db.add(db_conversation)
    await db.commit()
    await db.refresh(db_conversation)

    return db_conversation


@router.get("/conversations", response_model=List[ConversationListResponse])
async def list_conversations(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List user's conversations.
    """
    query = select(Conversation).where(
        Conversation.user_id == current_user.id
    ).order_by(desc(Conversation.updated_at)).offset(skip).limit(limit)

    result = await db.execute(query)
    conversations = result.scalars().all()

    # Build response with message count
    response = []
    for conv in conversations:
        message_count_query = select(Message).where(Message.conversation_id == conv.id)
        message_result = await db.execute(message_count_query)
        message_count = len(message_result.scalars().all())

        response.append(
            ConversationListResponse(
                id=conv.id,
                title=conv.title,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                message_count=message_count
            )
        )

    return response


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific conversation with all messages.
    """
    query = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    )
    result = await db.execute(query)
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    # Load messages
    messages_query = select(Message).where(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at)
    messages_result = await db.execute(messages_query)
    messages = messages_result.scalars().all()

    # Manually set messages to avoid lazy loading issues
    conversation.messages = messages

    return conversation


@router.patch("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    conversation_update: ConversationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a conversation.
    """
    query = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    )
    result = await db.execute(query)
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    # Update fields
    if conversation_update.title is not None:
        conversation.title = conversation_update.title
    if conversation_update.context is not None:
        conversation.context = conversation_update.context

    await db.commit()
    await db.refresh(conversation)

    return conversation


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a conversation.
    """
    query = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    )
    result = await db.execute(query)
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    await db.delete(conversation)
    await db.commit()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send a message and get AI response.
    Creates a new conversation if conversation_id is not provided.
    """
    return await _process_chat(request, db, current_user)


@router.post("/chat/demo")
async def chat_demo(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Demo chat endpoint without authentication - for testing/demo purposes.
    Returns simplified response without conversation persistence.
    """
    # Create a demo user context (no DB persistence)
    class DemoUser:
        id = "demo-user"
        organization_id = "demo-org"
    
    demo_user = DemoUser()
    
    # Process chat without saving to database for demo
    return await _process_chat_demo(request, db)


async def _process_chat_demo(request: ChatRequest, db: AsyncSession):
    """Process chat for demo mode without user authentication"""
    # Get AI response without saving to database
    try:
        # Build context from request
        message_list = [{"role": "user", "content": request.message}]
        
        # Get AI response using the AIService
        ai_response = await ai_service.generate_response(
            messages=message_list,
            context={
                "mode": "demo",
                "platform": "OptiFlow AI",
                "capabilities": [
                    "Consultar valores de tags em tempo real",
                    "Analisar dados históricos",
                    "Insights de otimização de processos",
                    "Monitoramento de alarmes e eventos"
                ]
            }
        )
        
        # Return simplified response for demo mode (not using ChatResponse schema)
        return {
            "conversation_id": None,
            "message": ai_response,
            "mode": "demo",
            "model": ai_service.model if ai_service.api_key else "fallback",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat: {str(e)}"
        )


async def _process_chat(request: ChatRequest, db: AsyncSession, current_user: User):
    """Process authenticated chat request"""
    # Get or create conversation
    if request.conversation_id:
        query = select(Conversation).where(
            Conversation.id == request.conversation_id,
            Conversation.user_id == current_user.id
        )
        result = await db.execute(query)
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
    else:
        # Create new conversation
        conversation = Conversation(
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            title=request.message[:50] + ("..." if len(request.message) > 50 else "")
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)

    # Save user message
    user_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content=request.message
    )
    db.add(user_message)
    await db.commit()
    await db.refresh(user_message)

    # Get conversation history
    messages_query = select(Message).where(
        Message.conversation_id == conversation.id
    ).order_by(Message.created_at)
    messages_result = await db.execute(messages_query)
    all_messages = messages_result.scalars().all()

    # Convert to format for AI service
    message_list = [
        {"role": msg.role.value, "content": msg.content}
        for msg in all_messages
    ]

    # Get platform context if requested
    context = None
    if request.include_context:
        context = await ai_service.get_platform_context(
            db,
            str(current_user.organization_id),
            include_devices=True,
            include_alarms=True,
            time_range="24h"
        )

    # Generate AI response
    ai_response = await ai_service.generate_response(message_list, context)

    # Save AI response
    assistant_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.ASSISTANT,
        content=ai_response,
        metadata={
            "model": ai_service.model,
            "context_included": request.include_context
        }
    )
    db.add(assistant_message)
    await db.commit()
    await db.refresh(assistant_message)

    # Generate suggestions
    suggestions = ai_service.generate_suggestions(all_messages + [assistant_message])

    return ChatResponse(
        conversation_id=conversation.id,
        message=MessageResponse.from_orm(assistant_message),
        suggestions=suggestions
    )


@router.post("/insights", response_model=InsightResponse)
async def get_insights(
    request: InsightRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get AI-powered insights based on platform data.
    """
    insights = await ai_service.generate_insights(
        db,
        str(current_user.organization_id),
        request.query,
        request.scope,
        str(request.entity_id) if request.entity_id else None,
        request.time_range
    )

    return InsightResponse(**insights)


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get messages for a specific conversation.
    """
    # Verify conversation ownership
    conv_query = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    )
    conv_result = await db.execute(conv_query)
    conversation = conv_result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    # Get messages
    query = select(Message).where(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at).offset(skip).limit(limit)

    result = await db.execute(query)
    messages = result.scalars().all()

    return messages
