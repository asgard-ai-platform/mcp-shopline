"""
加購商品 Tools — 加購商品列表與搜尋
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import Optional
from pydantic import Field

from app import mcp
from tools.base_tool import api_get, fetch_all_pages, money_to_float, get_translation


@mcp.tool()
def list_addon_products(
    search_keyword: Optional[str] = Field(default=None, description="搜尋關鍵字（加購商品名稱）"),
    max_results: int = Field(default=50, description="最多回傳筆數"),
) -> dict:
    """取得加購商品列表，支援依關鍵字搜尋。

    【用途】
    瀏覽或搜尋商店所有加購商品（Addon Products）設定，了解加購商品名稱、
    價格與庫存狀況。若提供搜尋關鍵字則呼叫搜尋端點，否則列出所有加購商品。
    適合分析加購策略與商品搭配情況。

    【呼叫的 Shopline API】
    - GET /v1/addon_products（無搜尋條件時）
    - GET /v1/addon_products/search（有搜尋條件時）

    【回傳結構】
    dict 含 total_found, returned, items[]。
    每筆包含 id, name, sku, price (TWD), quantity, status, created_at。
    """
    if search_keyword:
        params = {"keyword": search_keyword, "per_page": min(max_results, 50)}
        data = api_get("addon_products_search", params=params)
        addon_products = data.get("items", [])
    else:
        addon_products = fetch_all_pages("addon_products", max_pages=max(1, max_results // 50))

    results = []
    for p in addon_products[:max_results]:
        results.append({
            "id": p.get("id"),
            "name": get_translation(p.get("name_translations") or p.get("name")),
            "sku": p.get("sku"),
            "price": money_to_float(p.get("price")),
            "quantity": p.get("quantity"),
            "unlimited_quantity": p.get("unlimited_quantity"),
            "status": p.get("status"),
            "created_at": p.get("created_at"),
            "updated_at": p.get("updated_at"),
        })

    return {
        "total_found": len(addon_products),
        "returned": len(results),
        "items": results,
    }
