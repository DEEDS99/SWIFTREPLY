"""Contacts management routes."""

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.database import get_db
from app.db.models import Contact, User
from app.middleware.auth import get_current_user

router = APIRouter()


class ContactCreate(BaseModel):
    phone_number: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    tags: Optional[list] = []


@router.get("")
async def list_contacts(
    search: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(Contact).where(Contact.organisation_id == current_user.organisation_id)
    if search:
        q = q.where(
            Contact.display_name.ilike(f"%{search}%") |
            Contact.phone_number.ilike(f"%{search}%")
        )
    q = q.order_by(Contact.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(q)
    contacts = result.scalars().all()
    return {"contacts": [
        {
            "id": str(c.id),
            "phone_number": c.phone_number,
            "display_name": c.display_name,
            "email": c.email,
            "company": c.company,
            "tags": c.tags or [],
            "is_blocked": c.is_blocked,
            "created_at": c.created_at.isoformat(),
        }
        for c in contacts
    ]}


@router.post("", status_code=201)
async def create_contact(
    body: ContactCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = await db.execute(
        select(Contact).where(
            Contact.organisation_id == current_user.organisation_id,
            Contact.phone_number == body.phone_number,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Contact with this phone number already exists")

    contact = Contact(
        organisation_id=current_user.organisation_id,
        **body.dict(),
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return {"id": str(contact.id), "phone_number": contact.phone_number}
