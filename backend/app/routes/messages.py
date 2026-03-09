"""Send outbound messages via Evolution API REST."""

import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.db.models import Conversation, Contact, Message, Organisation, MessageDirection, MessageType, MessageStatus, User
from app.services.evolution_service import EvolutionService
from app.middleware.auth import get_current_user

router = APIRouter()


class SendMessageRequest(BaseModel):
    conversation_id: str
    message_type: str = "text"
    body: Optional[str] = None
    media_url: Optional[str] = None


@router.post("/send")
async def send_message(
    body: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a message via Evolution API."""
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.id == body.conversation_id,
            Conversation.organisation_id == current_user.organisation_id,
        )
    )
    conv = conv_result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    contact_result = await db.execute(select(Contact).where(Contact.id == conv.contact_id))
    contact = contact_result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    org_result = await db.execute(select(Organisation).where(Organisation.id == current_user.organisation_id))
    org = org_result.scalar_one_or_none()

    evo = EvolutionService(
        base_url=org.evolution_url or os.getenv("EVOLUTION_API_URL", ""),
        api_key=org.evolution_api_key or os.getenv("EVOLUTION_API_KEY", ""),
        instance=org.evolution_instance or os.getenv("EVOLUTION_INSTANCE", "swiftreply"),
    )

    send_result = {}
    if body.message_type == "text" and body.body:
        send_result = await evo.send_text(to=contact.phone_number, text=body.body)
    elif body.message_type == "image" and body.media_url:
        send_result = await evo.send_image(to=contact.phone_number, image_url=body.media_url, caption=body.body)
    elif body.message_type == "audio" and body.media_url:
        send_result = await evo.send_audio(to=contact.phone_number, audio_url=body.media_url)
    elif body.message_type == "video" and body.media_url:
        send_result = await evo.send_video(to=contact.phone_number, video_url=body.media_url, caption=body.body)
    else:
        raise HTTPException(status_code=400, detail="Invalid type or missing content")

    if isinstance(send_result, dict) and send_result.get("error"):
        raise HTTPException(status_code=502, detail=f"Evolution error: {send_result['error']}")

    evo_msg_id = send_result.get("key", {}).get("id") if isinstance(send_result, dict) else None

    msg = Message(
        conversation_id=conv.id,
        whatsapp_message_id=evo_msg_id,
        direction=MessageDirection.outbound,
        message_type=MessageType(body.message_type) if body.message_type in MessageType.__members__ else MessageType.text,
        status=MessageStatus.sent,
        body=body.body,
        media_url=body.media_url,
        ai_generated=False,
    )
    db.add(msg)
    from datetime import datetime
    conv.last_message_at = datetime.utcnow()
    await db.commit()
    await db.refresh(msg)
    return {"id": str(msg.id), "status": "sent", "evolution_message_id": evo_msg_id}
