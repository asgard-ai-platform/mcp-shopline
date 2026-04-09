"""
訂單配送相關 Tools — 配送單明細
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import Optional
from pydantic import Field

from app import mcp
from tools.base_tool import api_get, fetch_all_pages, money_to_float, get_translation


@mcp.tool()
def get_order_delivery(
    delivery_id: str = Field(description="配送單 ID（通常由訂單明細中的 delivery_id 欄位取得）"),
) -> dict:
    """取得單一配送單的完整資訊，包含物流狀態、追蹤編號及收件地址。

    【用途】
    查詢特定出貨單的配送狀態與物流詳情，適用於追蹤包裹、確認收件資料，
    或協助客服處理配送相關問題。配送單 ID 通常來自 get_order_detail 回傳的
    出貨資訊（shipments / deliveries 欄位）。

    【呼叫的 Shopline API】
    - GET /v1/order_deliveries/{delivery_id}

    【回傳結構】
    dict 包含：
    - id：配送單 ID
    - status：配送狀態（如 pending, shipped, delivered）
    - tracking_number：物流追蹤編號
    - tracking_url：物流追蹤連結
    - carrier：物流商名稱
    - shipping_address：收件地址（含姓名、電話、地址欄位）
    - line_items[]：出貨品項（商品名稱、數量）
    - created_at, updated_at
    """
    path_params = {"delivery_id": delivery_id}
    data = api_get("order_delivery_detail", path_params=path_params)

    delivery = data if "id" in data else data.get("item", data)

    raw_items = delivery.get("line_items", delivery.get("items", []))
    line_items = []
    for item in raw_items:
        line_items.append({
            "product_name": get_translation(item.get("product_title_translations")) or item.get("product_title"),
            "variant_title": item.get("variant_title"),
            "quantity": item.get("quantity", 0),
            "sku": item.get("sku"),
        })

    raw_address = delivery.get("shipping_address", {})
    shipping_address = {
        "name": raw_address.get("name"),
        "phone": raw_address.get("phone"),
        "address1": raw_address.get("address1"),
        "address2": raw_address.get("address2"),
        "city": raw_address.get("city"),
        "country": raw_address.get("country"),
        "zip": raw_address.get("zip"),
    } if raw_address else {}

    return {
        "id": delivery.get("id"),
        "status": delivery.get("status"),
        "tracking_number": delivery.get("tracking_number"),
        "tracking_url": delivery.get("tracking_url"),
        "carrier": delivery.get("carrier") or delivery.get("shipping_method"),
        "shipping_address": shipping_address,
        "line_items": line_items,
        "created_at": delivery.get("created_at"),
        "updated_at": delivery.get("updated_at"),
    }
