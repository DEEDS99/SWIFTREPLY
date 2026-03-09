"""Analytics dashboard endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta

from app.db.database import get_db
from app.db.models import Message, Conversation, Contact, AnalyticsEvent, MessageDirection, User
from app.middleware.auth import get_current_user

router = APIRouter()


@router.get("/summary")
async def analytics_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dashboard analytics summary."""
    org_id = current_user.organisation_id
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0)
    week_start = now - timedelta(days=7)
    month_start = now - timedelta(days=30)

    # Total conversations
    total_conv = await db.execute(
        select(func.count(Conversation.id)).where(Conversation.organisation_id == org_id)
    )
    # Open conversations
    open_conv = await db.execute(
        select(func.count(Conversation.id)).where(
            Conversation.organisation_id == org_id,
            Conversation.status == "open"
        )
    )
    # Total contacts
    total_contacts = await db.execute(
        select(func.count(Contact.id)).where(Contact.organisation_id == org_id)
    )
    # Messages today
    msgs_today = await db.execute(
        select(func.count(Message.id))
        .join(Conversation)
        .where(
            Conversation.organisation_id == org_id,
            Message.created_at >= today_start,
        )
    )
    # AI-generated messages this month
    ai_msgs = await db.execute(
        select(func.count(Message.id))
        .join(Conversation)
        .where(
            Conversation.organisation_id == org_id,
            Message.ai_generated == True,
            Message.created_at >= month_start,
        )
    )
    # Inbound vs outbound this week
    inbound_week = await db.execute(
        select(func.count(Message.id))
        .join(Conversation)
        .where(
            Conversation.organisation_id == org_id,
            Message.direction == MessageDirection.inbound,
            Message.created_at >= week_start,
        )
    )
    outbound_week = await db.execute(
        select(func.count(Message.id))
        .join(Conversation)
        .where(
            Conversation.organisation_id == org_id,
            Message.direction == MessageDirection.outbound,
            Message.created_at >= week_start,
        )
    )

    return {
        "total_conversations": total_conv.scalar() or 0,
        "open_conversations": open_conv.scalar() or 0,
        "total_contacts": total_contacts.scalar() or 0,
        "messages_today": msgs_today.scalar() or 0,
        "ai_messages_month": ai_msgs.scalar() or 0,
        "inbound_week": inbound_week.scalar() or 0,
        "outbound_week": outbound_week.scalar() or 0,
    }
