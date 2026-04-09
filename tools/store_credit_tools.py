"""
客戶儲值金 Tools — 儲值金餘額查詢
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import Optional
from pydantic import Field

from app import mcp
from tools.base_tool import api_get, fetch_all_pages, money_to_float


@mcp.tool()
def list_store_credits(
    max_results: int = Field(default=50, description="最多回傳筆數"),
) -> dict:
    """取得所有客戶的儲值金餘額列表。

    【用途】
    瀏覽客戶儲值金餘額概況，了解儲值金發放與使用狀況。
    可用於計算儲值金負債、找出高餘額客戶。

    【呼叫的 Shopline API】
    - GET /v1/user_credits

    【回傳結構】
    dict 含 total_found, returned, total_balance, credits[]。
    每個 credit 包含 customer_id, balance (TWD float)。
    """
    credits_list = fetch_all_pages("user_credits", max_pages=max(1, max_results // 50))

    results = []
    for cr in credits_list[:max_results]:
        results.append({
            "customer_id": cr.get("customer_id") or cr.get("user_id"),
            "customer_name": cr.get("customer_name") or cr.get("name"),
            "balance": money_to_float(cr.get("balance")),
            "updated_at": cr.get("updated_at"),
        })

    total_balance = sum(r["balance"] for r in results)

    return {
        "total_found": len(credits_list),
        "returned": len(results),
        "total_balance": round(total_balance, 2),
        "credits": results,
    }
