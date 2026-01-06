"""
User Pydantic schemas.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class UserBase(BaseModel):
    """Base user schema."""
    username: str = Field(..., min_length=1, max_length=64)


class UserCreate(UserBase):
    """Schema for creating a user."""
    password: str = Field(..., min_length=6, max_length=128)
    role: str = Field(default="USER", pattern="^(ADMIN|USER)$")


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    role: str | None = Field(default=None, pattern="^(ADMIN|USER)$")
    is_active: bool | None = None


class UserResponse(UserBase):
    """User response schema."""
    id: uuid.UUID
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    """Paginated user list response."""
    items: list[UserResponse]
    total: int
    page: int
    size: int
    pages: int


class PasswordReset(BaseModel):
    """Password reset request."""
    new_password: str = Field(..., min_length=6, max_length=128)


class CurrentUserResponse(BaseModel):
    """Current user info response."""
    id: uuid.UUID
    username: str
    role: str
    is_active: bool

    model_config = {"from_attributes": True}
