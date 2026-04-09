"""
稅率 Tools — 商店稅率設定查詢
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import mcp
from tools.base_tool import api_get, get_translation


@mcp.tool()
def list_taxes() -> dict:
    """取得商店設定的稅率清單。

    【用途】
    查看商店目前設定的稅率規則，例如營業稅、消費稅等。
    適合確認稅率設定或在財務分析時核對稅務規則。

    【呼叫的 Shopline API】
    - GET /v1/taxes

    【回傳結構】
    dict 含 total, taxes[]。
    每個 tax 包含 id, name, rate, included_in_price,
    country, region, created_at 等。
    """
    data = api_get("taxes")
    items = data.get("items", []) if isinstance(data, dict) else []

    results = []
    for t in items:
        results.append({
            "id": t.get("id"),
            "name": get_translation(t.get("name_translations")) or t.get("name"),
            "rate": t.get("rate"),
            "included_in_price": t.get("included_in_price"),
            "country": t.get("country"),
            "region": t.get("region"),
            "enabled": t.get("enabled"),
            "created_at": t.get("created_at"),
        })

    return {
        "total": len(results),
        "taxes": results,
    }
