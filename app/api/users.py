"""
User management API routes.
"""
import math
import uuid

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentAdmin, DbSession
from app.core.security import get_password_hash
from app.models import User
from app.schemas import (
    Message,
    PasswordReset,
    UserCreate,
    UserListResponse,
    UserResponse,
    UserUpdate,
)

router = APIRouter()


@router.get("", response_model=UserListResponse)
async def list_users(
    db: DbSession,
    _: CurrentAdmin,  # Require admin
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
) -> UserListResponse:
    """
    List all users (admin only).
    """
    # Count total
    count_result = await db.execute(select(func.count(User.id)))
    total = count_result.scalar() or 0
    
    # Get paginated users
    offset = (page - 1) * size
    result = await db.execute(
        select(User)
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(size)
    )
    users = result.scalars().all()
    
    return UserListResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total > 0 else 0,
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    db: DbSession,
    _: CurrentAdmin,  # Require admin
) -> UserResponse:
    """
    Create a new user (admin only).
    """
    # Check if username exists
    result = await db.execute(
        select(User).where(User.username == user_in.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )
    
    # Create user
    user = User(
        username=user_in.username,
        password_hash=get_password_hash(user_in.password),
        role=user_in.role,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    
    return UserResponse.model_validate(user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    db: DbSession,
    _: CurrentAdmin,  # Require admin
) -> UserResponse:
    """
    Get a specific user by ID (admin only).
    """
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    user_in: UserUpdate,
    db: DbSession,
    _: CurrentAdmin,  # Require admin
) -> UserResponse:
    """
    Update a user (admin only).
    
    Can update role and is_active status.
    """
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Update fields
    update_data = user_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    await db.flush()
    await db.refresh(user)
    
    return UserResponse.model_validate(user)


@router.post("/{user_id}/reset-password", response_model=Message)
async def reset_user_password(
    user_id: uuid.UUID,
    password_in: PasswordReset,
    db: DbSession,
    _: CurrentAdmin,  # Require admin
) -> Message:
    """
    Reset a user's password (admin only).
    """
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    user.password_hash = get_password_hash(password_in.new_password)
    await db.flush()
    
    return Message(detail="Password reset successfully")
