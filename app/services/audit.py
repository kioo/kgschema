"""
Audit logging service.
"""
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog


async def create_audit_log(
    db: AsyncSession,
    *,
    module: str,
    action: str,
    object_type: str,
    object_id: uuid.UUID | None = None,
    before_data: dict[str, Any] | None = None,
    after_data: dict[str, Any] | None = None,
    operator_id: uuid.UUID | None = None,
    batch_id: uuid.UUID | None = None,
) -> AuditLog:
    """
    Create an audit log entry.
    
    Args:
        db: Database session
        module: Module name (entities, relations, users, versions)
        action: Action type (CREATE, UPDATE, DELETE, PUBLISH, IMPORT)
        object_type: Object type (entity, entity_property, relation, etc.)
        object_id: ID of the affected object
        before_data: State before change (for UPDATE/DELETE)
        after_data: State after change (for CREATE/UPDATE)
        operator_id: ID of the user performing the action
        batch_id: Batch ID for grouping related operations
    """
    # Sanitize sensitive fields
    if before_data:
        before_data = _sanitize_data(before_data)
    if after_data:
        after_data = _sanitize_data(after_data)
    
    audit_log = AuditLog(
        batch_id=batch_id,
        module=module,
        action=action,
        object_type=object_type,
        object_id=object_id,
        before_jsonb=before_data,
        after_jsonb=after_data,
        operator_id=operator_id,
    )
    db.add(audit_log)
    await db.flush()
    return audit_log


def _sanitize_data(data: dict[str, Any]) -> dict[str, Any]:
    """Remove or mask sensitive fields from audit data."""
    sensitive_fields = {"password", "password_hash", "secret", "token"}
    sanitized = {}
    for key, value in data.items():
        if key.lower() in sensitive_fields:
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = _sanitize_data(value)
        else:
            sanitized[key] = value
    return sanitized


def model_to_dict(model: Any, exclude: set[str] | None = None) -> dict[str, Any]:
    """
    Convert SQLAlchemy model to dict for audit logging.
    
    Args:
        model: SQLAlchemy model instance
        exclude: Fields to exclude from output
    """
    if exclude is None:
        exclude = set()
    
    result = {}
    for column in model.__table__.columns:
        if column.name not in exclude:
            value = getattr(model, column.name)
            # Convert UUID to string for JSON serialization
            if isinstance(value, uuid.UUID):
                value = str(value)
            # Convert datetime to ISO string
            elif hasattr(value, 'isoformat'):
                value = value.isoformat()
            result[column.name] = value
    return result
