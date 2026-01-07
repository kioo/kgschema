"""Check for duplicate property codes in the schema data."""
import json
from pathlib import Path
from collections import defaultdict
import re

def extract_entity_code(text: str) -> str:
    if not text:
        return ""
    text = str(text).strip()
    match = re.match(r'^([A-Za-z\s]+)', text)
    if match:
        code = match.group(1).strip()
        return code.replace(' ', '_').upper()
    return text.replace(' ', '_').upper()

json_path = Path(r'd:\Ai\kgschema\app\scripts\schema_data.json')
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

entity_props_data = data['实体属性']['data']

# Track property codes per entity
entity_props = defaultdict(list)
current_entity = None

for row in entity_props_data:
    seq = row.get('序号', '')
    if seq and seq != '':
        entity_type_raw = row.get('实体类型', '')
        if entity_type_raw:
            current_entity = extract_entity_code(entity_type_raw)
    
    prop_code = str(row.get('属性名', '')).strip()
    if prop_code and current_entity:
        prop_code_normalized = prop_code.replace(' ', '_').lower()
        entity_props[current_entity].append(prop_code_normalized)

print("=== Checking for duplicate entity property codes ===")
for entity, props in entity_props.items():
    seen = set()
    for p in props:
        if p in seen:
            print(f"DUPLICATE in {entity}: {p}")
        seen.add(p)

# Check relation properties
relation_props_data = data['关系属性']['data']

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

relation_props = defaultdict(list)
current_relation = None

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
    
    prop_code = str(row.get('属性名', '')).strip()
    if prop_code and current_relation:
        prop_code_normalized = prop_code.replace(' ', '_').lower()
        relation_props[current_relation].append(prop_code_normalized)

print("\n=== Checking for duplicate relation property codes ===")
for rel, props in relation_props.items():
    seen = set()
    for p in props:
        if p in seen:
            print(f"DUPLICATE in {rel}: {p}")
        seen.add(p)

print("\nDone checking.")
