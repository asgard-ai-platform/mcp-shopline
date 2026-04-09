"""
採購單寫入 Tools — 建立、刪除採購單
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from typing import List
from pydantic import Field

from app import mcp
from tools.base_tool import api_post, _api_request


@mcp.tool()
def create_purchase_order(
    purchase_order_data: dict = Field(
        description="採購單資料，例如 {supplier_id, items: [{sku, quantity, cost}, ...], ...}"
    ),
) -> dict:
    """[WRITE] 建立新採購單。

    【用途】
    在 Shopline POS 系統中建立一筆新的採購單，用於記錄向供應商進貨的資訊。

    【呼叫的 Shopline API】
    - POST /v1/pos/purchase_orders

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str, purchase_order: dict。

    【副作用】
    - 在 POS 採購單列表中新增一筆記錄
    - 採購單建立後可進行後續入庫確認操作
    """
    result = api_post("purchase_order_create", json_body=purchase_order_data)
    po = result if "id" in result else result.get("item", result)
    return {
        "success": True,
        "resource_id": po.get("id", ""),
        "message": f"採購單建立成功（ID: {po.get('id', '')}）",
        "purchase_order": po,
    }


@mcp.tool()
def delete_purchase_orders(
    purchase_order_ids: List[str] = Field(description="要刪除的採購單 ID 列表（可批次刪除多筆）"),
) -> dict:
    """[WRITE] 批次刪除採購單。

    【用途】
    一次刪除一或多筆 POS 採購單記錄，適合清除測試資料或作廢錯誤採購單。

    【呼叫的 Shopline API】
    - DELETE /v1/pos/purchase_orders

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 永久刪除指定的採購單記錄，不可復原
    - 若採購單已執行入庫操作，刪除可能受限（取決於 Shopline 實作）
    """
    if not purchase_order_ids:
        return {"success": False, "resource_id": "", "message": "未提供任何採購單 ID"}

    _api_request(
        "DELETE",
        "purchase_order_delete",
        json_body={"ids": purchase_order_ids},
        retry_on_client_error=False,
    )
    ids_str = ", ".join(purchase_order_ids)
    return {
        "success": True,
        "resource_id": ids_str,
        "message": f"採購單已刪除（共 {len(purchase_order_ids)} 筆）：{ids_str}",
    }
