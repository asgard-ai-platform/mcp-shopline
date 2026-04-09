"""
商品訂閱 Tools — 訂閱列表、單筆訂閱詳情
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import Optional
from pydantic import Field

from app import mcp
from tools.base_tool import api_get, fetch_all_pages, money_to_float, get_translation


@mcp.tool()
def list_product_subscriptions(
    max_results: int = Field(default=50, description="最多回傳筆數"),
) -> dict:
    """取得商品訂閱列表。

    【用途】
    瀏覽所有商品訂閱紀錄，了解客戶訂閱哪些商品、訂閱狀態與週期設定。
    可取得 subscription_id 後進一步呼叫 get_product_subscription_detail 查詢完整詳情。
    適合分析訂閱收入與客戶留存率。

    【呼叫的 Shopline API】
    - GET /v1/product_subscriptions

    【回傳結構】
    dict 含 total_found, returned, items[]。
    每筆包含 id, customer_id, product_id, status, frequency, next_billing_at, created_at。
    """
    subscriptions = fetch_all_pages("product_subscriptions", max_pages=max(1, max_results // 50))

    results = []
    for s in subscriptions[:max_results]:
        results.append({
            "id": s.get("id"),
            "customer_id": s.get("customer_id"),
            "product_id": s.get("product_id"),
            "variant_id": s.get("variant_id"),
            "status": s.get("status"),
            "frequency": s.get("frequency"),
            "frequency_unit": s.get("frequency_unit"),
            "next_billing_at": s.get("next_billing_at"),
            "created_at": s.get("created_at"),
            "updated_at": s.get("updated_at"),
        })

    return {
        "total_found": len(subscriptions),
        "returned": len(results),
        "items": results,
    }


@mcp.tool()
def get_product_subscription_detail(
    subscription_id: str = Field(description="商品訂閱 ID（由 list_product_subscriptions 回傳的 id 欄位）"),
) -> dict:
    """取得單一商品訂閱的完整詳情。

    【用途】
    查詢特定訂閱紀錄的完整資訊，包含客戶、商品、付款方式、配送設定與
    訂閱週期等所有欄位。適合客服場景或個別訂閱狀態確認。

    【呼叫的 Shopline API】
    - GET /v1/product_subscriptions/{subscription_id}

    【回傳結構】
    dict 包含 id, customer_id, product_id, variant_id, status, frequency,
    frequency_unit, price (TWD), shipping_address, payment_method,
    next_billing_at, created_at, updated_at 等完整欄位。
    """
    data = api_get("product_subscription_detail", path_params={"subscription_id": subscription_id})
    s = data.get("item", data) if isinstance(data, dict) else data

    return {
        "id": s.get("id"),
        "customer_id": s.get("customer_id"),
        "product_id": s.get("product_id"),
        "variant_id": s.get("variant_id"),
        "status": s.get("status"),
        "frequency": s.get("frequency"),
        "frequency_unit": s.get("frequency_unit"),
        "price": money_to_float(s.get("price")),
        "quantity": s.get("quantity"),
        "shipping_address": s.get("shipping_address"),
        "payment_method": s.get("payment_method"),
        "next_billing_at": s.get("next_billing_at"),
        "last_billed_at": s.get("last_billed_at"),
        "created_at": s.get("created_at"),
        "updated_at": s.get("updated_at"),
    }
