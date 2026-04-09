"""
商家 Tools — 商家帳號資訊查詢
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import mcp
from tools.base_tool import api_get, get_translation


@mcp.tool()
def list_merchants() -> dict:
    """取得所有商家清單。

    【用途】
    查看此 API token 可存取的商家帳號列表。
    適合多商家環境下確認可操作的商家範圍。

    【呼叫的 Shopline API】
    - GET /v1/merchants

    【回傳結構】
    dict 含 total, merchants[]。
    每個 merchant 包含 id, name, handle, currency, locale, created_at 等。
    """
    data = api_get("merchants")
    items = data.get("items", []) if isinstance(data, dict) else []

    results = []
    for m in items:
        results.append({
            "id": m.get("id"),
            "name": get_translation(m.get("name_translations")) or m.get("name"),
            "handle": m.get("handle"),
            "currency": m.get("currency"),
            "locale": m.get("locale"),
            "country": m.get("country"),
            "created_at": m.get("created_at"),
        })

    return {
        "total": len(results),
        "merchants": results,
    }


@mcp.tool()
def get_merchant_detail(merchant_id: str) -> dict:
    """取得指定商家的詳細資訊。

    【用途】
    查詢單一商家的完整設定資訊，包含聯絡資訊、幣別、語系等。
    適合確認特定商家設定或做資料核對。

    【呼叫的 Shopline API】
    - GET /v1/merchants/{merchant_id}

    【回傳結構】
    dict 含商家詳細欄位：id, name, handle, currency, locale,
    country, email, phone, address, created_at 等。
    """
    data = api_get("merchant_detail", path_params={"merchant_id": merchant_id})
    m = data.get("merchant", data) if isinstance(data, dict) else {}

    return {
        "id": m.get("id"),
        "name": get_translation(m.get("name_translations")) or m.get("name"),
        "handle": m.get("handle"),
        "currency": m.get("currency"),
        "locale": m.get("locale"),
        "country": m.get("country"),
        "email": m.get("email"),
        "phone": m.get("phone"),
        "address": m.get("address"),
        "timezone": m.get("timezone"),
        "created_at": m.get("created_at"),
        "updated_at": m.get("updated_at"),
    }
