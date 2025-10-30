"""
Chat and Conversation models
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


class Conversation(Base):
    """
    Conversation - Chat conversation session
    """
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Conversation metadata
    title = Column(String(255), nullable=True)  # Auto-generated or user-defined
    is_active = Column(Boolean, default=True, nullable=False)

    # Context and settings
    context_tags = Column(JSONB, default=list, nullable=False)  # List of tag IDs relevant to this conversation
    settings = Column(JSONB, default=dict, nullable=False)
    # Settings example:
    # {
    #   "llm_provider": "openai",
    #   "model": "gpt-4-turbo",
    #   "temperature": 0.7,
    #   "include_context": true
    # }

    # Statistics
    message_count = Column(Integer, default=0, nullable=False)
    last_message_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="ChatMessage.created_at")

    def __repr__(self):
        return f"<Conversation {self.id} (user: {self.user_id})>"


class ChatMessage(Base):
    """
    ChatMessage - Individual message in a conversation
    """
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Message content
    role = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)

    # Metadata
    metadata = Column(JSONB, default=dict, nullable=False)
    # Metadata example:
    # {
    #   "context_used": true,
    #   "relevant_tags": ["tag1", "tag2"],
    #   "command": "/analyze",
    #   "processing_time_ms": 523,
    #   "tokens_used": 150
    # }

    # Context snapshot (what data was available when this message was sent)
    context_snapshot = Column(JSONB, default=dict, nullable=False)

    # User feedback
    feedback = Column(String(20), nullable=True)  # helpful, not_helpful, null
    feedback_comment = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        return f"<ChatMessage {self.id} ({self.role})>"


class ChatTemplate(Base):
    """
    ChatTemplate - Predefined chat templates and prompts
    """
    __tablename__ = "chat_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Template info
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, index=True)  # analysis, troubleshooting, optimization, etc.

    # Template content
    system_prompt = Column(Text, nullable=False)
    example_questions = Column(JSONB, default=list, nullable=False)  # List of example questions

    # Settings
    recommended_settings = Column(JSONB, default=dict, nullable=False)
    # Example:
    # {
    #   "temperature": 0.5,
    #   "include_context": true,
    #   "max_tokens": 1000
    # }

    # Usage tracking
    usage_count = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<ChatTemplate {self.name}>"


class ChatAnalytics(Base):
    """
    ChatAnalytics - Analytics for chat usage
    """
    __tablename__ = "chat_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Time period
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    period_type = Column(String(20), nullable=False)  # hourly, daily, weekly

    # Usage metrics
    total_conversations = Column(Integer, default=0, nullable=False)
    total_messages = Column(Integer, default=0, nullable=False)
    active_users = Column(Integer, default=0, nullable=False)

    # Message breakdown
    user_messages = Column(Integer, default=0, nullable=False)
    assistant_messages = Column(Integer, default=0, nullable=False)
    command_uses = Column(JSONB, default=dict, nullable=False)  # {"analyze": 45, "forecast": 23, ...}

    # Performance metrics
    avg_response_time_ms = Column(Integer, nullable=True)
    avg_tokens_per_message = Column(Integer, nullable=True)

    # Feedback metrics
    helpful_count = Column(Integer, default=0, nullable=False)
    not_helpful_count = Column(Integer, default=0, nullable=False)

    # Top topics
    top_tags_queried = Column(JSONB, default=list, nullable=False)  # List of most queried tags
    top_categories = Column(JSONB, default=dict, nullable=False)  # Category usage counts

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<ChatAnalytics {self.date} ({self.period_type})>"
