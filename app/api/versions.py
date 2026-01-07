"""
Version management API routes.
"""
import math
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.core.deps import CurrentUser, DbSession
from app.models import Entity, EntityProperty, Relation, RelationProperty, SchemaVersion, User
from app.schemas.version import (
    VersionCreate,
    VersionDetailResponse,
    VersionListResponse,
    VersionResponse,
)
from app.services.audit import create_audit_log

router = APIRouter()


async def _build_snapshot(db) -> dict:
    """Build a snapshot of current schema (entities + relations with properties)."""
    # Fetch all active entities with properties
    entities_result = await db.execute(
        select(Entity)
        .options(selectinload(Entity.properties))
        .where(Entity.is_active == True)
        .order_by(Entity.entity_code)
    )
    entities = entities_result.scalars().all()
    
    entities_snapshot = []
    for entity in entities:
        entity_data = {
            "entity_code": entity.entity_code,
            "entity_name": entity.entity_name,
            "entity_name_en": entity.entity_name_en,
            "description": entity.description,
            "status": entity.status,
            "properties": [
                {
                    "prop_code": p.prop_code,
                    "prop_name": p.prop_name,
                    "prop_name_en": p.prop_name_en,
                    "data_type": p.data_type,
                    "options_json": p.options_json,
                    "is_required": p.is_required,
                    "display_order": p.display_order,
                }
                for p in sorted(entity.properties, key=lambda x: x.display_order)
            ],
        }
        entities_snapshot.append(entity_data)
    
    # Fetch all active relations with properties
    relations_result = await db.execute(
        select(Relation)
        .options(
            selectinload(Relation.properties),
            selectinload(Relation.head_entity),
            selectinload(Relation.tail_entity),
        )
        .where(Relation.is_active == True)
        .order_by(Relation.relation_code)
    )
    relations = relations_result.scalars().all()
    
    relations_snapshot = []
    for relation in relations:
        relation_data = {
            "relation_code": relation.relation_code,
            "relation_name": relation.relation_name,
            "relation_name_en": relation.relation_name_en,
            "head_entity_code": relation.head_entity.entity_code if relation.head_entity else None,
            "tail_entity_code": relation.tail_entity.entity_code if relation.tail_entity else None,
            "description": relation.description,
            "status": relation.status,
            "properties": [
                {
                    "prop_code": p.prop_code,
                    "prop_name": p.prop_name,
                    "prop_name_en": p.prop_name_en,
                    "data_type": p.data_type,
                    "options_json": p.options_json,
                    "is_required": p.is_required,
                    "display_order": p.display_order,
                }
                for p in sorted(relation.properties, key=lambda x: x.display_order)
            ],
        }
        relations_snapshot.append(relation_data)
    
    return {
        "entities": entities_snapshot,
        "relations": relations_snapshot,
    }


@router.get("", response_model=VersionListResponse)
async def list_versions(
    db: DbSession,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
) -> VersionListResponse:
    """List all published versions."""
    query = select(SchemaVersion)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    
    # Get paginated results
    offset = (page - 1) * size
    result = await db.execute(
        query.order_by(SchemaVersion.version.desc()).offset(offset).limit(size)
    )
    versions = result.scalars().all()
    
    # Get publisher usernames
    publisher_ids = {v.published_by for v in versions if v.published_by}
    publisher_map = {}
    if publisher_ids:
        users_result = await db.execute(
            select(User).where(User.id.in_(publisher_ids))
        )
        for user in users_result.scalars():
            publisher_map[user.id] = user.username
    
    items = []
    for v in versions:
        resp = VersionResponse.model_validate(v)
        resp.published_by_username = publisher_map.get(v.published_by)
        items.append(resp)
    
    return VersionListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total > 0 else 0,
    )


@router.post("/publish", response_model=VersionResponse, status_code=status.HTTP_201_CREATED)
async def publish_version(
    version_in: VersionCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> VersionResponse:
    """Publish a new version snapshot of the current schema."""
    # Get next version number
    max_version_result = await db.execute(
        select(func.max(SchemaVersion.version))
    )
    max_version = max_version_result.scalar() or 0
    new_version = max_version + 1
    
    # Build snapshot
    snapshot = await _build_snapshot(db)
    published_at = datetime.now(timezone.utc)
    
    snapshot["version"] = new_version
    snapshot["published_at"] = published_at.isoformat()
    
    # Create version record
    version = SchemaVersion(
        version=new_version,
        snapshot_jsonb=snapshot,
        release_notes=version_in.release_notes,
        published_by=current_user.id,
        published_at=published_at,
    )
    db.add(version)
    await db.flush()
    await db.refresh(version)
    
    # Audit log
    await create_audit_log(
        db,
        module="versions",
        action="PUBLISH",
        object_type="schema_version",
        object_id=version.id,
        after_data={
            "version": new_version,
            "release_notes": version_in.release_notes,
            "entities_count": len(snapshot["entities"]),
            "relations_count": len(snapshot["relations"]),
        },
        operator_id=current_user.id,
    )
    
    resp = VersionResponse.model_validate(version)
    resp.published_by_username = current_user.username
    return resp


@router.get("/{version_id}", response_model=VersionDetailResponse)
async def get_version(
    version_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> VersionDetailResponse:
    """Get version details with snapshot."""
    version = await db.get(SchemaVersion, version_id)
    
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found",
        )
    
    # Get publisher username
    publisher_username = None
    if version.published_by:
        user = await db.get(User, version.published_by)
        if user:
            publisher_username = user.username
    
    resp = VersionDetailResponse.model_validate(version)
    resp.published_by_username = publisher_username
    return resp


@router.post("/{version_id}/copy-to-draft", status_code=status.HTTP_200_OK)
async def copy_version_to_draft(
    version_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """
    Copy a version's snapshot back to draft entities/relations.
    This effectively "rolls back" to that version's state.
    
    WARNING: This will replace all current draft data!
    """
    version = await db.get(SchemaVersion, version_id)
    
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found",
        )
    
    snapshot = version.snapshot_jsonb
    
    # Soft-delete all current entities and relations
    await db.execute(
        Entity.__table__.update().values(is_active=False)
    )
    await db.execute(
        Relation.__table__.update().values(is_active=False)
    )
    
    # Re-create entities from snapshot
    entity_code_to_id = {}
    for entity_data in snapshot.get("entities", []):
        entity = Entity(
            entity_code=entity_data["entity_code"],
            entity_name=entity_data["entity_name"],
            entity_name_en=entity_data.get("entity_name_en"),
            description=entity_data.get("description"),
            status="DRAFT",  # Reset to draft
            is_active=True,
        )
        db.add(entity)
        await db.flush()
        entity_code_to_id[entity.entity_code] = entity.id
        
        # Create properties
        for prop_data in entity_data.get("properties", []):
            prop = EntityProperty(
                entity_id=entity.id,
                prop_code=prop_data["prop_code"],
                prop_name=prop_data["prop_name"],
                prop_name_en=prop_data.get("prop_name_en"),
                data_type=prop_data.get("data_type", "STRING"),
                options_json=prop_data.get("options_json"),
                is_required=prop_data.get("is_required", False),
                display_order=prop_data.get("display_order", 0),
            )
            db.add(prop)
    
    # Re-create relations from snapshot
    for relation_data in snapshot.get("relations", []):
        head_id = entity_code_to_id.get(relation_data.get("head_entity_code"))
        tail_id = entity_code_to_id.get(relation_data.get("tail_entity_code"))
        
        if not head_id or not tail_id:
            continue  # Skip if referenced entities don't exist
        
        relation = Relation(
            relation_code=relation_data["relation_code"],
            relation_name=relation_data["relation_name"],
            relation_name_en=relation_data.get("relation_name_en"),
            head_entity_id=head_id,
            tail_entity_id=tail_id,
            description=relation_data.get("description"),
            status="DRAFT",
            is_active=True,
        )
        db.add(relation)
        await db.flush()
        
        # Create properties
        for prop_data in relation_data.get("properties", []):
            prop = RelationProperty(
                relation_id=relation.id,
                prop_code=prop_data["prop_code"],
                prop_name=prop_data["prop_name"],
                prop_name_en=prop_data.get("prop_name_en"),
                data_type=prop_data.get("data_type", "STRING"),
                options_json=prop_data.get("options_json"),
                is_required=prop_data.get("is_required", False),
                display_order=prop_data.get("display_order", 0),
            )
            db.add(prop)
    
    await db.flush()
    
    # Audit log
    await create_audit_log(
        db,
        module="versions",
        action="IMPORT",
        object_type="schema_version",
        object_id=version_id,
        after_data={"action": "copy_to_draft", "source_version": version.version},
        operator_id=current_user.id,
    )
    
    return {
        "message": f"Successfully copied version {version.version} to draft",
        "entities_created": len(snapshot.get("entities", [])),
        "relations_created": len(snapshot.get("relations", [])),
    }
