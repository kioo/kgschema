"""
SchemaVersion model for version snapshots.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin


class SchemaVersion(Base, UUIDMixin):
    """Schema version snapshot."""
    
    __tablename__ = "schema_versions"
    
    version: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    snapshot_jsonb: Mapped[dict] = mapped_column(JSONB, nullable=False)
    release_notes: Mapped[str | None] = mapped_column(Text)
    published_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
    )
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
