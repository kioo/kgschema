"""
AuditLog model for change tracking.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin


class AuditLog(Base, UUIDMixin):
    """Audit log for tracking all changes."""
    
    __tablename__ = "audit_logs"
    
    batch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)  # For batch operations
    module: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # entities/relations/users/versions
    action: Mapped[str] = mapped_column(String(32), nullable=False)  # CREATE/UPDATE/DELETE/PUBLISH/IMPORT
    object_type: Mapped[str] = mapped_column(String(64), nullable=False)  # entity/entity_property/relation/...
    object_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    before_jsonb: Mapped[dict | None] = mapped_column(JSONB)
    after_jsonb: Mapped[dict | None] = mapped_column(JSONB)
    operator_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        index=True,
    )
