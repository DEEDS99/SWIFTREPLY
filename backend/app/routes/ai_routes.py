"""AI-powered reply generation endpoints."""

import os
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.db.models import Conversation, Message, Organisation, User
from app.services.gemini_service import GeminiService
from app.middleware.auth import get_current_user

router = APIRouter()


class GenerateReplyRequest(BaseModel):
    conversation_id: str
    instruction: Optional[str] = None


@router.post("/generate-reply")
async def generate_reply(
    body: GenerateReplyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually trigger AI reply generation for a conversation."""
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.id == body.conversation_id,
            Conversation.organisation_id == current_user.organisation_id,
        )
    )
    conv = conv_result.scalar_one_or_none()
    if not conv:
        from fastapi import HTTPException
        raise HTTPException(404, "Conversation not found")

    org_result = await db.execute(select(Organisation).where(Organisation.id == current_user.organisation_id))
    org = org_result.scalar_one_or_none()

    hist_result = await db.execute(
        select(Message).where(Message.conversation_id == conv.id)
        .order_by(Message.created_at.desc()).limit(10)
    )
    history = [
        {"direction": m.direction, "body": m.body or ""}
        for m in reversed(hist_result.scalars().all())
    ]

    system_prompt = body.instruction or org.ai_system_prompt or "You are a helpful business assistant."
    gemini = GeminiService(api_key=org.gemini_api_key or os.getenv("GEMINI_API_KEY"))

    result = await gemini.generate_text_reply(
        incoming_text=history[-1].get("body", "") if history else "",
        conversation_history=history[:-1],
        system_prompt=system_prompt,
        contact_name="Customer",
    )

    return {"suggested_reply": result.get("reply"), "success": result.get("success")}
