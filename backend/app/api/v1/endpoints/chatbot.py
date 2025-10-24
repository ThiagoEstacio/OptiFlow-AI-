"""ChatBot API"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.api.deps import get_current_user
from app.models.user import User
from app.services.chatbot_service import chatbot_service
from app.services.plc_service import plc_service
from app.api.v1.endpoints.smartport_dashboard import dashboardApi

router = APIRouter()

class ChatMessage(BaseModel):
    message: str
    include_context: bool = True

@router.post("/chat")
async def chat(
    data: ChatMessage,
    current_user: User = Depends(get_current_user)
):
    """Send message to chatbot"""
    context = None
    if data.include_context:
        # Gather context
        plc_data = await plc_service.read_all_tags()
        context = {"plc_data": plc_data}

    response = await chatbot_service.chat(
        user_id=str(current_user.id),
        message=data.message,
        context=context
    )
    return {"response": response}

@router.get("/history")
async def get_chat_history(current_user: User = Depends(get_current_user)):
    """Get conversation history"""
    history = chatbot_service.get_conversation(str(current_user.id))
    return {"history": history}

@router.delete("/history")
async def clear_chat_history(current_user: User = Depends(get_current_user)):
    """Clear conversation history"""
    chatbot_service.clear_conversation(str(current_user.id))
    return {"status": "cleared"}
