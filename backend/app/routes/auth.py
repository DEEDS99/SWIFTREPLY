"""Authentication routes — register organisation and login."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
import re

from app.db.database import get_db
from app.db.models import Organisation, User, UserRole
from app.middleware.auth import hash_password, verify_password, create_access_token

router = APIRouter()


class RegisterRequest(BaseModel):
    org_name: str
    email: EmailStr
    password: str
    full_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


@router.post("/register", status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new organisation and owner user."""
    # Check email unique
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create org
    slug = slugify(body.org_name)
    # Ensure slug unique
    slug_check = await db.execute(select(Organisation).where(Organisation.slug == slug))
    if slug_check.scalar_one_or_none():
        import uuid
        slug = f"{slug}-{str(uuid.uuid4())[:8]}"

    org = Organisation(name=body.org_name, slug=slug)
    db.add(org)
    await db.flush()

    # Create owner user
    user = User(
        organisation_id=org.id,
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        role=UserRole.owner,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token({"sub": str(user.id), "org_id": str(org.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "organisation_id": str(org.id),
            "organisation_name": org.name,
        },
    }


@router.post("/login")
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login and receive JWT token."""
    result = await db.execute(select(User).where(User.email == body.email, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    org_result = await db.execute(select(Organisation).where(Organisation.id == user.organisation_id))
    org = org_result.scalar_one_or_none()

    from datetime import datetime
    user.last_login = datetime.utcnow()
    await db.commit()

    token = create_access_token({"sub": str(user.id), "org_id": str(user.organisation_id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "organisation_id": str(user.organisation_id),
            "organisation_name": org.name if org else "",
        },
    }


@router.get("/me")
async def me(db: AsyncSession = Depends(get_db), current_user=Depends(__import__("app.middleware.auth", fromlist=["get_current_user"]).get_current_user)):
    org_result = await db.execute(select(Organisation).where(Organisation.id == current_user.organisation_id))
    org = org_result.scalar_one_or_none()
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "organisation_id": str(current_user.organisation_id),
        "organisation_name": org.name if org else "",
        "ai_enabled": org.ai_enabled if org else False,
        "plan": org.plan if org else "starter",
    }


@router.patch("/organisation")
async def update_organisation(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(__import__("app.middleware.auth", fromlist=["get_current_user"]).get_current_user),
):
    """Update organisation settings (Evolution API, AI, WhatsApp)."""
    org_result = await db.execute(select(Organisation).where(Organisation.id == current_user.organisation_id))
    org = org_result.scalar_one_or_none()
    if not org:
        raise HTTPException(404, "Organisation not found")

    allowed = [
        "evolution_url", "evolution_api_key", "evolution_instance",
        "gemini_api_key", "ai_system_prompt", "ai_enabled",
        "whatsapp_phone_id", "whatsapp_token", "whatsapp_verify_token",
    ]
    for key, value in body.items():
        if key in allowed:
            setattr(org, key, value)

    await db.commit()
    return {"updated": True}
