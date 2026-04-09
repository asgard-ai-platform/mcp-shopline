"""
配送選項寫入 Tools — 更新自取門市資訊
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pydantic import Field

from app import mcp
from tools.base_tool import api_put


@mcp.tool()
def update_pickup_store(
    delivery_option_id: str = Field(description="配送選項 ID"),
    pickup_store_data: dict = Field(
        description=(
            "自取門市資料，例如："
            "{\"store_name\": \"台北信義門市\", \"address\": \"台北市信義區...\", \"phone\": \"02-1234-5678\", \"business_hours\": \"10:00-22:00\"}"
        )
    ),
) -> dict:
    """[WRITE] 更新配送選項的自取門市資訊。

    【用途】
    修改指定配送選項下的自取門市（Pickup Store）資訊，例如更新門市名稱、地址、電話、營業時間等。
    適合門市資訊異動時同步更新 Shopline 的自取門市設定。

    【呼叫的 Shopline API】
    - PUT /v1/delivery_options/{delivery_option_id}/pickup_store

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 修改指定配送選項下的自取門市資訊，變更立即生效
    - 顧客於結帳頁選擇自取時將看到更新後的門市資訊
    - 不可復原，但可再次呼叫此工具覆蓋
    """
    if not pickup_store_data:
        return {"success": False, "resource_id": delivery_option_id, "message": "未提供任何要更新的欄位"}

    api_put("delivery_option_pickup_store", json_body=pickup_store_data,
            path_params={"delivery_option_id": delivery_option_id})
    return {
        "success": True,
        "resource_id": delivery_option_id,
        "message": f"配送選項 {delivery_option_id} 的自取門市資訊已更新",
    }
