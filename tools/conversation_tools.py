"""
對話相關 Tools — 對話列表、對話訊息
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import Optional
from pydantic import Field

from app import mcp
from tools.base_tool import api_get, fetch_all_pages, money_to_float, get_translation


@mcp.tool()
def list_conversations(
    max_results: int = Field(default=50, description="最多回傳筆數"),
) -> dict:
    """取得客服對話列表。

    【用途】
    瀏覽所有客服對話的摘要清單，了解目前進行中或歷史的客服溝通狀況。
    可依此清單篩選需要進一步查閱訊息內容的對話，再用 get_conversation_messages
    取得完整聊天記錄。

    【呼叫的 Shopline API】
    - GET /v1/conversations

    【回傳結構】
    dict 含 total_found, returned, conversations[]。
    每個 conversation 包含 id, platform（通訊平台）, status（對話狀態）,
    created_at。
    """
    max_pages = max(1, max_results // 50)
    items = fetch_all_pages("conversations", max_pages=max_pages)

    results = []
    for conv in items[:max_results]:
        results.append({
            "id": conv.get("id"),
            "platform": conv.get("platform"),
            "status": conv.get("status"),
            "created_at": conv.get("created_at"),
        })

    return {
        "total_found": len(items),
        "returned": len(results),
        "conversations": results,
    }


@mcp.tool()
def get_conversation_messages(
    conversation_id: str = Field(description="對話 ID（由 list_conversations 回傳的 id 欄位）"),
    max_results: int = Field(default=50, description="最多回傳訊息筆數"),
) -> dict:
    """取得指定對話的完整訊息記錄。

    【用途】
    查閱特定客服對話的所有聊天訊息，適用於了解客戶問題脈絡、審核客服回應品質，
    或追蹤訂單相關諮詢的處理進度。對話 ID 從 list_conversations 取得。

    【呼叫的 Shopline API】
    - GET /v1/conversations/{conversation_id}/messages

    【回傳結構】
    dict 含 conversation_id, total_found, returned, messages[]。
    每個 message 包含 id, sender_type（發送者類型：customer/staff）,
    content（訊息內容）, message_type, created_at。
    """
    path_params = {"conversation_id": conversation_id}
    max_pages = max(1, max_results // 50)
    items = fetch_all_pages(
        "conversation_messages",
        path_params=path_params,
        max_pages=max_pages,
    )

    results = []
    for msg in items[:max_results]:
        results.append({
            "id": msg.get("id"),
            "sender_type": msg.get("sender_type"),
            "content": msg.get("content") or msg.get("body"),
            "message_type": msg.get("message_type") or msg.get("type"),
            "created_at": msg.get("created_at"),
        })

    return {
        "conversation_id": conversation_id,
        "total_found": len(items),
        "returned": len(results),
        "messages": results,
    }
