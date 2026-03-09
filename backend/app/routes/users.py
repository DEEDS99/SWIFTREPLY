"""
SwiftReply — User Management
=============================
Invite team members, update roles, deactivate users.
Owner/Admin only for most operations.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.db.models import User, UserRole, Organisation
from app.middleware.auth import get_current_user, require_admin, hash_password

router = APIRouter()


class InviteUser(BaseModel):
    email: EmailStr
    full_name: str
    role: str = "agent"
    password: str  # In production, send invite email instead


class UpdateUser(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("")
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all users in the organisation."""
    result = await db.execute(
        select(User).where(
            User.organisation_id == current_user.organisation_id
        ).order_by(User.created_at)
    )
    users = result.scalars().all()
    return {
        "users": [
            {
                "id": str(u.id),
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role,
                "is_active": u.is_active,
                "last_login": u.last_login.isoformat() if u.last_login else None,
                "created_at": u.created_at.isoformat(),
            }
            for u in users
        ]
    }


@router.post("/invite", status_code=201)
async def invite_user(
    body: InviteUser,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Invite (create) a new user in the organisation."""
    # Check email unique across all orgs
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Email already registered")

    if body.role not in [r.value for r in UserRole]:
        raise HTTPException(400, f"Invalid role. Choose from: {[r.value for r in UserRole]}")

    user = User(
        organisation_id=current_user.organisation_id,
        email=body.email,
        full_name=body.full_name,
        hashed_password=hash_password(body.password),
        role=body.role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "message": f"User {user.email} added to organisation",
    }


@router.patch("/{user_id}")
async def update_user(
    user_id: str,
    body: UpdateUser,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update a user's role or status."""
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.organisation_id == current_user.organisation_id,
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    # Prevent demoting yourself
    if str(user.id) == str(current_user.id) and body.role and body.role != current_user.role:
        raise HTTPException(400, "You cannot change your own role")

    if body.full_name:
        user.full_name = body.full_name
    if body.role:
        if body.role not in [r.value for r in UserRole]:
            raise HTTPException(400, "Invalid role")
        user.role = body.role
    if body.is_active is not None:
        user.is_active = body.is_active

    await db.commit()
    return {"id": str(user.id), "updated": True}


@router.delete("/{user_id}")
async def deactivate_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Deactivate a user (soft delete)."""
    if str(user_id) == str(current_user.id):
        raise HTTPException(400, "Cannot deactivate yourself")

    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.organisation_id == current_user.organisation_id,
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    user.is_active = False
    await db.commit()
    return {"deactivated": True}
