"""
SwiftReply — Evolution API Webhook Handler
==========================================
Receives events from a self-hosted Evolution API instance.
Evolution API uses WhatsApp Web protocol — no Meta approval needed.

Incoming event types handled:
  - messages.upsert   → new incoming message (text/image/audio/video/doc)
  - messages.update   → status updates (read/delivered)
  - connection.update → QR code, connect/disconnect events
  - qrcode.updated    → new QR code available
"""

import os
import logging
from datetime import datetime
from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.db.models import (
    Organisation, Contact, Conversation, Message, AnalyticsEvent,
    MessageDirection, MessageStatus, MessageType, ConversationStatus,
)
from app.services.evolution_service import EvolutionService, parse_evolution_webhook
from app.services.gemini_service import GeminiService
from app.services.websocket_manager import manager

router = APIRouter()
logger = logging.getLogger("swiftreply.evolution_webhook")


# ─── Webhook receiver ────────────────────────────────────────────────────────

@router.post("/evolution/webhook")
async def evolution_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Receive all Evolution API events.
    No signature verification header needed — secure via network/API key.
    """
    body = await request.json()

    parsed = parse_evolution_webhook(body)
    if not parsed:
        return {"status": "ignored"}

    event_type = parsed.get("event")

    if event_type == "message":
        await handle_incoming_message(db, parsed)

    elif event_type in ("connection_update", "qr_update"):
        await handle_connection_event(parsed)

    return {"status": "ok"}


# ─── Connection / QR events ──────────────────────────────────────────────────

async def handle_connection_event(parsed: dict):
    """Broadcast connection state and QR codes to all dashboard clients."""
    instance = parsed.get("instance", "")
    payload = {
        "type": "connection_update",
        "instance": instance,
        "state": parsed.get("state", ""),
        "qr": parsed.get("qr", ""),
    }
    # Broadcast to all orgs watching this instance
    for org_id in list(manager.active.keys()):
        await manager.broadcast_to_org(org_id, payload)
    logger.info(f"Connection update for {instance}: state={parsed.get('state')}")


# ─── Incoming message ────────────────────────────────────────────────────────

async def handle_incoming_message(db: AsyncSession, parsed: dict):
    instance = parsed["instance"]
    phone = parsed["phone"]
    contact_name = parsed.get("contact_name", phone)
    msg_type = parsed["type"]
    body_text = parsed.get("body", "")
    media_url = parsed.get("media_url", "")
    caption = parsed.get("caption", "")
    msg_id = parsed.get("message_id", "")
    remote_jid = parsed.get("remote_jid", "")
    raw_data = parsed.get("raw_data", {})

    # ── Find organisation by Evolution instance name ─────────────────
    result = await db.execute(
        select(Organisation).where(
            Organisation.evolution_instance == instance,
            Organisation.is_active == True,
        )
    )
    org = result.scalar_one_or_none()

    # Fallback: first active org
    if not org:
        result = await db.execute(
            select(Organisation).where(Organisation.is_active == True).limit(1)
        )
        org = result.scalar_one_or_none()

    if not org:
        logger.error(f"No org found for Evolution instance: {instance}")
        return

    # ── Contact ──────────────────────────────────────────────────────
    contact_result = await db.execute(
        select(Contact).where(
            Contact.organisation_id == org.id,
            Contact.phone_number == phone,
        )
    )
    contact = contact_result.scalar_one_or_none()
    if not contact:
        contact = Contact(
            organisation_id=org.id,
            phone_number=phone,
            display_name=contact_name,
        )
        db.add(contact)
        await db.flush()
    elif contact_name and not contact.display_name:
        contact.display_name = contact_name

    # ── Conversation ─────────────────────────────────────────────────
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.organisation_id == org.id,
            Conversation.contact_id == contact.id,
            Conversation.status.in_(["open", "pending", "assigned"]),
        ).order_by(Conversation.last_message_at.desc())
    )
    conv = conv_result.scalar_one_or_none()
    if not conv:
        conv = Conversation(
            organisation_id=org.id,
            contact_id=contact.id,
            status=ConversationStatus.open,
        )
        db.add(conv)
        await db.flush()

    conv.unread_count = (conv.unread_count or 0) + 1
    conv.last_message_at = datetime.utcnow()

    # ── Save inbound message ─────────────────────────────────────────
    inbound = Message(
        conversation_id=conv.id,
        whatsapp_message_id=msg_id,
        direction=MessageDirection.inbound,
        message_type=MessageType(msg_type) if msg_type in MessageType.__members__ else MessageType.text,
        status=MessageStatus.delivered,
        body=body_text,
        media_url=media_url,
        metadata_=raw_data,
    )
    db.add(inbound)
    await db.flush()

    # ── Download and process media if needed ────────────────────────
    content = {"body": body_text, "url": media_url, "caption": caption}

    if msg_type in ("image", "audio", "video") and not media_url:
        # Try to get base64 media from Evolution for Gemini
        evo = EvolutionService(
            base_url=org.evolution_url or os.getenv("EVOLUTION_API_URL"),
            api_key=org.evolution_api_key or os.getenv("EVOLUTION_API_KEY"),
            instance=instance,
        )
        media_result = await evo.download_media_base64(
            message={"key": {"id": msg_id, "remoteJid": remote_jid, "fromMe": False},
                     "message": parsed.get("raw_message", {})},
            instance=instance,
        )
        if media_result and media_result.get("base64"):
            # Save locally
            import base64 as b64mod
            media_bytes = b64mod.b64decode(media_result["base64"])
            ext_map = {"image": "jpg", "audio": "ogg", "video": "mp4"}
            ext = ext_map.get(msg_type, "bin")
            os.makedirs(f"uploads/{org.id}", exist_ok=True)
            filepath = f"uploads/{org.id}/{msg_id}.{ext}"
            with open(filepath, "wb") as f:
                f.write(media_bytes)
            backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
            media_url = f"{backend_url}/{filepath}"
            inbound.media_url = media_url
            content["url"] = media_url

    # ── AI reply ────────────────────────────────────────────────────
    if org.ai_enabled:
        hist_result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conv.id)
            .order_by(Message.created_at.desc())
            .limit(15)
        )
        history = [
            {"direction": m.direction, "body": m.body or ""}
            for m in reversed(hist_result.scalars().all())
        ]

        gemini = GeminiService(api_key=org.gemini_api_key or os.getenv("GEMINI_API_KEY"))
        system_prompt = org.ai_system_prompt or "You are a helpful business assistant."

        ai_result = await gemini.process_incoming_message(
            message_type=msg_type,
            content=content,
            conversation_history=history,
            system_prompt=system_prompt,
            contact_name=contact.display_name or phone,
            org_api_key=org.gemini_api_key,
        )

        if ai_result.get("success") and ai_result.get("reply"):
            reply_text = ai_result["reply"]

            # Send via Evolution API
            evo = EvolutionService(
                base_url=org.evolution_url or os.getenv("EVOLUTION_API_URL"),
                api_key=org.evolution_api_key or os.getenv("EVOLUTION_API_KEY"),
                instance=org.evolution_instance or instance,
            )
            send_result = await evo.send_text(
                to=phone,
                text=reply_text,
                reply_to=msg_id,
                instance=org.evolution_instance or instance,
            )

            reply_msg_id = send_result.get("key", {}).get("id") if isinstance(send_result, dict) else None

            outbound = Message(
                conversation_id=conv.id,
                whatsapp_message_id=reply_msg_id,
                direction=MessageDirection.outbound,
                message_type=MessageType.text,
                status=MessageStatus.sent,
                body=reply_text,
                ai_generated=True,
                ai_analysis=ai_result.get("ai_analysis"),
                ai_confidence=ai_result.get("confidence", 85),
                reply_to_id=inbound.id,
            )
            db.add(outbound)

    await db.commit()

    # ── Analytics ────────────────────────────────────────────────────
    event = AnalyticsEvent(
        organisation_id=org.id,
        event_type="message_received",
        event_data={"type": msg_type, "contact": phone, "instance": instance},
    )
    db.add(event)
    await db.commit()

    # ── Real-time broadcast ──────────────────────────────────────────
    await manager.broadcast_to_org(str(org.id), {
        "type": "new_message",
        "conversation_id": str(conv.id),
        "contact_name": contact.display_name or phone,
        "contact_phone": phone,
        "message_type": msg_type,
        "body": body_text,
        "ai_replied": org.ai_enabled,
    })


# ─── Instance management endpoints ──────────────────────────────────────────

@router.get("/evolution/qr/{instance_name}")
async def get_qr_code(
    instance_name: str,
    db: AsyncSession = Depends(get_db),
):
    """Get QR code for pairing a WhatsApp number with an Evolution instance."""
    evo = EvolutionService()
    result = await evo.get_qr_code(instance=instance_name)
    return result


@router.get("/evolution/status/{instance_name}")
async def get_instance_status(
    instance_name: str,
    db: AsyncSession = Depends(get_db),
):
    """Get connection status for an Evolution instance."""
    evo = EvolutionService()
    result = await evo.get_connection_state(instance=instance_name)
    return result


@router.post("/evolution/instance/create")
async def create_instance(
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    """Create a new Evolution API instance."""
    from app.middleware.auth import get_current_user
    evo = EvolutionService()
    instance_name = body.get("instance_name", "swiftreply")
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    webhook_url = f"{backend_url}/api/evolution/webhook"
    result = await evo.create_instance(instance_name, webhook_url)
    return result
