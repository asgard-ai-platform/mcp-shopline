"""
快閃價格活動 Tools — 快閃特賣活動列表、單筆詳情
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import Optional
from pydantic import Field

from app import mcp
from tools.base_tool import api_get, fetch_all_pages, money_to_float, get_translation


@mcp.tool()
def list_flash_price_campaigns(
    max_results: int = Field(default=50, description="最多回傳筆數"),
) -> dict:
    """取得快閃價格活動列表。

    【用途】
    瀏覽商店所有快閃特賣（限時特價）活動，了解活動名稱、狀態與時間範圍。
    可取得 campaign_id 後進一步呼叫 get_flash_price_campaign_detail 查詢完整詳情。

    【呼叫的 Shopline API】
    - GET /v1/flash_price_campaigns

    【回傳結構】
    dict 含 total_found, returned, items[]。
    每筆包含 id, title, status, start_at, end_at, created_at。
    """
    campaigns = fetch_all_pages("flash_price_campaigns", max_pages=max(1, max_results // 50))

    results = []
    for c in campaigns[:max_results]:
        results.append({
            "id": c.get("id"),
            "title": get_translation(c.get("title_translations") or c.get("title")),
            "status": c.get("status"),
            "start_at": c.get("start_at"),
            "end_at": c.get("end_at"),
            "created_at": c.get("created_at"),
            "updated_at": c.get("updated_at"),
        })

    return {
        "total_found": len(campaigns),
        "returned": len(results),
        "items": results,
    }


@mcp.tool()
def get_flash_price_campaign_detail(
    campaign_id: str = Field(description="快閃價格活動 ID（由 list_flash_price_campaigns 回傳的 id 欄位）"),
) -> dict:
    """取得單一快閃價格活動的完整詳情。

    【用途】
    查詢特定快閃特賣活動的折扣規則、適用商品與時間設定等完整資訊。
    適合在已知 campaign_id 的情況下取得所有欄位。

    【呼叫的 Shopline API】
    - GET /v1/flash_price_campaigns/{campaign_id}

    【回傳結構】
    dict 包含 id, title, status, discount_type, discount_value,
    products, start_at, end_at, created_at, updated_at 等完整欄位。
    """
    data = api_get("flash_price_campaign_detail", path_params={"campaign_id": campaign_id})
    c = data.get("item", data) if isinstance(data, dict) else data

    return {
        "id": c.get("id"),
        "title": get_translation(c.get("title_translations") or c.get("title")),
        "status": c.get("status"),
        "discount_type": c.get("discount_type"),
        "discount_value": c.get("discount_value"),
        "products": c.get("products", []),
        "start_at": c.get("start_at"),
        "end_at": c.get("end_at"),
        "created_at": c.get("created_at"),
        "updated_at": c.get("updated_at"),
    }
