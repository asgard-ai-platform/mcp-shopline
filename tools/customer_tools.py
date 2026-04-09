"""
客戶相關 Tools — 客戶列表、搜尋、完整個人檔案
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import Optional
from pydantic import Field

from app import mcp
from tools.base_tool import (
    api_get, fetch_all_pages, money_to_float, get_translation, resolve_field
)


@mcp.tool()
def list_customers(
    search_keyword: Optional[str] = Field(default=None, description="搜尋關鍵字（姓名、email、電話）"),
    max_results: int = Field(default=50, description="最多回傳筆數"),
) -> dict:
    """取得客戶列表，支援依關鍵字搜尋客戶。

    【用途】
    查詢特定客戶或瀏覽客戶清單。可用姓名、email、電話搜尋。
    若要取得單一客戶的完整資訊（含儲值金、點數、等級），請改用 get_customer_profile。

    【呼叫的 Shopline API】
    - GET /v1/customers（無搜尋條件時）
    - GET /v1/customers/search（有搜尋條件時）

    【回傳結構】
    dict 含 total_found, returned, customers[]。
    每個 customer 包含 id, name, email, phone, tags, created_at。
    """
    search_keyword = resolve_field(search_keyword)
    if search_keyword:
        params = {"keyword": search_keyword, "per_page": min(max_results, 50)}
        data = api_get("customers_search", params=params)
        customers = data.get("items", [])
    else:
        customers = fetch_all_pages("customers", max_pages=max(1, max_results // 50))

    results = []
    for c in customers[:max_results]:
        results.append({
            "id": c.get("id"),
            "name": c.get("name"),
            "email": c.get("email"),
            "phone": c.get("phone"),
            "gender": c.get("gender"),
            "birthday": c.get("birthday"),
            "tags": c.get("tags", []),
            "membership_tier": c.get("membership_tier_id"),
            "total_spent": money_to_float(c.get("total_spent")),
            "orders_count": c.get("orders_count", 0),
            "created_at": c.get("created_at"),
        })

    return {
        "total_found": len(customers),
        "returned": len(results),
        "customers": results,
    }


@mcp.tool()
def get_customer_profile(
    customer_id: str = Field(description="客戶內部 ID（由 list_customers 回傳的 id 欄位）"),
) -> dict:
    """取得單一客戶的完整輪廓（基本資料 + 儲值金紀錄 + 會員點數 + 會員等級變動 + 優惠券）。

    【用途】
    回答「這位客戶是誰、消費狀況、會員狀態」等完整客戶概況問題。適合客服
    場景或個別會員分析。若要批次分析客戶行為請改用 get_rfm_analysis。

    【呼叫的 Shopline API】
    - GET /v1/customers/{customer_id}
    - GET /v1/customers/{customer_id}/store-credit-history
    - GET /v1/customers/{customer_id}/member-points
    - GET /v1/customers/{customer_id}/membership-tier-history
    - GET /v1/customers/{customer_id}/promotions

    【回傳結構】
    dict 包含 profile / store_credits / member_points / tier_history / promotions 五大區塊。
    金額皆為 float (TWD)。
    """
    path_params = {"customer_id": customer_id}

    detail = api_get("customer_detail", path_params=path_params)
    c = detail if "name" in detail else detail.get("item", detail)

    profile = {
        "id": c.get("id"),
        "name": c.get("name"),
        "email": c.get("email"),
        "phone": c.get("phone"),
        "gender": c.get("gender"),
        "birthday": c.get("birthday"),
        "tags": c.get("tags", []),
        "total_spent": money_to_float(c.get("total_spent")),
        "orders_count": c.get("orders_count", 0),
        "membership_tier_id": c.get("membership_tier_id"),
        "created_at": c.get("created_at"),
        "updated_at": c.get("updated_at"),
    }

    store_credits = []
    try:
        sc_data = api_get("customer_store_credit_history", path_params=path_params)
        for sc in (sc_data.get("items", []) if isinstance(sc_data, dict) else []):
            store_credits.append({
                "amount": money_to_float(sc.get("amount")),
                "balance": money_to_float(sc.get("balance")),
                "type": sc.get("type"),
                "note": sc.get("note"),
                "created_at": sc.get("created_at"),
            })
    except Exception:
        store_credits = [{"error": "無法取得儲值金紀錄"}]

    member_points = []
    try:
        mp_data = api_get("customer_member_points", path_params=path_params)
        for mp in (mp_data.get("items", []) if isinstance(mp_data, dict) else []):
            member_points.append({
                "points": mp.get("points", 0),
                "balance": mp.get("balance", 0),
                "type": mp.get("type"),
                "note": mp.get("note"),
                "created_at": mp.get("created_at"),
            })
    except Exception:
        member_points = [{"error": "無法取得會員點數紀錄"}]

    tier_history = []
    try:
        th_data = api_get("customer_membership_tier_history", path_params=path_params)
        for th in (th_data.get("items", []) if isinstance(th_data, dict) else []):
            tier_history.append({
                "from_tier": th.get("from_tier"),
                "to_tier": th.get("to_tier"),
                "reason": th.get("reason"),
                "created_at": th.get("created_at"),
            })
    except Exception:
        tier_history = [{"error": "無法取得會員等級變動紀錄"}]

    promotions = []
    try:
        promo_data = api_get("customer_promotions", path_params=path_params)
        for p in (promo_data.get("items", []) if isinstance(promo_data, dict) else []):
            promotions.append({
                "id": p.get("id"),
                "title": get_translation(p.get("title_translations")),
                "status": p.get("status"),
                "discount_type": p.get("discount_type"),
            })
    except Exception:
        promotions = [{"error": "無法取得客戶優惠"}]

    return {
        "profile": profile,
        "store_credits": store_credits,
        "member_points": member_points,
        "tier_history": tier_history,
        "promotions": promotions,
    }
