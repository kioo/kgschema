"""
Audit log API routes.
"""
import math
import uuid
from datetime import datetime

from fastapi import APIRouter, Query
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.core.deps import CurrentUser, DbSession
from app.models import AuditLog, User
from app.schemas.audit import AuditLogListResponse, AuditLogResponse

router = APIRouter()


@router.get("/logs", response_model=AuditLogListResponse)
async def list_audit_logs(
    db: DbSession,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    module: str | None = None,
    action: str | None = None,
    object_type: str | None = None,
    object_id: uuid.UUID | None = None,
    operator_id: uuid.UUID | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> AuditLogListResponse:
    """
    Query audit logs with filtering.
    
    Filters:
    - module: entities, relations, users, versions
    - action: CREATE, UPDATE, DELETE, PUBLISH, IMPORT
    - object_type: entity, entity_property, relation, etc.
    - object_id: ID of specific object
    - operator_id: ID of user who performed the action
    - start_time/end_time: Time range filter
    """
    query = select(AuditLog)
    
    if module:
        query = query.where(AuditLog.module == module)
    if action:
        query = query.where(AuditLog.action == action)
    if object_type:
        query = query.where(AuditLog.object_type == object_type)
    if object_id:
        query = query.where(AuditLog.object_id == object_id)
    if operator_id:
        query = query.where(AuditLog.operator_id == operator_id)
    if start_time:
        query = query.where(AuditLog.created_at >= start_time)
    if end_time:
        query = query.where(AuditLog.created_at <= end_time)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    
    # Get paginated results
    offset = (page - 1) * size
    result = await db.execute(
        query.order_by(AuditLog.created_at.desc()).offset(offset).limit(size)
    )
    logs = result.scalars().all()
    
    # Get operator usernames
    operator_ids = {log.operator_id for log in logs if log.operator_id}
    operator_map = {}
    if operator_ids:
        users_result = await db.execute(
            select(User).where(User.id.in_(operator_ids))
        )
        for user in users_result.scalars():
            operator_map[user.id] = user.username
    
    # Build response
    items = []
    for log in logs:
        resp = AuditLogResponse.model_validate(log)
        resp.operator_username = operator_map.get(log.operator_id)
        items.append(resp)
    
    return AuditLogListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total > 0 else 0,
    )
