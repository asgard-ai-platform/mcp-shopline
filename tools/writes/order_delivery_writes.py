"""
訂單配送寫入 Tools — 更新訂單配送資訊
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pydantic import Field

from app import mcp
from tools.base_tool import api_put


@mcp.tool()
def update_order_delivery(
    delivery_id: str = Field(description="訂單配送記錄 ID"),
    delivery_data: dict = Field(
        description=(
            "要更新的配送欄位，例如："
            "{\"tracking_number\": \"123456\", \"carrier\": \"黑貓宅急便\", \"status\": \"shipped\"}"
        )
    ),
) -> dict:
    """[WRITE] 更新訂單配送資訊。

    【用途】
    修改指定訂單配送記錄的物流資訊，例如更新追蹤號碼、物流公司、配送狀態等。
    適合整合第三方物流系統後回寫配送狀態。

    【呼叫的 Shopline API】
    - PUT /v1/order_deliveries/{delivery_id}

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 修改訂單配送記錄，變更立即生效
    - 狀態變更可能觸發 Shopline 的自動通知（如寄送出貨通知 Email 給顧客）
    - 不可復原，但可再次呼叫此工具覆蓋
    """
    if not delivery_data:
        return {"success": False, "resource_id": delivery_id, "message": "未提供任何要更新的欄位"}

    api_put("order_delivery_update", json_body=delivery_data,
            path_params={"delivery_id": delivery_id})
    return {
        "success": True,
        "resource_id": delivery_id,
        "message": f"訂單配送記錄 {delivery_id} 已更新",
    }
