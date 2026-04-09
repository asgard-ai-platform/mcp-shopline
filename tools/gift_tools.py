"""
贈品 Tools — 贈品列表與搜尋
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import Optional
from pydantic import Field

from app import mcp
from tools.base_tool import api_get, fetch_all_pages, money_to_float, get_translation


@mcp.tool()
def list_gifts(
    search_keyword: Optional[str] = Field(default=None, description="搜尋關鍵字（贈品名稱）"),
    max_results: int = Field(default=50, description="最多回傳筆數"),
) -> dict:
    """取得贈品列表，支援依關鍵字搜尋。

    【用途】
    瀏覽或搜尋商店所有贈品設定，了解贈品名稱、庫存與適用條件。
    若提供搜尋關鍵字則呼叫搜尋端點，否則列出所有贈品。

    【呼叫的 Shopline API】
    - GET /v1/gifts（無搜尋條件時）
    - GET /v1/gifts/search（有搜尋條件時）

    【回傳結構】
    dict 含 total_found, returned, items[]。
    每筆包含 id, name, sku, quantity, status, created_at。
    """
    if search_keyword:
        params = {"keyword": search_keyword, "per_page": min(max_results, 50)}
        data = api_get("gifts_search", params=params)
        gifts = data.get("items", [])
    else:
        gifts = fetch_all_pages("gifts", max_pages=max(1, max_results // 50))

    results = []
    for g in gifts[:max_results]:
        results.append({
            "id": g.get("id"),
            "name": get_translation(g.get("name_translations") or g.get("name")),
            "sku": g.get("sku"),
            "quantity": g.get("quantity"),
            "unlimited_quantity": g.get("unlimited_quantity"),
            "status": g.get("status"),
            "created_at": g.get("created_at"),
            "updated_at": g.get("updated_at"),
        })

    return {
        "total_found": len(gifts),
        "returned": len(results),
        "items": results,
    }
