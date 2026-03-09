"""
SwiftReply — Broadcast Campaigns
=================================
Send bulk messages to multiple contacts via Evolution API.
Supports text, image, video, document broadcasts with progress tracking.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import get_db
from app.db.models import Contact, Organisation, AnalyticsEvent, User
from app.services.evolution_service import EvolutionService
from app.services.websocket_manager import manager
from app.middleware.auth import get_current_user

router = APIRouter()
logger = logging.getLogger("swiftreply.broadcast")

# In-memory campaign progress store (use Redis in production for multi-instance)
_campaign_progress: dict = {}


# ── DB Model (inline for simplicity — uses raw SQL via SQLAlchemy text) ──────

class CampaignCreate(BaseModel):
    name: str
    message_body: str
    message_type: str = "text"
    media_url: Optional[str] = None
    contact_ids: Optional[list] = None   # None = all contacts
    tags: Optional[list] = None          # filter by tag
    scheduled_at: Optional[str] = None


# ── Background sender ─────────────────────────────────────────────────────────

async def send_broadcast_job(
    campaign_id: str,
    org_id: str,
    contacts: list,
    message_body: str,
    message_type: str,
    media_url: Optional[str],
    evo: EvolutionService,
    db_url: str,
):
    """Background task: sends messages to all contacts with rate limiting."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    engine = create_async_engine(db_url.replace("postgresql://", "postgresql+asyncpg://").replace("postgres://", "postgresql+asyncpg://"))
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    total = len(contacts)
    sent = 0
    failed = 0

    _campaign_progress[campaign_id] = {
        "status": "running",
        "total": total,
        "sent": 0,
        "failed": 0,
        "started_at": datetime.utcnow().isoformat(),
    }

    for contact in contacts:
        phone = contact.get("phone_number") or contact.get("phone")
        if not phone:
            failed += 1
            continue
        try:
            if message_type == "text":
                result = await evo.send_text(to=phone, text=message_body)
            elif message_type == "image" and media_url:
                result = await evo.send_image(to=phone, image_url=media_url, caption=message_body)
            elif message_type == "video" and media_url:
                result = await evo.send_video(to=phone, video_url=media_url, caption=message_body)
            elif message_type == "document" and media_url:
                result = await evo.send_document(to=phone, doc_url=media_url, filename="document")
            else:
                result = await evo.send_text(to=phone, text=message_body)

            if result.get("error"):
                failed += 1
            else:
                sent += 1

        except Exception as e:
            logger.error(f"Broadcast send error for {phone}: {e}")
            failed += 1

        _campaign_progress[campaign_id].update({"sent": sent, "failed": failed})

        # Broadcast progress via WebSocket
        await manager.broadcast_to_org(org_id, {
            "type": "broadcast_progress",
            "campaign_id": campaign_id,
            "sent": sent,
            "failed": failed,
            "total": total,
            "percent": round((sent + failed) / total * 100),
        })

        # Rate limit: ~1 msg/second to avoid WhatsApp bans
        await asyncio.sleep(1.1)

    _campaign_progress[campaign_id].update({
        "status": "completed",
        "completed_at": datetime.utcnow().isoformat(),
    })

    # Final WebSocket push
    await manager.broadcast_to_org(org_id, {
        "type": "broadcast_complete",
        "campaign_id": campaign_id,
        "sent": sent,
        "failed": failed,
        "total": total,
    })

    # Log analytics
    async with SessionLocal() as session:
        event = AnalyticsEvent(
            organisation_id=org_id,
            event_type="broadcast_completed",
            event_data={"campaign_id": campaign_id, "sent": sent, "failed": failed, "total": total},
        )
        session.add(event)
        await session.commit()

    await engine.dispose()
    logger.info(f"Broadcast {campaign_id} done: {sent}/{total} sent, {failed} failed")


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("", status_code=202)
async def create_and_send_broadcast(
    body: CampaignCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a broadcast campaign and start sending immediately (or schedule).
    Returns campaign_id for progress tracking via WebSocket or polling.
    """
    org_result = await db.execute(
        select(Organisation).where(Organisation.id == current_user.organisation_id)
    )
    org = org_result.scalar_one_or_none()
    if not org:
        raise HTTPException(404, "Organisation not found")

    # Build contact list
    q = select(Contact).where(
        Contact.organisation_id == current_user.organisation_id,
        Contact.is_blocked == False,
        Contact.opted_out == False,
    )
    if body.contact_ids:
        q = q.where(Contact.id.in_(body.contact_ids))
    if body.tags:
        # JSONB contains-any filter
        q = q.where(Contact.tags.op("?|")(body.tags))

    result = await db.execute(q)
    contacts_db = result.scalars().all()

    if not contacts_db:
        raise HTTPException(400, "No eligible contacts found for this broadcast")

    contacts = [{"phone_number": c.phone_number, "name": c.display_name} for c in contacts_db]
    campaign_id = str(uuid4())

    evo = EvolutionService(
        base_url=org.evolution_url or os.getenv("EVOLUTION_API_URL", ""),
        api_key=org.evolution_api_key or os.getenv("EVOLUTION_API_KEY", ""),
        instance=org.evolution_instance or os.getenv("EVOLUTION_INSTANCE", "swiftreply"),
    )

    from app.db.database import ASYNC_DATABASE_URL
    background_tasks.add_task(
        send_broadcast_job,
        campaign_id=campaign_id,
        org_id=str(current_user.organisation_id),
        contacts=contacts,
        message_body=body.message_body,
        message_type=body.message_type,
        media_url=body.media_url,
        evo=evo,
        db_url=ASYNC_DATABASE_URL,
    )

    _campaign_progress[campaign_id] = {
        "status": "queued",
        "total": len(contacts),
        "sent": 0,
        "failed": 0,
    }

    return {
        "campaign_id": campaign_id,
        "status": "queued",
        "total_recipients": len(contacts),
        "message": f"Broadcasting to {len(contacts)} contacts. Track progress via WebSocket or GET /broadcasts/{campaign_id}/progress",
    }


@router.get("/{campaign_id}/progress")
async def get_campaign_progress(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
):
    """Poll broadcast campaign progress."""
    progress = _campaign_progress.get(campaign_id)
    if not progress:
        raise HTTPException(404, "Campaign not found or expired")
    return progress


@router.get("")
async def list_recent_broadcasts(
    current_user: User = Depends(get_current_user),
):
    """List recent broadcast campaign statuses (in-memory, last 50)."""
    return {
        "campaigns": [
            {"id": k, **v}
            for k, v in list(_campaign_progress.items())[-50:]
        ]
    }
