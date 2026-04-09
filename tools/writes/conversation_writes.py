"""
對話訊息寫入 Tools — 發送訂單訊息與商店訊息
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pydantic import Field

from app import mcp
from tools.base_tool import api_post


@mcp.tool()
def send_order_message(
    message_data: dict = Field(
        description=(
            "訊息資料，例如 {\"order_id\": \"ORD123\", \"message\": \"您的訂單已出貨，"
            "請注意查收！\", \"sender_type\": \"merchant\"}"
        )
    ),
) -> dict:
    """[WRITE] 發送與特定訂單相關的對話訊息。

    【用途】
    針對指定訂單發送訊息給買家，適用於出貨通知、客服回覆、訂單異常說明等場景。

    【呼叫的 Shopline API】
    - POST /v1/conversations/order-messages

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str, conversation: dict。

    【副作用】
    - 在買家的對話收件匣中新增一則訊息，買家可即時收到通知
    - 訊息送出後無法撤回或修改
    """
    result = api_post("conversation_order_message", json_body=message_data)

    conversation = result if isinstance(result, dict) else {}
    resource_id = conversation.get("id", conversation.get("message_id", ""))
    return {
        "success": True,
        "resource_id": str(resource_id),
        "message": "訂單訊息發送成功",
        "conversation": conversation,
    }


@mcp.tool()
def send_shop_message(
    message_data: dict = Field(
        description=(
            "訊息資料，例如 {\"customer_id\": \"CUST456\", \"message\": \"感謝您的支持，"
            "本週特惠活動開始囉！\", \"sender_type\": \"merchant\"}"
        )
    ),
) -> dict:
    """[WRITE] 發送一般商店對話訊息。

    【用途】
    對客戶發送非特定訂單的通用訊息，適用於行銷通知、活動公告、客服主動聯繫等場景。

    【呼叫的 Shopline API】
    - POST /v1/conversations/shop-messages

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str, conversation: dict。

    【副作用】
    - 在客戶的對話收件匣中新增一則商店訊息，客戶可即時收到通知
    - 訊息送出後無法撤回或修改
    - 大量發送時請注意 Shopline 的訊息頻率限制，以避免觸發反垃圾機制
    """
    result = api_post("conversation_shop_message", json_body=message_data)

    conversation = result if isinstance(result, dict) else {}
    resource_id = conversation.get("id", conversation.get("message_id", ""))
    return {
        "success": True,
        "resource_id": str(resource_id),
        "message": "商店訊息發送成功",
        "conversation": conversation,
    }
