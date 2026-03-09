"""Conversation list and detail endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.db.models import Conversation, Contact, Message, User
from app.middleware.auth import get_current_user

router = APIRouter()


@router.get("")
async def list_conversations(
    status: str = Query(None),
    search: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List conversations for the current organisation."""
    q = (
        select(Conversation)
        .where(Conversation.organisation_id == current_user.organisation_id)
        .options(selectinload(Conversation.contact))
        .order_by(Conversation.last_message_at.desc())
    )
    if status:
        q = q.where(Conversation.status == status)

    offset = (page - 1) * limit
    result = await db.execute(q.offset(offset).limit(limit))
    convs = result.scalars().all()

    # Get latest message for each
    items = []
    for conv in convs:
        last_msg_result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conv.id)
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        last_msg = last_msg_result.scalar_one_or_none()
        items.append({
            "id": str(conv.id),
            "status": conv.status,
            "unread_count": conv.unread_count,
            "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None,
            "contact": {
                "id": str(conv.contact.id),
                "name": conv.contact.display_name or conv.contact.phone_number,
                "phone": conv.contact.phone_number,
            } if conv.contact else None,
            "last_message": {
                "body": last_msg.body,
                "type": last_msg.message_type,
                "direction": last_msg.direction,
                "created_at": last_msg.created_at.isoformat(),
            } if last_msg else None,
        })

    return {"conversations": items, "page": page, "limit": limit}


@router.get("/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get messages for a specific conversation."""
    # Verify ownership
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.organisation_id == current_user.organisation_id,
        )
    )
    conv = conv_result.scalar_one_or_none()
    if not conv:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Reset unread
    conv.unread_count = 0
    await db.commit()

    offset = (page - 1) * limit
    msgs_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .offset(offset).limit(limit)
    )
    msgs = msgs_result.scalars().all()

    return {
        "messages": [
            {
                "id": str(m.id),
                "direction": m.direction,
                "type": m.message_type,
                "status": m.status,
                "body": m.body,
                "media_url": m.media_url,
                "ai_generated": m.ai_generated,
                "ai_analysis": m.ai_analysis,
                "created_at": m.created_at.isoformat(),
            }
            for m in msgs
        ]
    }


@router.patch("/{conversation_id}/status")
async def update_conversation_status(
    conversation_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update conversation status (open/resolved/pending)."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.organisation_id == current_user.organisation_id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not found")

    from app.db.models import ConversationStatus
    from datetime import datetime
    new_status = body.get("status")
    if new_status:
        conv.status = new_status
        if new_status == "resolved":
            conv.resolved_at = datetime.utcnow()
    await db.commit()
    return {"status": conv.status}
