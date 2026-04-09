"""
聯盟行銷活動 Tools — 聯盟活動列表、詳情、訂單使用統計
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import Optional
from pydantic import Field

from app import mcp
from tools.base_tool import api_get, fetch_all_pages, money_to_float, get_translation


@mcp.tool()
def list_affiliate_campaigns(
    max_results: int = Field(default=50, description="最多回傳筆數"),
) -> dict:
    """取得聯盟行銷活動列表。

    【用途】
    瀏覽商店所有聯盟行銷（Affiliate）活動，了解活動名稱、狀態與推廣條件。
    可取得 campaign_id 後進一步呼叫 get_affiliate_campaign_detail 或
    get_affiliate_campaign_usage 查詢詳細資訊與訂單使用統計。

    【呼叫的 Shopline API】
    - GET /v1/affiliate_campaigns

    【回傳結構】
    dict 含 total_found, returned, items[]。
    每筆包含 id, title, status, commission_type, commission_value, created_at。
    """
    campaigns = fetch_all_pages("affiliate_campaigns", max_pages=max(1, max_results // 50))

    results = []
    for c in campaigns[:max_results]:
        results.append({
            "id": c.get("id"),
            "title": get_translation(c.get("title_translations") or c.get("title")),
            "status": c.get("status"),
            "commission_type": c.get("commission_type"),
            "commission_value": c.get("commission_value"),
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
def get_affiliate_campaign_detail(
    campaign_id: str = Field(description="聯盟行銷活動 ID（由 list_affiliate_campaigns 回傳的 id 欄位）"),
) -> dict:
    """取得單一聯盟行銷活動的完整詳情。

    【用途】
    查詢特定聯盟行銷活動的佣金規則、適用範圍與推廣連結等完整資訊。
    適合在已知 campaign_id 的情況下取得所有欄位。

    【呼叫的 Shopline API】
    - GET /v1/affiliate_campaigns/{campaign_id}

    【回傳結構】
    dict 包含 id, title, status, commission_type, commission_value,
    tracking_code, start_at, end_at, created_at, updated_at 等完整欄位。
    """
    data = api_get("affiliate_campaign_detail", path_params={"campaign_id": campaign_id})
    c = data.get("item", data) if isinstance(data, dict) else data

    return {
        "id": c.get("id"),
        "title": get_translation(c.get("title_translations") or c.get("title")),
        "status": c.get("status"),
        "commission_type": c.get("commission_type"),
        "commission_value": c.get("commission_value"),
        "tracking_code": c.get("tracking_code"),
        "description": get_translation(c.get("description_translations") or c.get("description")),
        "conditions": c.get("conditions"),
        "start_at": c.get("start_at"),
        "end_at": c.get("end_at"),
        "created_at": c.get("created_at"),
        "updated_at": c.get("updated_at"),
    }


@mcp.tool()
def get_affiliate_campaign_usage(
    campaign_id: str = Field(description="聯盟行銷活動 ID（由 list_affiliate_campaigns 回傳的 id 欄位）"),
) -> dict:
    """取得聯盟行銷活動的訂單使用統計。

    【用途】
    分析特定聯盟行銷活動帶來的訂單數與銷售額，評估推廣效果。
    回傳訂單使用紀錄，可計算總訂單數、總銷售額、佣金金額等。

    【呼叫的 Shopline API】
    - GET /v1/affiliate_campaigns/{campaign_id}/order_usage

    【回傳結構】
    dict 含 campaign_id, total_orders, total_revenue (TWD), items[]。
    每筆訂單包含 order_id, order_number, revenue, commission, created_at。
    """
    data = api_get("affiliate_campaign_order_usage", path_params={"campaign_id": campaign_id})
    items = data.get("items", []) if isinstance(data, dict) else []

    orders = []
    total_revenue = 0.0
    total_commission = 0.0
    for item in items:
        revenue = money_to_float(item.get("revenue") or item.get("total_price"))
        commission = money_to_float(item.get("commission"))
        total_revenue += revenue
        total_commission += commission
        orders.append({
            "order_id": item.get("order_id"),
            "order_number": item.get("order_number"),
            "revenue": revenue,
            "commission": commission,
            "created_at": item.get("created_at"),
        })

    return {
        "campaign_id": campaign_id,
        "total_orders": len(orders),
        "total_revenue": round(total_revenue, 2),
        "total_commission": round(total_commission, 2),
        "items": orders,
    }
