"""
Relation management API routes.
"""
import math
import uuid

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.core.deps import CurrentUser, DbSession
from app.models import Entity, Relation, RelationProperty
from app.schemas.relation import (
    RelationCreate,
    RelationDetailResponse,
    RelationListResponse,
    RelationPropertyCreate,
    RelationPropertyResponse,
    RelationPropertyUpdate,
    RelationResponse,
    RelationUpdate,
)
from app.services.audit import create_audit_log, model_to_dict

router = APIRouter()


# ============================================
# Relation CRUD
# ============================================

@router.get("", response_model=RelationListResponse)
async def list_relations(
    db: DbSession,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None, pattern="^(DRAFT|ACTIVE)$"),
    is_active: bool = Query(True),
    search: str | None = None,
) -> RelationListResponse:
    """List relations with pagination and filtering."""
    query = select(Relation).where(Relation.is_active == is_active)
    
    if status:
        query = query.where(Relation.status == status)
    
    if search:
        query = query.where(
            Relation.relation_name.ilike(f"%{search}%") |
            Relation.relation_code.ilike(f"%{search}%")
        )
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    
    # Get paginated results with entity info
    offset = (page - 1) * size
    result = await db.execute(
        query.options(
            selectinload(Relation.head_entity),
            selectinload(Relation.tail_entity),
        ).order_by(Relation.created_at.desc()).offset(offset).limit(size)
    )
    relations = result.scalars().all()
    
    # Build response with entity codes
    items = []
    for r in relations:
        resp = RelationResponse.model_validate(r)
        resp.head_entity_code = r.head_entity.entity_code if r.head_entity else None
        resp.tail_entity_code = r.tail_entity.entity_code if r.tail_entity else None
        items.append(resp)
    
    return RelationListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total > 0 else 0,
    )


@router.post("", response_model=RelationResponse, status_code=status.HTTP_201_CREATED)
async def create_relation(
    relation_in: RelationCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> RelationResponse:
    """Create a new relation."""
    # Check unique constraint
    existing = await db.execute(
        select(Relation).where(Relation.relation_code == relation_in.relation_code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Relation code '{relation_in.relation_code}' already exists",
        )
    
    # Verify head entity exists
    head_entity = await db.get(Entity, relation_in.head_entity_id)
    if not head_entity or not head_entity.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Head entity not found or inactive",
        )
    
    # Verify tail entity exists
    tail_entity = await db.get(Entity, relation_in.tail_entity_id)
    if not tail_entity or not tail_entity.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tail entity not found or inactive",
        )
    
    relation = Relation(**relation_in.model_dump())
    db.add(relation)
    await db.flush()
    await db.refresh(relation)
    
    # Audit log
    await create_audit_log(
        db,
        module="relations",
        action="CREATE",
        object_type="relation",
        object_id=relation.id,
        after_data=model_to_dict(relation),
        operator_id=current_user.id,
    )
    
    resp = RelationResponse.model_validate(relation)
    resp.head_entity_code = head_entity.entity_code
    resp.tail_entity_code = tail_entity.entity_code
    return resp


@router.get("/{relation_id}", response_model=RelationDetailResponse)
async def get_relation(
    relation_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> RelationDetailResponse:
    """Get relation details with properties."""
    result = await db.execute(
        select(Relation)
        .options(
            selectinload(Relation.properties),
            selectinload(Relation.head_entity),
            selectinload(Relation.tail_entity),
        )
        .where(Relation.id == relation_id)
    )
    relation = result.scalar_one_or_none()
    
    if not relation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Relation not found",
        )
    
    resp = RelationDetailResponse.model_validate(relation)
    resp.head_entity_code = relation.head_entity.entity_code if relation.head_entity else None
    resp.tail_entity_code = relation.tail_entity.entity_code if relation.tail_entity else None
    return resp


@router.patch("/{relation_id}", response_model=RelationResponse)
async def update_relation(
    relation_id: uuid.UUID,
    relation_in: RelationUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> RelationResponse:
    """Update a relation."""
    result = await db.execute(
        select(Relation).options(
            selectinload(Relation.head_entity),
            selectinload(Relation.tail_entity),
        ).where(Relation.id == relation_id)
    )
    relation = result.scalar_one_or_none()
    
    if not relation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Relation not found",
        )
    
    before_data = model_to_dict(relation)
    
    # If updating head/tail entity, verify they exist
    update_data = relation_in.model_dump(exclude_unset=True)
    
    if "head_entity_id" in update_data:
        head_entity = await db.get(Entity, update_data["head_entity_id"])
        if not head_entity or not head_entity.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Head entity not found or inactive",
            )
    
    if "tail_entity_id" in update_data:
        tail_entity = await db.get(Entity, update_data["tail_entity_id"])
        if not tail_entity or not tail_entity.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tail entity not found or inactive",
            )
    
    # Update fields
    for field, value in update_data.items():
        setattr(relation, field, value)
    
    await db.flush()
    await db.refresh(relation)
    
    # Audit log
    await create_audit_log(
        db,
        module="relations",
        action="UPDATE",
        object_type="relation",
        object_id=relation.id,
        before_data=before_data,
        after_data=model_to_dict(relation),
        operator_id=current_user.id,
    )
    
    resp = RelationResponse.model_validate(relation)
    resp.head_entity_code = relation.head_entity.entity_code if relation.head_entity else None
    resp.tail_entity_code = relation.tail_entity.entity_code if relation.tail_entity else None
    return resp


@router.delete("/{relation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_relation(
    relation_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """Soft delete a relation (set is_active=False)."""
    relation = await db.get(Relation, relation_id)
    
    if not relation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Relation not found",
        )
    
    before_data = model_to_dict(relation)
    relation.is_active = False
    await db.flush()
    
    # Audit log
    await create_audit_log(
        db,
        module="relations",
        action="DELETE",
        object_type="relation",
        object_id=relation.id,
        before_data=before_data,
        after_data=model_to_dict(relation),
        operator_id=current_user.id,
    )


# ============================================
# Relation Property CRUD
# ============================================

@router.get("/{relation_id}/properties", response_model=list[RelationPropertyResponse])
async def list_relation_properties(
    relation_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> list[RelationPropertyResponse]:
    """List properties for a relation."""
    result = await db.execute(
        select(RelationProperty)
        .where(RelationProperty.relation_id == relation_id)
        .order_by(RelationProperty.display_order)
    )
    properties = result.scalars().all()
    return [RelationPropertyResponse.model_validate(p) for p in properties]


@router.post("/{relation_id}/properties", response_model=RelationPropertyResponse, status_code=status.HTTP_201_CREATED)
async def create_relation_property(
    relation_id: uuid.UUID,
    prop_in: RelationPropertyCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> RelationPropertyResponse:
    """Create a new property for a relation."""
    # Check relation exists
    relation = await db.get(Relation, relation_id)
    if not relation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Relation not found",
        )
    
    # Check unique prop_code within relation
    existing = await db.execute(
        select(RelationProperty).where(
            RelationProperty.relation_id == relation_id,
            RelationProperty.prop_code == prop_in.prop_code,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Property code '{prop_in.prop_code}' already exists in this relation",
        )
    
    prop = RelationProperty(relation_id=relation_id, **prop_in.model_dump())
    db.add(prop)
    await db.flush()
    await db.refresh(prop)
    
    # Audit log
    await create_audit_log(
        db,
        module="relations",
        action="CREATE",
        object_type="relation_property",
        object_id=prop.id,
        after_data=model_to_dict(prop),
        operator_id=current_user.id,
    )
    
    return RelationPropertyResponse.model_validate(prop)


@router.patch("/{relation_id}/properties/{prop_id}", response_model=RelationPropertyResponse)
async def update_relation_property(
    relation_id: uuid.UUID,
    prop_id: uuid.UUID,
    prop_in: RelationPropertyUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> RelationPropertyResponse:
    """Update a relation property."""
    result = await db.execute(
        select(RelationProperty).where(
            RelationProperty.id == prop_id,
            RelationProperty.relation_id == relation_id,
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
        module="relations",
        action="UPDATE",
        object_type="relation_property",
        object_id=prop.id,
        before_data=before_data,
        after_data=model_to_dict(prop),
        operator_id=current_user.id,
    )
    
    return RelationPropertyResponse.model_validate(prop)


@router.delete("/{relation_id}/properties/{prop_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_relation_property(
    relation_id: uuid.UUID,
    prop_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """Delete a relation property."""
    result = await db.execute(
        select(RelationProperty).where(
            RelationProperty.id == prop_id,
            RelationProperty.relation_id == relation_id,
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
        module="relations",
        action="DELETE",
        object_type="relation_property",
        object_id=prop_id,
        before_data=before_data,
        operator_id=current_user.id,
    )
