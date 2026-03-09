"""
SwiftReply — WhatsApp Webhook Handler
=====================================
Processes ALL incoming WhatsApp messages:
- Text, Image, Audio, Video, Document
- Saves to DB, triggers Gemini AI, sends reply
- Broadcasts to WebSocket clients in real-time
"""

import os
import logging
from datetime import datetime
from fastapi import APIRouter, Request, Response, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import httpx

from app.db.database import get_db
from app.db.models import (
    Organisation, Contact, Conversation, Message, AnalyticsEvent,
    MessageDirection, MessageStatus, MessageType, ConversationStatus
)
from app.services.gemini_service import GeminiService
from app.services.whatsapp_service import WhatsAppService
from app.services.websocket_manager import manager

router = APIRouter()
logger = logging.getLogger("swiftreply.webhook")


async def get_or_create_contact(db: AsyncSession, org_id, phone: str, name: str = None) -> Contact:
    result = await db.execute(
        select(Contact).where(Contact.organisation_id == org_id, Contact.phone_number == phone)
    )
    contact = result.scalar_one_or_none()
    if not contact:
        contact = Contact(
            organisation_id=org_id,
            phone_number=phone,
            display_name=name or phone,
        )
        db.add(contact)
        await db.flush()
    elif name and not contact.display_name:
        contact.display_name = name
    return contact


async def get_or_create_conversation(db: AsyncSession, org_id, contact_id) -> Conversation:
    result = await db.execute(
        select(Conversation).where(
            Conversation.organisation_id == org_id,
            Conversation.contact_id == contact_id,
            Conversation.status.in_(["open", "pending", "assigned"])
        ).order_by(Conversation.last_message_at.desc())
    )
    conv = result.scalar_one_or_none()
    if not conv:
        conv = Conversation(
            organisation_id=org_id,
            contact_id=contact_id,
            status=ConversationStatus.open,
        )
        db.add(conv)
        await db.flush()
    return conv


async def download_media_to_storage(media_id: str, token: str, org_id: str) -> str:
    """Download media from Meta and save locally. Returns URL."""
    wa = WhatsAppService(token=token)
    data = await wa.download_media(media_id, token=token)
    if not data:
        return ""
    os.makedirs(f"uploads/{org_id}", exist_ok=True)
    filename = f"uploads/{org_id}/{media_id}"
    with open(filename, "wb") as f:
        f.write(data)
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    return f"{backend_url}/{filename}"


@router.get("/webhook")
async def verify_webhook(request: Request):
    """Meta webhook verification challenge."""
    params = dict(request.query_params)
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    # Try to find org by verify token
    if mode == "subscribe":
        verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN")
        if token == verify_token:
            logger.info("Webhook verified successfully")
            return Response(content=challenge, media_type="text/plain")

    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def receive_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Receive and process WhatsApp webhook events.
    Handles: messages (text/image/audio/video/document), status updates.
    """
    body = await request.json()

    try:
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages_data = value.get("messages", [])
        statuses = value.get("statuses", [])

        # Handle status updates (delivered, read, failed)
        for status_update in statuses:
            await handle_status_update(db, status_update)

        # Handle incoming messages
        for msg_data in messages_data:
            await process_incoming_message(db, value, msg_data)

    except Exception as e:
        logger.error(f"Webhook processing error: {e}", exc_info=True)

    return {"status": "ok"}


async def handle_status_update(db: AsyncSession, status_data: dict):
    """Update message delivery status in DB."""
    wa_msg_id = status_data.get("id")
    status_str = status_data.get("status")

    status_map = {
        "sent": MessageStatus.sent,
        "delivered": MessageStatus.delivered,
        "read": MessageStatus.read,
        "failed": MessageStatus.failed,
    }
    new_status = status_map.get(status_str)
    if not new_status:
        return

    result = await db.execute(
        select(Message).where(Message.whatsapp_message_id == wa_msg_id)
    )
    msg = result.scalar_one_or_none()
    if msg:
        msg.status = new_status
        await db.commit()


async def process_incoming_message(db: AsyncSession, value: dict, msg_data: dict):
    """Process a single incoming WhatsApp message."""
    phone_number_id = value.get("metadata", {}).get("phone_number_id", "")
    profile = value.get("contacts", [{}])[0].get("profile", {})
    contact_name = profile.get("name", "")
    from_number = msg_data.get("from", "")
    wa_msg_id = msg_data.get("id", "")
    msg_type = msg_data.get("type", "text")
    timestamp = msg_data.get("timestamp")

    # Find organisation by phone_id
    result = await db.execute(
        select(Organisation).where(
            Organisation.whatsapp_phone_id == phone_number_id,
            Organisation.is_active == True,
        )
    )
    org = result.scalar_one_or_none()

    # Fallback: use default org (first active)
    if not org:
        result = await db.execute(
            select(Organisation).where(Organisation.is_active == True).limit(1)
        )
        org = result.scalar_one_or_none()

    if not org:
        logger.error(f"No organisation found for phone_id {phone_number_id}")
        return

    org_token = org.whatsapp_token or os.getenv("WHATSAPP_TOKEN")
    org_phone_id = org.whatsapp_phone_id or phone_number_id

    # Get or create contact
    contact = await get_or_create_contact(db, org.id, from_number, contact_name)

    # Get or create conversation
    conv = await get_or_create_conversation(db, org.id, contact.id)
    conv.unread_count = (conv.unread_count or 0) + 1
    conv.last_message_at = datetime.utcnow()

    # Parse message content
    content = {}
    body_text = ""
    media_url = ""

    if msg_type == "text":
        body_text = msg_data.get("text", {}).get("body", "")
        content = {"body": body_text}

    elif msg_type in ("image", "video", "audio", "document", "sticker"):
        media_data = msg_data.get(msg_type, {})
        media_id = media_data.get("id", "")
        caption = media_data.get("caption", "")
        mime_type = media_data.get("mime_type", "")
        filename = media_data.get("filename", "")

        # Download and store media
        if media_id:
            media_url = await download_media_to_storage(media_id, org_token, str(org.id))

        content = {
            "url": media_url,
            "caption": caption,
            "mime_type": mime_type,
            "filename": filename,
        }
        body_text = caption or f"[{msg_type} message]"

    # Save inbound message
    inbound_msg = Message(
        conversation_id=conv.id,
        whatsapp_message_id=wa_msg_id,
        direction=MessageDirection.inbound,
        message_type=MessageType(msg_type) if msg_type in MessageType.__members__ else MessageType.text,
        status=MessageStatus.delivered,
        body=body_text,
        media_url=media_url,
        metadata_=msg_data,
    )
    db.add(inbound_msg)
    await db.flush()

    # Mark as read on WhatsApp
    wa = WhatsAppService(token=org_token, phone_id=org_phone_id)
    await wa.mark_message_read(wa_msg_id, token=org_token, phone_id=org_phone_id)

    # --- AI REPLY ---
    if org.ai_enabled:
        # Get conversation history
        hist_result = await db.execute(
            select(Message).where(Message.conversation_id == conv.id)
            .order_by(Message.created_at.desc()).limit(15)
        )
        history_msgs = hist_result.scalars().all()
        history = [
            {"direction": m.direction, "body": m.body or ""}
            for m in reversed(history_msgs)
        ]

        gemini = GeminiService(api_key=org.gemini_api_key or os.getenv("GEMINI_API_KEY"))
        system_prompt = org.ai_system_prompt or "You are a helpful business assistant."

        ai_result = await gemini.process_incoming_message(
            message_type=msg_type,
            content=content,
            conversation_history=history,
            system_prompt=system_prompt,
            contact_name=contact.display_name or from_number,
            org_api_key=org.gemini_api_key,
        )

        if ai_result.get("success") and ai_result.get("reply"):
            reply_text = ai_result["reply"]

            # Send reply via WhatsApp
            send_result = await wa.send_text_message(
                to=from_number,
                text=reply_text,
                reply_to_id=wa_msg_id,
                token=org_token,
                phone_id=org_phone_id,
            )

            reply_wa_id = send_result.get("messages", [{}])[0].get("id")

            # Save outbound AI message
            outbound_msg = Message(
                conversation_id=conv.id,
                whatsapp_message_id=reply_wa_id,
                direction=MessageDirection.outbound,
                message_type=MessageType.text,
                status=MessageStatus.sent,
                body=reply_text,
                ai_generated=True,
                ai_analysis=ai_result.get("ai_analysis"),
                ai_confidence=ai_result.get("confidence", 85),
                reply_to_id=inbound_msg.id,
            )
            db.add(outbound_msg)

    await db.commit()

    # Track analytics
    event = AnalyticsEvent(
        organisation_id=org.id,
        event_type="message_received",
        event_data={"type": msg_type, "contact": from_number},
    )
    db.add(event)
    await db.commit()

    # Broadcast to WebSocket clients
    await manager.broadcast_to_org(str(org.id), {
        "type": "new_message",
        "conversation_id": str(conv.id),
        "contact_name": contact.display_name,
        "message_type": msg_type,
        "body": body_text,
    })
