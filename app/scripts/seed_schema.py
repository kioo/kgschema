"""
Seed script to import initial data from pre-parsed JSON schema file.

Run with: python -m app.scripts.seed_schema
"""
import asyncio
import json
import re
import traceback
from pathlib import Path
from typing import Dict, Set

from sqlalchemy import delete
from app.db.session import async_session_maker
from app.models import Entity, EntityProperty, Relation, RelationProperty


def normalize_code(s: str) -> str:
    if not s:
        return ""
    s = str(s).strip()
    match = re.match(r'^([A-Za-z0-9_\s]+)', s)
    if match:
        code = match.group(1).strip()
        code = re.sub(r'\s+', '_', code)
        return code.upper()
    return s.upper().replace(' ', '_')


def extract_entity_code(text: str) -> str:
    if not text:
        return ""
    text = str(text).strip()
    match = re.match(r'^([A-Za-z\s]+)', text)
    if match:
        code = match.group(1).strip()
        return code.replace(' ', '_').upper()
    return text.replace(' ', '_').upper()


def map_data_type(dtype: str) -> str:
    if not dtype:
        return "STRING"
    dtype = str(dtype).strip().upper()
    if dtype in ["STRING", "TEXT"]:
        return "STRING"
    elif dtype in ["INTEGER", "INT"]:
        return "INTEGER"
    elif dtype == "FLOAT":
        return "FLOAT"
    elif dtype in ["BOOLEAN", "BOOL"]:
        return "BOOLEAN"
    return "STRING"


def is_required(val: str) -> bool:
    if not val:
        return False
    return "✅" in str(val)


async def seed_schema():
    """Import schema from JSON file."""
    try:
        script_dir = Path(__file__).parent
        json_path = script_dir / "schema_data.json"
        
        print(f"Looking for JSON at: {json_path}")
        
        if not json_path.exists():
            print(f"Error: {json_path} not found!")
            return
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("JSON loaded successfully")
        
        entities_data = data['实体类型']['data']
        entity_props_data = data['实体属性']['data']
        relations_data = data['关系类型']['data']
        relation_props_data = data['关系属性']['data']
        
        # Phase 1: Clear and create entities
        async with async_session_maker() as db:
            print("Phase 1: Clearing existing data...")
            await db.execute(delete(RelationProperty))
            await db.execute(delete(Relation))
            await db.execute(delete(EntityProperty))
            await db.execute(delete(Entity))
            await db.commit()
            print("Data cleared.")
        
        entity_code_to_id: Dict[str, str] = {}
        
        # Phase 2: Create entities
        async with async_session_maker() as db:
            print("Phase 2: Creating entities...")
            for row in entities_data:
                entity_type = row.get('实体类型', '')
                if not entity_type:
                    continue
                    
                entity_code = normalize_code(entity_type)
                if not entity_code:
                    continue
                    
                entity = Entity(
                    entity_code=entity_code,
                    entity_name=str(row.get('中文含义', '')).strip() or entity_code,
                    entity_name_en=str(row.get('实体类型', '')).strip() if row.get('实体类型') else None,
                    description=str(row.get('概念补充', '')).strip() if row.get('概念补充') else None,
                    status="ACTIVE",
                    is_active=True,
                )
                db.add(entity)
                await db.flush()
                entity_code_to_id[entity_code] = str(entity.id)
                print(f"  Created entity: {entity_code}")
            
            await db.commit()
            print(f"Entities created: {len(entity_code_to_id)}")
        
        # Phase 3: Create entity properties (with dedup)
        async with async_session_maker() as db:
            print("Phase 3: Creating entity properties...")
            current_entity_code = None
            prop_order = 0
            props_created = 0
            seen_props: Dict[str, Set[str]] = {}  # entity_id -> set of prop_codes
            
            for row in entity_props_data:
                seq = row.get('序号', '')
                if seq and seq != '':
                    entity_type_raw = row.get('实体类型', '')
                    if entity_type_raw:
                        current_entity_code = extract_entity_code(entity_type_raw)
                        prop_order = 0
                
                prop_code = str(row.get('属性名', '')).strip()
                if not prop_code:
                    continue
                
                if not current_entity_code or current_entity_code not in entity_code_to_id:
                    continue
                
                entity_id = entity_code_to_id[current_entity_code]
                prop_code_normalized = prop_code.replace(' ', '_').lower()
                
                # Skip duplicates
                if entity_id not in seen_props:
                    seen_props[entity_id] = set()
                if prop_code_normalized in seen_props[entity_id]:
                    print(f"  Skipping duplicate: {current_entity_code}.{prop_code_normalized}")
                    continue
                seen_props[entity_id].add(prop_code_normalized)
                
                prop = EntityProperty(
                    entity_id=entity_id,
                    prop_code=prop_code_normalized,
                    prop_name=str(row.get('说明', prop_code)).strip() if row.get('说明') else prop_code,
                    prop_name_en=prop_code,
                    data_type=map_data_type(row.get('数据类型', 'String')),
                    is_required=is_required(row.get('必填', '')),
                    display_order=prop_order,
                )
                db.add(prop)
                prop_order += 1
                props_created += 1
            
            await db.commit()
            print(f"Entity properties created: {props_created}")
        
        relation_code_to_id: Dict[str, str] = {}
        
        # Phase 4: Create relations
        async with async_session_maker() as db:
            print("Phase 4: Creating relations...")
            for row in relations_data:
                relation_type = row.get('关系类型', '')
                if not relation_type:
                    continue
                
                relation_code = normalize_code(relation_type)
                if not relation_code:
                    continue
                
                head_code = normalize_code(row.get('起点实体', ''))
                tail_code = normalize_code(row.get('终点实体', ''))
                
                if head_code == "PATHOGENIC_MECHANISM":
                    head_code = "PATHOGENESIS"
                if tail_code == "PATHOGENIC_MECHANISM":
                    tail_code = "PATHOGENESIS"
                
                head_id = entity_code_to_id.get(head_code)
                tail_id = entity_code_to_id.get(tail_code)
                
                if not head_id or not tail_id:
                    print(f"  Skipping relation {relation_code}: missing entities")
                    continue
                
                relation = Relation(
                    relation_code=relation_code,
                    relation_name=str(row.get('中文名称', '')).strip() or relation_code,
                    relation_name_en=str(row.get('关系类型', '')).strip() if row.get('关系类型') else None,
                    head_entity_id=head_id,
                    tail_entity_id=tail_id,
                    description=str(row.get('描述', '')).strip() if row.get('描述') else None,
                    status="ACTIVE",
                    is_active=True,
                )
                db.add(relation)
                await db.flush()
                relation_code_to_id[relation_code] = str(relation.id)
                print(f"  Created relation: {relation_code}")
            
            await db.commit()
            print(f"Relations created: {len(relation_code_to_id)}")
        
        # Phase 5: Create relation properties (with dedup)
        async with async_session_maker() as db:
            print("Phase 5: Creating relation properties...")
            current_relation_code = None
            prop_order = 0
            rel_props_created = 0
            seen_rel_props: Dict[str, Set[str]] = {}  # relation_id -> set of prop_codes
            
            for row in relation_props_data:
                seq = row.get('序号', '')
                if seq and seq != '':
                    relation_type_raw = row.get('关系类型', '')
                    if relation_type_raw:
                        match = re.match(r'^([A-Z0-9_]+)', str(relation_type_raw).strip())
                        if match:
                            current_relation_code = match.group(1)
                        else:
                            current_relation_code = normalize_code(relation_type_raw)
                        prop_order = 0
                
                prop_code = str(row.get('属性名', '')).strip()
                if not prop_code:
                    continue
                
                if not current_relation_code or current_relation_code not in relation_code_to_id:
                    continue
                
                relation_id = relation_code_to_id[current_relation_code]
                prop_code_normalized = prop_code.replace(' ', '_').lower()
                
                # Skip duplicates
                if relation_id not in seen_rel_props:
                    seen_rel_props[relation_id] = set()
                if prop_code_normalized in seen_rel_props[relation_id]:
                    print(f"  Skipping duplicate: {current_relation_code}.{prop_code_normalized}")
                    continue
                seen_rel_props[relation_id].add(prop_code_normalized)
                
                prop = RelationProperty(
                    relation_id=relation_id,
                    prop_code=prop_code_normalized,
                    prop_name=str(row.get('说明', prop_code)).strip() if row.get('说明') else prop_code,
                    prop_name_en=prop_code,
                    data_type=map_data_type(row.get('数据类型', 'String')),
                    is_required=is_required(row.get('必填', '')),
                    display_order=prop_order,
                )
                db.add(prop)
                prop_order += 1
                rel_props_created += 1
            
            await db.commit()
            print(f"Relation properties created: {rel_props_created}")
        
        print("\n=== Import Complete ===")
        print(f"Entities: {len(entity_code_to_id)}")
        print(f"Relations: {len(relation_code_to_id)}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(seed_schema())
