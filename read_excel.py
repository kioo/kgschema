import pandas as pd
import json

xl = pd.ExcelFile(r'd:\Ai\kgschema\知识图谱Schema-0104-v3.xlsx')

# Read each sheet
entities_df = pd.read_excel(xl, '实体类型')
entity_props_df = pd.read_excel(xl, '实体属性')
relations_df = pd.read_excel(xl, '关系类型')
relation_props_df = pd.read_excel(xl, '关系属性')

# Convert to dict and save as JSON
data = {
    '实体类型': {
        'columns': entities_df.columns.tolist(),
        'shape': list(entities_df.shape),
        'data': entities_df.fillna('').to_dict(orient='records')
    },
    '实体属性': {
        'columns': entity_props_df.columns.tolist(),
        'shape': list(entity_props_df.shape),
        'data': entity_props_df.fillna('').to_dict(orient='records')
    },
    '关系类型': {
        'columns': relations_df.columns.tolist(),
        'shape': list(relations_df.shape),
        'data': relations_df.fillna('').to_dict(orient='records')
    },
    '关系属性': {
        'columns': relation_props_df.columns.tolist(),
        'shape': list(relation_props_df.shape),
        'data': relation_props_df.fillna('').to_dict(orient='records')
    }
}

with open('excel_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Saved to excel_data.json")
print("\n实体类型 columns:", data['实体类型']['columns'])
print("实体类型 rows:", data['实体类型']['shape'][0])
print("\n实体属性 columns:", data['实体属性']['columns'])
print("实体属性 rows:", data['实体属性']['shape'][0])
print("\n关系类型 columns:", data['关系类型']['columns'])
print("关系类型 rows:", data['关系类型']['shape'][0])
print("\n关系属性 columns:", data['关系属性']['columns'])
print("关系属性 rows:", data['关系属性']['shape'][0])
