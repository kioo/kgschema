"""
Entity management API routes.
"""
import math
import uuid

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.core.deps import CurrentUser, DbSession
from app.models import Entity, EntityProperty
from app.schemas.entity import (
    EntityCreate,
    EntityDetailResponse,
    EntityListResponse,
    EntityPropertyCreate,
    EntityPropertyResponse,
    EntityPropertyUpdate,
    EntityResponse,
    EntityUpdate,
)
from app.services.audit import create_audit_log, model_to_dict

router = APIRouter()


# ============================================
# Entity CRUD
# ============================================

@router.get("", response_model=EntityListResponse)
async def list_entities(
    db: DbSession,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None, pattern="^(DRAFT|ACTIVE)$"),
    is_active: bool = Query(True),
    search: str | None = None,
) -> EntityListResponse:
    """List entities with pagination and filtering."""
    query = select(Entity).where(Entity.is_active == is_active)
    
    if status:
        query = query.where(Entity.status == status)
    
    if search:
        query = query.where(
            Entity.entity_name.ilike(f"%{search}%") |
            Entity.entity_code.ilike(f"%{search}%")
        )
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    
    # Get paginated results
    offset = (page - 1) * size
    result = await db.execute(
        query.order_by(Entity.created_at.desc()).offset(offset).limit(size)
    )
    entities = result.scalars().all()
    
    return EntityListResponse(
        items=[EntityResponse.model_validate(e) for e in entities],
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total > 0 else 0,
    )


@router.post("", response_model=EntityResponse, status_code=status.HTTP_201_CREATED)
async def create_entity(
    entity_in: EntityCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> EntityResponse:
    """Create a new entity."""
    # Check unique constraint
    existing = await db.execute(
        select(Entity).where(Entity.entity_code == entity_in.entity_code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Entity code '{entity_in.entity_code}' already exists",
        )
    
    entity = Entity(**entity_in.model_dump())
    db.add(entity)
    await db.flush()
    await db.refresh(entity)
    
    # Audit log
    await create_audit_log(
        db,
        module="entities",
        action="CREATE",
        object_type="entity",
        object_id=entity.id,
        after_data=model_to_dict(entity),
        operator_id=current_user.id,
    )
    
    return EntityResponse.model_validate(entity)


@router.get("/{entity_id}", response_model=EntityDetailResponse)
async def get_entity(
    entity_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> EntityDetailResponse:
    """Get entity details with properties."""
    result = await db.execute(
        select(Entity)
        .options(selectinload(Entity.properties))
        .where(Entity.id == entity_id)
    )
    entity = result.scalar_one_or_none()
    
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entity not found",
        )
    
    return EntityDetailResponse.model_validate(entity)


@router.patch("/{entity_id}", response_model=EntityResponse)
async def update_entity(
    entity_id: uuid.UUID,
    entity_in: EntityUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> EntityResponse:
    """Update an entity."""
    entity = await db.get(Entity, entity_id)
    
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entity not found",
        )
    
    before_data = model_to_dict(entity)
    
    # Update fields
    update_data = entity_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(entity, field, value)
    
    await db.flush()
    await db.refresh(entity)
    
    # Audit log
    await create_audit_log(
        db,
        module="entities",
        action="UPDATE",
        object_type="entity",
        object_id=entity.id,
        before_data=before_data,
        after_data=model_to_dict(entity),
        operator_id=current_user.id,
    )
    
    return EntityResponse.model_validate(entity)


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entity(
    entity_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """Soft delete an entity (set is_active=False)."""
    entity = await db.get(Entity, entity_id)
    
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entity not found",
        )
    
    before_data = model_to_dict(entity)
    entity.is_active = False
    await db.flush()
    
    # Audit log
    await create_audit_log(
        db,
        module="entities",
        action="DELETE",
        object_type="entity",
        object_id=entity.id,
        before_data=before_data,
        after_data=model_to_dict(entity),
        operator_id=current_user.id,
    )


# ============================================
# Entity Property CRUD
# ============================================

@router.get("/{entity_id}/properties", response_model=list[EntityPropertyResponse])
async def list_entity_properties(
    entity_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> list[EntityPropertyResponse]:
    """List properties for an entity."""
    result = await db.execute(
        select(EntityProperty)
        .where(EntityProperty.entity_id == entity_id)
        .order_by(EntityProperty.display_order)
    )
    properties = result.scalars().all()
    return [EntityPropertyResponse.model_validate(p) for p in properties]


@router.post("/{entity_id}/properties", response_model=EntityPropertyResponse, status_code=status.HTTP_201_CREATED)
async def create_entity_property(
    entity_id: uuid.UUID,
    prop_in: EntityPropertyCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> EntityPropertyResponse:
    """Create a new property for an entity."""
    # Check entity exists
    entity = await db.get(Entity, entity_id)
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entity not found",
        )
    
    # Check unique prop_code within entity
    existing = await db.execute(
        select(EntityProperty).where(
            EntityProperty.entity_id == entity_id,
            EntityProperty.prop_code == prop_in.prop_code,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Property code '{prop_in.prop_code}' already exists in this entity",
        )
    
    prop = EntityProperty(entity_id=entity_id, **prop_in.model_dump())
    db.add(prop)
    await db.flush()
    await db.refresh(prop)
    
    # Audit log
    await create_audit_log(
        db,
        module="entities",
        action="CREATE",
        object_type="entity_property",
        object_id=prop.id,
        after_data=model_to_dict(prop),
        operator_id=current_user.id,
    )
    
    return EntityPropertyResponse.model_validate(prop)


@router.patch("/{entity_id}/properties/{prop_id}", response_model=EntityPropertyResponse)
async def update_entity_property(
    entity_id: uuid.UUID,
    prop_id: uuid.UUID,
    prop_in: EntityPropertyUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> EntityPropertyResponse:
    """Update an entity property."""
    result = await db.execute(
        select(EntityProperty).where(
            EntityProperty.id == prop_id,
            EntityProperty.entity_id == entity_id,
        )
    )
    prop = result.scalar_one_or_none()
    
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )
    
    before_data = model_to_dict(prop)
    
    # Update fields
    update_data = prop_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(prop, field, value)
    
    await db.flush()
    await db.refresh(prop)
    
    # Audit log
    await create_audit_log(
        db,
        module="entities",
        action="UPDATE",
        object_type="entity_property",
        object_id=prop.id,
        before_data=before_data,
        after_data=model_to_dict(prop),
        operator_id=current_user.id,
    )
    
    return EntityPropertyResponse.model_validate(prop)


@router.delete("/{entity_id}/properties/{prop_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entity_property(
    entity_id: uuid.UUID,
    prop_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """Delete an entity property."""
    result = await db.execute(
        select(EntityProperty).where(
            EntityProperty.id == prop_id,
            EntityProperty.entity_id == entity_id,
        )
    )
    prop = result.scalar_one_or_none()
    
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )
    
    before_data = model_to_dict(prop)
    await db.delete(prop)
    await db.flush()
    
    # Audit log
    await create_audit_log(
        db,
        module="entities",
        action="DELETE",
        object_type="entity_property",
        object_id=prop_id,
        before_data=before_data,
        operator_id=current_user.id,
    )
