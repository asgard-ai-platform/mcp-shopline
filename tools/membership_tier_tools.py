"""
會員等級 Tools — 會員等級列表、個別會員等級變動歷程
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pydantic import Field

from app import mcp
from tools.base_tool import api_get, fetch_all_pages


@mcp.tool()
def list_membership_tiers() -> dict:
    """取得商店的所有會員等級定義。

    【用途】
    查看商店設定了哪些會員等級、升等門檻、各等級權益。
    用於分析會員結構或確認等級設定。

    【呼叫的 Shopline API】
    - GET /v1/membership_tiers

    【回傳結構】
    dict 含 total, tiers[]。
    每個 tier 包含 id, name, threshold, benefits 等。
    """
    data = api_get("membership_tiers")
    tiers = data.get("items", []) if isinstance(data, dict) else []

    results = []
    for t in tiers:
        results.append({
            "id": t.get("id"),
            "name": t.get("name"),
            "threshold": t.get("threshold"),
            "description": t.get("description"),
            "benefits": t.get("benefits"),
            "created_at": t.get("created_at"),
        })

    return {
        "total": len(results),
        "tiers": results,
    }


@mcp.tool()
def get_customer_tier_history(
    customer_id: str = Field(description="客戶內部 ID"),
) -> dict:
    """取得指定客戶的會員等級變動歷程。

    【用途】
    追蹤客戶會員等級升降紀錄，了解是升等還是降級、原因為何。
    搭配 list_membership_tiers 對照等級名稱。

    【呼叫的 Shopline API】
    - GET /v1/customers/{customer_id}/membership-tier-history

    【回傳結構】
    dict 含 customer_id, total_changes, history[]。
    每筆含 from_tier, to_tier, reason, created_at。
    """
    data = api_get("customer_membership_tier_history",
                   path_params={"customer_id": customer_id})
    items = data.get("items", []) if isinstance(data, dict) else []

    history = []
    for h in items:
        history.append({
            "from_tier": h.get("from_tier"),
            "to_tier": h.get("to_tier"),
            "reason": h.get("reason"),
            "created_at": h.get("created_at"),
        })

    return {
        "customer_id": customer_id,
        "total_changes": len(history),
        "history": history,
    }
