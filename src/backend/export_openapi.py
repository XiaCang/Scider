"""
导出 OpenAPI schema 到 openapi.json，可直接导入 Postman / Apifox。

用法（在 src/backend 目录下执行）：
    python export_openapi.py
"""

import json
from app.main import app

schema = app.openapi()
with open("openapi.json", "w", encoding="utf-8") as f:
    json.dump(schema, f, ensure_ascii=False, indent=2)

print("openapi.json 已生成，可导入 Postman 或 Apifox。")
