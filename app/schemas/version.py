"""
Version management Pydantic schemas.
"""
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class VersionSnapshot(BaseModel):
    """Schema for version snapshot content."""
    version: int
    published_at: str
    entities: list[dict[str, Any]]
    relations: list[dict[str, Any]]


class VersionCreate(BaseModel):
    """Schema for publishing a new version."""
    release_notes: str | None = Field(None, max_length=1000)


class VersionResponse(BaseModel):
    """Schema for version response."""
    id: uuid.UUID
    version: int
    release_notes: str | None
    published_by: uuid.UUID | None
    published_by_username: str | None = None
    published_at: datetime

    model_config = {"from_attributes": True}


class VersionDetailResponse(VersionResponse):
    """Schema for version detail with snapshot."""
    snapshot_jsonb: dict[str, Any]


class VersionListResponse(BaseModel):
    """Schema for paginated version list."""
    items: list[VersionResponse]
    total: int
    page: int
    size: int
    pages: int
