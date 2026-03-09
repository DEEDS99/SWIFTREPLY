"""Message templates routes."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.db.models import MessageTemplate, User
from app.middleware.auth import get_current_user

router = APIRouter()


class TemplateCreate(BaseModel):
    name: str
    body: str
    category: Optional[str] = "UTILITY"
    language: Optional[str] = "en"
    header: Optional[str] = None
    footer: Optional[str] = None
    variables: Optional[list] = []


@router.get("")
async def list_templates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(MessageTemplate).where(
            MessageTemplate.organisation_id == current_user.organisation_id,
            MessageTemplate.is_active == True,
        ).order_by(MessageTemplate.created_at.desc())
    )
    templates = result.scalars().all()
    return {"templates": [
        {
            "id": str(t.id),
            "name": t.name,
            "body": t.body,
            "category": t.category,
            "language": t.language,
            "header": t.header,
            "footer": t.footer,
            "variables": t.variables or [],
            "status": t.status,
        }
        for t in templates
    ]}


@router.post("", status_code=201)
async def create_template(
    body: TemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    template = MessageTemplate(
        organisation_id=current_user.organisation_id,
        **body.dict(),
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return {"id": str(template.id), "name": template.name}


@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(MessageTemplate).where(
            MessageTemplate.id == template_id,
            MessageTemplate.organisation_id == current_user.organisation_id,
        )
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(404, "Template not found")
    template.is_active = False
    await db.commit()
    return {"deleted": True}
