"""
SwiftReply Database Models
All tables with created_at/updated_at timestamps.
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Boolean, DateTime, Integer,
    ForeignKey, Enum, JSON, BigInteger
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

from app.db.database import Base


class OrgPlan(str, enum.Enum):
    starter = "starter"
    professional = "professional"
    enterprise = "enterprise"


class MessageType(str, enum.Enum):
    text = "text"
    image = "image"
    audio = "audio"
    video = "video"
    document = "document"
    sticker = "sticker"
    location = "location"
    template = "template"


class MessageDirection(str, enum.Enum):
    inbound = "inbound"
    outbound = "outbound"


class MessageStatus(str, enum.Enum):
    pending = "pending"
    sent = "sent"
    delivered = "delivered"
    read = "read"
    failed = "failed"


class ConversationStatus(str, enum.Enum):
    open = "open"
    resolved = "resolved"
    pending = "pending"
    assigned = "assigned"


# ─── Organisation ──────────────────────────────────────────

class Organisation(Base):
    __tablename__ = "organisations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    plan = Column(Enum(OrgPlan), default=OrgPlan.starter, nullable=False)
    # Meta WhatsApp Cloud API (legacy / optional)
    whatsapp_phone_id = Column(String(100))
    whatsapp_token = Column(Text)
    whatsapp_verify_token = Column(String(255))

    # Evolution API (primary — WhatsApp Web protocol, ToS-compliant)
    evolution_url = Column(Text)             # e.g. https://evo.myserver.com
    evolution_api_key = Column(Text)         # Evolution global API key
    evolution_instance = Column(String(255)) # e.g. "swiftreply-org1"
    evolution_connected = Column(Boolean, default=False)

    gemini_api_key = Column(Text)
    ai_enabled = Column(Boolean, default=True)
    ai_system_prompt = Column(Text, default="You are a helpful business assistant. Reply professionally and concisely.")
    monthly_message_limit = Column(Integer, default=1000)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    users = relationship("User", back_populates="organisation")
    contacts = relationship("Contact", back_populates="organisation")
    conversations = relationship("Conversation", back_populates="organisation")
    templates = relationship("MessageTemplate", back_populates="organisation")


# ─── User ──────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    agent = "agent"
    viewer = "viewer"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.agent, nullable=False)
    avatar_url = Column(Text)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    organisation = relationship("Organisation", back_populates="users")
    assigned_conversations = relationship("Conversation", back_populates="assigned_agent")


# ─── Contact ───────────────────────────────────────────────

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    phone_number = Column(String(30), nullable=False)  # E.164 format
    display_name = Column(String(255))
    email = Column(String(255))
    company = Column(String(255))
    tags = Column(JSON, default=list)
    custom_fields = Column(JSON, default=dict)
    is_blocked = Column(Boolean, default=False)
    opted_out = Column(Boolean, default=False)
    total_messages = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    organisation = relationship("Organisation", back_populates="contacts")
    conversations = relationship("Conversation", back_populates="contact")


# ─── Conversation ──────────────────────────────────────────

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=False)
    assigned_agent_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    status = Column(Enum(ConversationStatus), default=ConversationStatus.open)
    last_message_at = Column(DateTime, default=datetime.utcnow)
    unread_count = Column(Integer, default=0)
    subject = Column(String(500))
    labels = Column(JSON, default=list)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    organisation = relationship("Organisation", back_populates="conversations")
    contact = relationship("Contact", back_populates="conversations")
    assigned_agent = relationship("User", back_populates="assigned_conversations")
    messages = relationship("Message", back_populates="conversation", order_by="Message.created_at")


# ─── Message ───────────────────────────────────────────────

class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    whatsapp_message_id = Column(String(255), unique=True)  # Meta's message ID
    direction = Column(Enum(MessageDirection), nullable=False)
    message_type = Column(Enum(MessageType), default=MessageType.text)
    status = Column(Enum(MessageStatus), default=MessageStatus.pending)

    # Content
    body = Column(Text)                    # Text content or AI transcription
    media_url = Column(Text)               # URL to media file
    media_mime_type = Column(String(100))
    media_filename = Column(String(500))
    media_size = Column(BigInteger)

    # AI processing
    ai_generated = Column(Boolean, default=False)
    ai_analysis = Column(Text)             # Gemini's analysis of media
    ai_confidence = Column(Integer)        # 0-100

    # Template
    template_name = Column(String(255))
    template_params = Column(JSON, default=list)

    # Reply
    reply_to_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=True)

    metadata_ = Column("metadata", JSON, default=dict)  # Raw WhatsApp payload
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    conversation = relationship("Conversation", back_populates="messages")
    reply_to = relationship("Message", remote_side=[id])


# ─── Message Template ──────────────────────────────────────

class MessageTemplate(Base):
    __tablename__ = "message_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(100))         # MARKETING, UTILITY, AUTHENTICATION
    language = Column(String(10), default="en")
    body = Column(Text, nullable=False)
    header = Column(Text)
    footer = Column(Text)
    variables = Column(JSON, default=list) # ["{{1}}", "{{2}}"]
    whatsapp_template_id = Column(String(255))
    status = Column(String(50), default="draft")  # draft, submitted, approved, rejected
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    organisation = relationship("Organisation", back_populates="templates")


# ─── Analytics Event ───────────────────────────────────────

class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    event_type = Column(String(100), nullable=False)  # message_sent, message_received, etc.
    event_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
