"""
AuditLog Pydantic schemas.
"""
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AuditLogResponse(BaseModel):
    """Schema for audit log response."""
    id: uuid.UUID
    batch_id: uuid.UUID | None
    module: str
    action: str
    object_type: str
    object_id: uuid.UUID | None
    before_jsonb: dict[str, Any] | None
    after_jsonb: dict[str, Any] | None
    operator_id: uuid.UUID | None
    operator_username: str | None = None  # Joined from users table
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    """Schema for paginated audit log list."""
    items: list[AuditLogResponse]
    total: int
    page: int
    size: int
    pages: int


class AuditLogQuery(BaseModel):
    """Schema for querying audit logs."""
    module: str | None = None
    action: str | None = None
    object_type: str | None = None
    object_id: uuid.UUID | None = None
    operator_id: uuid.UUID | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
