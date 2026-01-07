"""
Import/Export API routes for Excel operations.
"""
import io
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
import pandas as pd

from app.core.deps import CurrentUser, DbSession
from app.models import Entity, EntityProperty, Relation, RelationProperty
from app.schemas.import_export import ImportError as ImportErrorSchema, ImportResult
from app.services.audit import create_audit_log

router = APIRouter()


def validate_code(value: str) -> bool:
    """Validate entity/relation/property code format."""
    return bool(re.match(r"^[a-zA-Z0-9_]+$", value))


async def _export_current_schema(db) -> dict[str, list[dict]]:
    """Export current active entities and relations."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    
    # Entities
    entities_result = await db.execute(
        select(Entity)
        .options(selectinload(Entity.properties))
        .where(Entity.is_active == True)
        .order_by(Entity.entity_code)
    )
    entities = entities_result.scalars().all()
    
    # Relations
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
    
    return {
        "entities": [
            {
                "entity_code": e.entity_code,
                "entity_name": e.entity_name,
                "entity_name_en": e.entity_name_en,
                "description": e.description,
                "properties": [
                    {
                        "prop_code": p.prop_code,
                        "prop_name": p.prop_name,
                        "prop_name_en": p.prop_name_en,
                        "data_type": p.data_type,
                        "options": ",".join(p.options_json) if p.options_json else None,
                        "is_required": p.is_required,
                    }
                    for p in sorted(e.properties, key=lambda x: x.display_order)
                ],
            }
            for e in entities
        ],
        "relations": [
            {
                "relation_code": r.relation_code,
                "relation_name": r.relation_name,
                "relation_name_en": r.relation_name_en,
                "head_entity_code": r.head_entity.entity_code if r.head_entity else None,
                "tail_entity_code": r.tail_entity.entity_code if r.tail_entity else None,
                "description": r.description,
                "properties": [
                    {
                        "prop_code": p.prop_code,
                        "prop_name": p.prop_name,
                        "prop_name_en": p.prop_name_en,
                        "data_type": p.data_type,
                        "options": ",".join(p.options_json) if p.options_json else None,
                        "is_required": p.is_required,
                    }
                    for p in sorted(r.properties, key=lambda x: x.display_order)
                ],
            }
            for r in relations
        ],
    }


@router.get("/template")
async def download_import_template(current_user: CurrentUser) -> StreamingResponse:
    """Download Excel import template."""
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Sheet 1: Entities
        entities_df = pd.DataFrame(columns=[
            "entity_code", "entity_name", "entity_name_en", "description"
        ])
        entities_df.to_excel(writer, sheet_name="实体定义", index=False)
        
        # Sheet 2: Entity Properties
        entity_props_df = pd.DataFrame(columns=[
            "entity_code", "prop_code", "prop_name", "prop_name_en",
            "data_type", "options", "is_required"
        ])
        entity_props_df.to_excel(writer, sheet_name="实体属性", index=False)
        
        # Sheet 3: Relations
        relations_df = pd.DataFrame(columns=[
            "relation_code", "relation_name", "relation_name_en",
            "head_entity_code", "tail_entity_code", "description"
        ])
        relations_df.to_excel(writer, sheet_name="关系定义", index=False)
        
        # Sheet 4: Relation Properties
        relation_props_df = pd.DataFrame(columns=[
            "relation_code", "prop_code", "prop_name", "prop_name_en",
            "data_type", "options", "is_required"
        ])
        relation_props_df.to_excel(writer, sheet_name="关系属性", index=False)
    
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=import_template.xlsx"},
    )


@router.post("/excel", response_model=ImportResult)
async def import_excel(
    db: DbSession,
    current_user: CurrentUser,
    file: UploadFile = File(...),
) -> ImportResult:
    """
    Import entities and relations from Excel file.
    
    The Excel file should have 4 sheets:
    1. 实体定义 (Entities)
    2. 实体属性 (Entity Properties)
    3. 关系定义 (Relations)
    4. 关系属性 (Relation Properties)
    """
    errors: list[ImportErrorSchema] = []
    batch_id = uuid.uuid4()
    
    try:
        content = await file.read()
        excel_file = io.BytesIO(content)
        
        # Read all sheets
        try:
            entities_df = pd.read_excel(excel_file, sheet_name="实体定义")
            excel_file.seek(0)
            entity_props_df = pd.read_excel(excel_file, sheet_name="实体属性")
            excel_file.seek(0)
            relations_df = pd.read_excel(excel_file, sheet_name="关系定义")
            excel_file.seek(0)
            relation_props_df = pd.read_excel(excel_file, sheet_name="关系属性")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid Excel format: {str(e)}",
            )
        
        # Validate and collect entities
        entity_codes = set()
        entities_to_create = []
        
        for idx, row in entities_df.iterrows():
            row_num = idx + 2  # Excel row (1-indexed, plus header)
            entity_code = str(row.get("entity_code", "")).strip()
            entity_name = str(row.get("entity_name", "")).strip()
            
            if not entity_code:
                errors.append(ImportErrorSchema(
                    sheet="实体定义", row=row_num, field="entity_code",
                    value=None, error="entity_code 不能为空"
                ))
                continue
            
            if not validate_code(entity_code):
                errors.append(ImportErrorSchema(
                    sheet="实体定义", row=row_num, field="entity_code",
                    value=entity_code, error="entity_code 只能包含字母、数字和下划线"
                ))
                continue
            
            if entity_code in entity_codes:
                errors.append(ImportErrorSchema(
                    sheet="实体定义", row=row_num, field="entity_code",
                    value=entity_code, error="entity_code 重复"
                ))
                continue
            
            if not entity_name:
                errors.append(ImportErrorSchema(
                    sheet="实体定义", row=row_num, field="entity_name",
                    value=None, error="entity_name 不能为空"
                ))
                continue
            
            entity_codes.add(entity_code)
            entities_to_create.append({
                "entity_code": entity_code,
                "entity_name": entity_name,
                "entity_name_en": str(row.get("entity_name_en", "")).strip() or None,
                "description": str(row.get("description", "")).strip() or None,
            })
        
        # Validate entity properties
        entity_props_to_create = {}
        prop_codes_per_entity = {}
        
        for idx, row in entity_props_df.iterrows():
            row_num = idx + 2
            entity_code = str(row.get("entity_code", "")).strip()
            prop_code = str(row.get("prop_code", "")).strip()
            prop_name = str(row.get("prop_name", "")).strip()
            
            if not entity_code:
                errors.append(ImportErrorSchema(
                    sheet="实体属性", row=row_num, field="entity_code",
                    value=None, error="entity_code 不能为空"
                ))
                continue
            
            if entity_code not in entity_codes:
                errors.append(ImportErrorSchema(
                    sheet="实体属性", row=row_num, field="entity_code",
                    value=entity_code, error="entity_code 在实体定义中不存在"
                ))
                continue
            
            if not prop_code:
                errors.append(ImportErrorSchema(
                    sheet="实体属性", row=row_num, field="prop_code",
                    value=None, error="prop_code 不能为空"
                ))
                continue
            
            if not prop_name:
                errors.append(ImportErrorSchema(
                    sheet="实体属性", row=row_num, field="prop_name",
                    value=None, error="prop_name 不能为空"
                ))
                continue
            
            # Check prop_code unique within entity
            if entity_code not in prop_codes_per_entity:
                prop_codes_per_entity[entity_code] = set()
            
            if prop_code in prop_codes_per_entity[entity_code]:
                errors.append(ImportErrorSchema(
                    sheet="实体属性", row=row_num, field="prop_code",
                    value=prop_code, error=f"prop_code 在实体 {entity_code} 中重复"
                ))
                continue
            
            prop_codes_per_entity[entity_code].add(prop_code)
            
            data_type = str(row.get("data_type", "STRING")).strip().upper()
            if data_type not in ["STRING", "INTEGER", "FLOAT", "BOOLEAN", "ENUM"]:
                data_type = "STRING"
            
            options = str(row.get("options", "")).strip()
            options_list = [o.strip() for o in options.split(",") if o.strip()] if options else None
            
            is_required = str(row.get("is_required", "")).strip().upper() in ["TRUE", "YES", "1"]
            
            if entity_code not in entity_props_to_create:
                entity_props_to_create[entity_code] = []
            
            entity_props_to_create[entity_code].append({
                "prop_code": prop_code,
                "prop_name": prop_name,
                "prop_name_en": str(row.get("prop_name_en", "")).strip() or None,
                "data_type": data_type,
                "options_json": options_list,
                "is_required": is_required,
                "display_order": len(entity_props_to_create[entity_code]),
            })
        
        # Validate relations
        relation_codes = set()
        relations_to_create = []
        
        for idx, row in relations_df.iterrows():
            row_num = idx + 2
            relation_code = str(row.get("relation_code", "")).strip()
            relation_name = str(row.get("relation_name", "")).strip()
            head_entity_code = str(row.get("head_entity_code", "")).strip()
            tail_entity_code = str(row.get("tail_entity_code", "")).strip()
            
            if not relation_code:
                errors.append(ImportErrorSchema(
                    sheet="关系定义", row=row_num, field="relation_code",
                    value=None, error="relation_code 不能为空"
                ))
                continue
            
            if not validate_code(relation_code):
                errors.append(ImportErrorSchema(
                    sheet="关系定义", row=row_num, field="relation_code",
                    value=relation_code, error="relation_code 只能包含字母、数字和下划线"
                ))
                continue
            
            if relation_code in relation_codes:
                errors.append(ImportErrorSchema(
                    sheet="关系定义", row=row_num, field="relation_code",
                    value=relation_code, error="relation_code 重复"
                ))
                continue
            
            if not relation_name:
                errors.append(ImportErrorSchema(
                    sheet="关系定义", row=row_num, field="relation_name",
                    value=None, error="relation_name 不能为空"
                ))
                continue
            
            if head_entity_code not in entity_codes:
                errors.append(ImportErrorSchema(
                    sheet="关系定义", row=row_num, field="head_entity_code",
                    value=head_entity_code, error="head_entity_code 在实体定义中不存在"
                ))
                continue
            
            if tail_entity_code not in entity_codes:
                errors.append(ImportErrorSchema(
                    sheet="关系定义", row=row_num, field="tail_entity_code",
                    value=tail_entity_code, error="tail_entity_code 在实体定义中不存在"
                ))
                continue
            
            relation_codes.add(relation_code)
            relations_to_create.append({
                "relation_code": relation_code,
                "relation_name": relation_name,
                "relation_name_en": str(row.get("relation_name_en", "")).strip() or None,
                "head_entity_code": head_entity_code,
                "tail_entity_code": tail_entity_code,
                "description": str(row.get("description", "")).strip() or None,
            })
        
        # Validate relation properties
        relation_props_to_create = {}
        prop_codes_per_relation = {}
        
        for idx, row in relation_props_df.iterrows():
            row_num = idx + 2
            relation_code = str(row.get("relation_code", "")).strip()
            prop_code = str(row.get("prop_code", "")).strip()
            prop_name = str(row.get("prop_name", "")).strip()
            
            if not relation_code:
                errors.append(ImportErrorSchema(
                    sheet="关系属性", row=row_num, field="relation_code",
                    value=None, error="relation_code 不能为空"
                ))
                continue
            
            if relation_code not in relation_codes:
                errors.append(ImportErrorSchema(
                    sheet="关系属性", row=row_num, field="relation_code",
                    value=relation_code, error="relation_code 在关系定义中不存在"
                ))
                continue
            
            if not prop_code:
                errors.append(ImportErrorSchema(
                    sheet="关系属性", row=row_num, field="prop_code",
                    value=None, error="prop_code 不能为空"
                ))
                continue
            
            if not prop_name:
                errors.append(ImportErrorSchema(
                    sheet="关系属性", row=row_num, field="prop_name",
                    value=None, error="prop_name 不能为空"
                ))
                continue
            
            if relation_code not in prop_codes_per_relation:
                prop_codes_per_relation[relation_code] = set()
            
            if prop_code in prop_codes_per_relation[relation_code]:
                errors.append(ImportErrorSchema(
                    sheet="关系属性", row=row_num, field="prop_code",
                    value=prop_code, error=f"prop_code 在关系 {relation_code} 中重复"
                ))
                continue
            
            prop_codes_per_relation[relation_code].add(prop_code)
            
            data_type = str(row.get("data_type", "STRING")).strip().upper()
            if data_type not in ["STRING", "INTEGER", "FLOAT", "BOOLEAN", "ENUM"]:
                data_type = "STRING"
            
            options = str(row.get("options", "")).strip()
            options_list = [o.strip() for o in options.split(",") if o.strip()] if options else None
            
            is_required = str(row.get("is_required", "")).strip().upper() in ["TRUE", "YES", "1"]
            
            if relation_code not in relation_props_to_create:
                relation_props_to_create[relation_code] = []
            
            relation_props_to_create[relation_code].append({
                "prop_code": prop_code,
                "prop_name": prop_name,
                "prop_name_en": str(row.get("prop_name_en", "")).strip() or None,
                "data_type": data_type,
                "options_json": options_list,
                "is_required": is_required,
                "display_order": len(relation_props_to_create[relation_code]),
            })
        
        # If there are errors, return them without making changes
        if errors:
            return ImportResult(
                success=False,
                errors=errors,
            )
        
        # All validation passed - create entities
        entity_code_to_id = {}
        for entity_data in entities_to_create:
            entity = Entity(
                entity_code=entity_data["entity_code"],
                entity_name=entity_data["entity_name"],
                entity_name_en=entity_data["entity_name_en"],
                description=entity_data["description"],
                status="DRAFT",
                is_active=True,
            )
            db.add(entity)
            await db.flush()
            entity_code_to_id[entity.entity_code] = entity.id
            
            # Create properties
            for prop_data in entity_props_to_create.get(entity.entity_code, []):
                prop = EntityProperty(
                    entity_id=entity.id,
                    **prop_data,
                )
                db.add(prop)
        
        # Create relations
        for relation_data in relations_to_create:
            relation = Relation(
                relation_code=relation_data["relation_code"],
                relation_name=relation_data["relation_name"],
                relation_name_en=relation_data["relation_name_en"],
                head_entity_id=entity_code_to_id[relation_data["head_entity_code"]],
                tail_entity_id=entity_code_to_id[relation_data["tail_entity_code"]],
                description=relation_data["description"],
                status="DRAFT",
                is_active=True,
            )
            db.add(relation)
            await db.flush()
            
            # Create properties
            for prop_data in relation_props_to_create.get(relation.relation_code, []):
                prop = RelationProperty(
                    relation_id=relation.id,
                    **prop_data,
                )
                db.add(prop)
        
        await db.flush()
        
        # Audit log
        await create_audit_log(
            db,
            module="import",
            action="IMPORT",
            object_type="excel",
            batch_id=batch_id,
            after_data={
                "entities": len(entities_to_create),
                "relations": len(relations_to_create),
                "entity_properties": sum(len(v) for v in entity_props_to_create.values()),
                "relation_properties": sum(len(v) for v in relation_props_to_create.values()),
            },
            operator_id=current_user.id,
        )
        
        return ImportResult(
            success=True,
            errors=[],
            entities_count=len(entities_to_create),
            relations_count=len(relations_to_create),
            entity_properties_count=sum(len(v) for v in entity_props_to_create.values()),
            relation_properties_count=sum(len(v) for v in relation_props_to_create.values()),
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}",
        )


@router.get("/json")
async def export_json(
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Export current schema as JSON."""
    data = await _export_current_schema(db)
    data["exported_at"] = datetime.now(timezone.utc).isoformat()
    return data


@router.get("/excel")
async def export_excel(
    db: DbSession,
    current_user: CurrentUser,
) -> StreamingResponse:
    """Export current schema as Excel."""
    data = await _export_current_schema(db)
    
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Entities sheet
        entities_rows = []
        for e in data["entities"]:
            entities_rows.append({
                "entity_code": e["entity_code"],
                "entity_name": e["entity_name"],
                "entity_name_en": e.get("entity_name_en"),
                "description": e.get("description"),
            })
        pd.DataFrame(entities_rows).to_excel(writer, sheet_name="实体定义", index=False)
        
        # Entity Properties sheet
        entity_props_rows = []
        for e in data["entities"]:
            for p in e.get("properties", []):
                entity_props_rows.append({
                    "entity_code": e["entity_code"],
                    "prop_code": p["prop_code"],
                    "prop_name": p["prop_name"],
                    "prop_name_en": p.get("prop_name_en"),
                    "data_type": p.get("data_type"),
                    "options": p.get("options"),
                    "is_required": "TRUE" if p.get("is_required") else "FALSE",
                })
        pd.DataFrame(entity_props_rows).to_excel(writer, sheet_name="实体属性", index=False)
        
        # Relations sheet
        relations_rows = []
        for r in data["relations"]:
            relations_rows.append({
                "relation_code": r["relation_code"],
                "relation_name": r["relation_name"],
                "relation_name_en": r.get("relation_name_en"),
                "head_entity_code": r.get("head_entity_code"),
                "tail_entity_code": r.get("tail_entity_code"),
                "description": r.get("description"),
            })
        pd.DataFrame(relations_rows).to_excel(writer, sheet_name="关系定义", index=False)
        
        # Relation Properties sheet
        relation_props_rows = []
        for r in data["relations"]:
            for p in r.get("properties", []):
                relation_props_rows.append({
                    "relation_code": r["relation_code"],
                    "prop_code": p["prop_code"],
                    "prop_name": p["prop_name"],
                    "prop_name_en": p.get("prop_name_en"),
                    "data_type": p.get("data_type"),
                    "options": p.get("options"),
                    "is_required": "TRUE" if p.get("is_required") else "FALSE",
                })
        pd.DataFrame(relation_props_rows).to_excel(writer, sheet_name="关系属性", index=False)
    
    output.seek(0)
    
    filename = f"schema_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
