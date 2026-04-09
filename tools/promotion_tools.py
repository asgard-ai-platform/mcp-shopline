"""
促銷活動 Tools — 促銷列表、搜尋、單筆詳情
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import Optional
from pydantic import Field

from app import mcp
from tools.base_tool import api_get, fetch_all_pages, money_to_float, get_translation, resolve_field


@mcp.tool()
def list_promotions(
    status: Optional[str] = Field(default=None, description="促銷狀態篩選，例如 'active'、'inactive'、'scheduled'"),
    max_results: int = Field(default=50, description="最多回傳筆數"),
) -> dict:
    """取得促銷活動列表，支援依狀態篩選。

    【用途】
    瀏覽商店目前所有促銷活動，了解進行中、已排程或已結束的促銷。
    可用於分析促銷策略，或取得 promotion_id 後進一步查詢詳情。

    【呼叫的 Shopline API】
    - GET /v1/promotions

    【回傳結構】
    dict 含 total_found, returned, items[]。
    每筆包含 id, title, status, discount_type, start_at, end_at。
    """
    status = resolve_field(status)
    params = {}
    if status:
        params["status"] = status

    promotions = fetch_all_pages("promotions", params=params, max_pages=max(1, max_results // 50))

    results = []
    for p in promotions[:max_results]:
        results.append({
            "id": p.get("id"),
            "title": get_translation(p.get("title_translations") or p.get("title")),
            "status": p.get("status"),
            "discount_type": p.get("discount_type"),
            "start_at": p.get("start_at"),
            "end_at": p.get("end_at"),
            "created_at": p.get("created_at"),
            "updated_at": p.get("updated_at"),
        })

    return {
        "total_found": len(promotions),
        "returned": len(results),
        "items": results,
    }


@mcp.tool()
def get_promotion_detail(
    promotion_id: str = Field(description="促銷活動 ID（由 list_promotions 或 search_promotions 回傳的 id 欄位）"),
) -> dict:
    """取得單一促銷活動的完整詳情。

    【用途】
    查詢特定促銷活動的折扣規則、適用商品、使用限制等完整資訊。
    適合在已知 promotion_id 的情況下取得所有欄位。

    【呼叫的 Shopline API】
    - GET /v1/promotions/{promotion_id}

    【回傳結構】
    dict 包含 id, title, status, discount_type, discount_value,
    target_type, conditions, start_at, end_at, created_at, updated_at 等完整欄位。
    """
    data = api_get("promotion_detail", path_params={"promotion_id": promotion_id})
    p = data.get("item", data) if isinstance(data, dict) else data

    return {
        "id": p.get("id"),
        "title": get_translation(p.get("title_translations") or p.get("title")),
        "status": p.get("status"),
        "discount_type": p.get("discount_type"),
        "discount_value": p.get("discount_value"),
        "target_type": p.get("target_type"),
        "conditions": p.get("conditions"),
        "coupon_code": p.get("coupon_code"),
        "usage_limit": p.get("usage_limit"),
        "usage_count": p.get("usage_count"),
        "user_usage_limit": p.get("user_usage_limit"),
        "start_at": p.get("start_at"),
        "end_at": p.get("end_at"),
        "created_at": p.get("created_at"),
        "updated_at": p.get("updated_at"),
    }


@mcp.tool()
def search_promotions(
    keyword: str = Field(description="搜尋關鍵字（促銷名稱）"),
    max_results: int = Field(default=50, description="最多回傳筆數"),
) -> dict:
    """依關鍵字搜尋促銷活動。

    【用途】
    快速找到特定名稱的促銷活動，例如搜尋「週年慶」、「黑五」等。
    搜尋結果含 id 可進一步呼叫 get_promotion_detail 取得完整資訊。

    【呼叫的 Shopline API】
    - GET /v1/promotions/search

    【回傳結構】
    dict 含 total_found, returned, items[]。
    每筆包含 id, title, status, discount_type, start_at, end_at。
    """
    params = {"keyword": keyword, "per_page": min(max_results, 50)}
    data = api_get("promotions_search", params=params)
    promotions = data.get("items", [])

    results = []
    for p in promotions[:max_results]:
        results.append({
            "id": p.get("id"),
            "title": get_translation(p.get("title_translations") or p.get("title")),
            "status": p.get("status"),
            "discount_type": p.get("discount_type"),
            "start_at": p.get("start_at"),
            "end_at": p.get("end_at"),
            "created_at": p.get("created_at"),
        })

    return {
        "total_found": len(promotions),
        "returned": len(results),
        "items": results,
    }
