"""
客戶群組 Tools — 客戶分群列表、成員查詢
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import Optional
from pydantic import Field

from app import mcp
from tools.base_tool import api_get, fetch_all_pages, resolve_field


@mcp.tool()
def list_customer_groups(
    search_keyword: Optional[str] = Field(default=None, description="群組名稱搜尋關鍵字"),
    max_results: int = Field(default=50, description="最多回傳筆數"),
) -> dict:
    """取得客戶群組列表，支援依名稱搜尋。

    【用途】
    瀏覽或搜尋已建立的客戶群組（分群）。可用於確認客戶標籤分群策略、
    取得群組 ID 後進一步查詢群組成員。

    【呼叫的 Shopline API】
    - GET /v1/customer-groups（無搜尋條件時）
    - GET /v1/customer-groups/search（有搜尋條件時）

    【回傳結構】
    dict 含 total_found, returned, groups[]。
    每個 group 包含 id, name, customers_count, created_at。
    """
    search_keyword = resolve_field(search_keyword)
    if search_keyword:
        params = {"keyword": search_keyword, "per_page": min(max_results, 50)}
        data = api_get("customer_groups_search", params=params)
        groups = data.get("items", [])
    else:
        groups = fetch_all_pages("customer_groups", max_pages=max(1, max_results // 50))

    results = []
    for g in groups[:max_results]:
        results.append({
            "id": g.get("id"),
            "name": g.get("name"),
            "customers_count": g.get("customers_count", 0),
            "created_at": g.get("created_at"),
            "updated_at": g.get("updated_at"),
        })

    return {
        "total_found": len(groups),
        "returned": len(results),
        "groups": results,
    }


@mcp.tool()
def get_customer_group_members(
    group_id: str = Field(description="客戶群組 ID（由 list_customer_groups 回傳）"),
) -> dict:
    """取得指定客戶群組中的所有客戶 ID 列表。

    【用途】
    查詢特定群組包含哪些客戶。回傳客戶 ID 列表，可搭配 get_customer_profile 取得個別客戶詳情。

    【呼叫的 Shopline API】
    - GET /v1/customer-groups/{group_id}/customers

    【回傳結構】
    dict 含 group_id, total_members, customer_ids[]。
    """
    data = api_get("customer_group_customers", path_params={"group_id": group_id})
    customer_ids = data.get("items", data.get("customer_ids", []))

    return {
        "group_id": group_id,
        "total_members": len(customer_ids),
        "customer_ids": customer_ids,
    }
