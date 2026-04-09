"""
自訂欄位 Tools — 客戶自訂欄位定義查詢
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import mcp
from tools.base_tool import api_get, get_translation


@mcp.tool()
def list_custom_fields() -> dict:
    """取得商店定義的客戶自訂欄位清單。

    【用途】
    查看商店在客戶資料上設定了哪些額外自訂欄位（如生日、偏好、備註等）。
    用於了解客戶資料結構或分析資料完整度。

    【呼叫的 Shopline API】
    - GET /v1/custom_fields

    【回傳結構】
    dict 含 total, fields[]。
    每個 field 包含 id, name, type, options 等。
    """
    data = api_get("custom_fields")
    fields = data.get("items", []) if isinstance(data, dict) else []

    results = []
    for f in fields:
        results.append({
            "id": f.get("id"),
            "name": get_translation(f.get("name_translations")) or f.get("name"),
            "type": f.get("type"),
            "required": f.get("required", False),
            "options": f.get("options", []),
            "created_at": f.get("created_at"),
        })

    return {
        "total": len(results),
        "fields": results,
    }
