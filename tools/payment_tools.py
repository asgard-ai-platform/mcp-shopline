"""
付款方式 Tools — 商店付款方式設定查詢
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import mcp
from tools.base_tool import api_get, get_translation


@mcp.tool()
def list_payments() -> dict:
    """取得商店啟用的付款方式清單。

    【用途】
    查看商店目前設定的付款方式，例如信用卡、ATM 轉帳、
    貨到付款、第三方支付等。適合確認可用付款渠道或做訂單
    付款方式分析的參考。

    【呼叫的 Shopline API】
    - GET /v1/payments

    【回傳結構】
    dict 含 total, payments[]。
    每個 payment 包含 id, name, payment_type, enabled,
    position, created_at 等。
    """
    data = api_get("payments")
    items = data.get("items", []) if isinstance(data, dict) else []

    results = []
    for p in items:
        results.append({
            "id": p.get("id"),
            "name": get_translation(p.get("name_translations")) or p.get("name"),
            "payment_type": p.get("payment_type"),
            "enabled": p.get("enabled"),
            "position": p.get("position"),
            "created_at": p.get("created_at"),
        })

    return {
        "total": len(results),
        "payments": results,
    }
