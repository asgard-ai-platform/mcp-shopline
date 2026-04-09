"""
退貨單寫入 Tools — 建立、更新退貨／退款申請
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pydantic import Field

from app import mcp
from tools.base_tool import api_post, api_put


@mcp.tool()
def create_return_order(
    return_order_data: dict = Field(
        description=(
            "退貨單資料，例如 {\"order_id\": \"ORD123\", \"reason\": \"商品瑕疵\", "
            "\"items\": [{\"line_item_id\": \"LI001\", \"quantity\": 1}]}"
        )
    ),
) -> dict:
    """[WRITE] 建立退貨／退款申請單。

    【用途】
    針對指定訂單建立退貨或退款申請，適用於客服處理退換貨流程。

    【呼叫的 Shopline API】
    - POST /v1/return_orders

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str, return_order: dict。

    【副作用】
    - 在系統中建立退貨／退款申請記錄，狀態為待審核
    - 觸發退貨流程，可能影響庫存預留與財務帳務（視 Shopline 退貨處理設定）
    - 若訂單不符退貨條件（如已超過退貨期限），API 可能回傳錯誤
    """
    result = api_post("return_order_create", json_body=return_order_data)

    return_order = result if "id" in result else result.get("item", result)
    return_order_id = return_order.get("id", "")
    return {
        "success": True,
        "resource_id": str(return_order_id),
        "message": f"退貨單 {return_order_id} 建立成功",
        "return_order": return_order,
    }


@mcp.tool()
def update_return_order(
    return_order_id: str = Field(description="退貨單 ID"),
    return_order_data: dict = Field(
        description="要更新的退貨單欄位，例如 {\"status\": \"approved\", \"note\": \"已確認退款\"}"
    ),
) -> dict:
    """[WRITE] 更新退貨單狀態或資料。

    【用途】
    修改退貨單的審核狀態、退款金額、備註等資料，適用於客服審核退貨申請流程。

    【呼叫的 Shopline API】
    - PUT /v1/return_orders/{return_order_id}

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 退貨單資料變更立即生效
    - 若將狀態更新為「已退款」，可能觸發實際退款動作並影響財務帳務
    - 不可復原，請謹慎確認狀態變更
    """
    api_put("return_order_update", json_body=return_order_data,
            path_params={"return_order_id": return_order_id})
    return {
        "success": True,
        "resource_id": return_order_id,
        "message": f"退貨單 {return_order_id} 資料已更新",
    }
