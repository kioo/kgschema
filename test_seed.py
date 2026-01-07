"""
Test seed script locally to debug errors.
"""
import json
import re
from pathlib import Path

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

# Read JSON
json_path = Path(r'd:\Ai\kgschema\app\scripts\schema_data.json')
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

entities_data = data['实体类型']['data']
entity_props_data = data['实体属性']['data']
relations_data = data['关系类型']['data']
relation_props_data = data['关系属性']['data']

print("=== Entities ===")
entity_codes = []
for row in entities_data:
    entity_type = row.get('实体类型', '')
    if entity_type:
        code = normalize_code(entity_type)
        entity_codes.append(code)
        print(f"  {code} -> {row.get('中文含义')}")

print(f"\nTotal entities: {len(entity_codes)}")
print(f"Unique: {len(set(entity_codes))}")

# Check entity properties
print("\n=== Entity Properties ===")
current_entity = None
prop_count = 0
for row in entity_props_data:
    seq = row.get('序号', '')
    if seq and seq != '':
        entity_type_raw = row.get('实体类型', '')
        if entity_type_raw:
            current_entity = extract_entity_code(entity_type_raw)
            print(f"  Entity: {current_entity}")
    
    prop_code = str(row.get('属性名', '')).strip()
    if prop_code and current_entity:
        prop_count += 1

print(f"Total entity properties: {prop_count}")

print("\n=== Relations ===")
relation_codes = []
for row in relations_data:
    relation_type = row.get('关系类型', '')
    if relation_type:
        code = normalize_code(relation_type)
        head = normalize_code(row.get('起点实体', ''))
        tail = normalize_code(row.get('终点实体', ''))
        
        # Map special names
        if head == "PATHOGENIC_MECHANISM":
            head = "PATHOGENESIS"
        if tail == "PATHOGENIC_MECHANISM":
            tail = "PATHOGENESIS"
        
        head_exists = head in entity_codes
        tail_exists = tail in entity_codes
        
        status = "✓" if head_exists and tail_exists else "✗"
        relation_codes.append(code)
        print(f"  {status} {code}: {head} -> {tail}")
        
        if not head_exists:
            print(f"    WARNING: Head entity not found: {head}")
        if not tail_exists:
            print(f"    WARNING: Tail entity not found: {tail}")

print(f"\nTotal relations: {len(relation_codes)}")
print(f"Unique: {len(set(relation_codes))}")

# Check relation properties
print("\n=== Relation Properties ===")
current_relation = None
rel_prop_count = 0
for row in relation_props_data:
    seq = row.get('序号', '')
    if seq and seq != '':
        relation_type_raw = row.get('关系类型', '')
        if relation_type_raw:
            match = re.match(r'^([A-Z0-9_]+)', str(relation_type_raw).strip())
            if match:
                current_relation = match.group(1)
            else:
                current_relation = normalize_code(relation_type_raw)
            print(f"  Relation: {current_relation}")
    
    prop_code = str(row.get('属性名', '')).strip()
    if prop_code and current_relation:
        rel_prop_count += 1

print(f"Total relation properties: {rel_prop_count}")
