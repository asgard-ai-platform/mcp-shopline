"""
商家寫入 Tools — 更新商家基本資料
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pydantic import Field

from app import mcp
from tools.base_tool import api_put


@mcp.tool()
def update_merchant(
    merchant_id: str = Field(description="商家 ID"),
    merchant_data: dict = Field(
        description=(
            "要更新的商家欄位，例如："
            "{\"name\": \"我的商店\", \"email\": \"shop@example.com\", \"phone\": \"02-1234-5678\", \"address\": \"台北市...\"}"
        )
    ),
) -> dict:
    """[WRITE] 更新商家基本資料。

    【用途】
    修改指定商家的名稱、聯絡資訊、地址等基本設定。僅傳入要修改的欄位，未傳入的欄位不會被覆蓋。
    適合商家資料異動（如搬遷、更名）時同步更新 Shopline 商家設定。

    【呼叫的 Shopline API】
    - PUT /v1/merchants/{merchant_id}

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 修改商家資料，變更立即生效
    - 商家名稱等資訊可能顯示於顧客可見的頁面（如收據、通知 Email）
    - 不可復原，但可再次呼叫此工具覆蓋
    """
    if not merchant_data:
        return {"success": False, "resource_id": merchant_id, "message": "未提供任何要更新的欄位"}

    api_put("merchant_update", json_body=merchant_data,
            path_params={"merchant_id": merchant_id})
    return {
        "success": True,
        "resource_id": merchant_id,
        "message": f"商家 {merchant_id} 資料已更新",
    }
