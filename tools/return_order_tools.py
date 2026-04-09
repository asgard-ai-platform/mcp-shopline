"""
退貨單相關 Tools — 退貨單列表、退貨單明細
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import Optional
from pydantic import Field

from app import mcp
from tools.base_tool import api_get, fetch_all_pages, money_to_float, get_translation, resolve_field


@mcp.tool()
def list_return_orders(
    start_date: Optional[str] = Field(default=None, description="查詢起始日期（ISO 8601 格式，如 2024-01-01T00:00:00Z）"),
    end_date: Optional[str] = Field(default=None, description="查詢結束日期（ISO 8601 格式，如 2024-12-31T23:59:59Z）"),
    max_results: int = Field(default=100, description="最多回傳筆數"),
) -> dict:
    """取得退貨單列表，可依建立日期區間篩選。

    【用途】
    查詢特定時段內的退貨申請清單，了解退貨狀況與數量。提供退貨單的摘要資訊
    （含狀態、對應原始訂單、退款金額及退貨品項數）。若需取得單一退貨單的完整
    品項明細，請改用 get_return_order_detail。

    注意：analytics_tools 中的 get_refund_summary 也使用同一端點，但以彙總分析
    為目的；本工具提供的是原始列表檢視，適合逐筆查閱退貨紀錄。

    【呼叫的 Shopline API】
    - GET /v1/return_orders

    【回傳結構】
    dict 含 total_found, returned, return_orders[]。
    每個 return_order 包含 id, status, order_id, total（TWD float）,
    items_count, created_at。
    """
    start_date = resolve_field(start_date)
    end_date = resolve_field(end_date)
    params = {"per_page": 50}
    if start_date:
        params["created_after"] = start_date
    if end_date:
        params["created_before"] = end_date

    max_pages = max(1, max_results // 50)
    items = fetch_all_pages("return_orders", params=params, max_pages=max_pages)

    results = []
    for ro in items[:max_results]:
        line_items = ro.get("line_items", ro.get("items", []))
        results.append({
            "id": ro.get("id"),
            "status": ro.get("status"),
            "order_id": ro.get("order_id"),
            "total": money_to_float(ro.get("total")),
            "items_count": len(line_items),
            "created_at": ro.get("created_at"),
        })

    return {
        "total_found": len(items),
        "returned": len(results),
        "return_orders": results,
    }


@mcp.tool()
def get_return_order_detail(
    return_order_id: str = Field(description="退貨單 ID（由 list_return_orders 回傳的 id 欄位）"),
) -> dict:
    """取得單一退貨單的完整明細，包含所有退貨品項。

    【用途】
    查閱特定退貨申請的完整資訊：退貨原因、每件退貨商品（商品名稱、數量、退款
    金額）、物流狀態及客戶聯絡資料。適合客服處理個案或審核退貨申請時使用。

    【呼叫的 Shopline API】
    - GET /v1/return_orders/{return_order_id}

    【回傳結構】
    dict 包含退貨單基本資訊（id, status, reason, order_id, created_at）、
    金額摘要（total, refund_amount，皆為 TWD float）及 line_items[]。
    每個 line_item 包含 product_name, variant_title, quantity, price。
    """
    path_params = {"return_order_id": return_order_id}
    data = api_get("return_order_detail", path_params=path_params)

    ro = data if "id" in data else data.get("item", data)

    raw_items = ro.get("line_items", ro.get("items", []))
    line_items = []
    for item in raw_items:
        line_items.append({
            "product_name": get_translation(item.get("product_title_translations")) or item.get("product_title"),
            "variant_title": item.get("variant_title"),
            "quantity": item.get("quantity", 0),
            "price": money_to_float(item.get("price")),
        })

    return {
        "id": ro.get("id"),
        "status": ro.get("status"),
        "reason": ro.get("reason"),
        "order_id": ro.get("order_id"),
        "total": money_to_float(ro.get("total")),
        "refund_amount": money_to_float(ro.get("refund_amount")),
        "created_at": ro.get("created_at"),
        "updated_at": ro.get("updated_at"),
        "line_items": line_items,
    }
