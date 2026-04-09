"""
Token Tools — API Token 資訊與權限查詢
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import mcp
from tools.base_tool import api_get


@mcp.tool()
def get_token_info() -> dict:
    """取得目前 API Token 的資訊與授權範圍。

    【用途】
    查詢此 API Token 的詳細資訊，包含所屬商家、
    授權的 scope（權限範圍）以及有效期限等。
    適合排查 API 存取問題、確認 token 是否擁有
    所需的操作權限。

    【呼叫的 Shopline API】
    - GET /v1/token/info

    【回傳結構】
    dict 含 token_info，包含 merchant_id, scopes[],
    expires_at, created_at 等欄位。
    """
    data = api_get("token_info")
    info = data.get("token_info", data) if isinstance(data, dict) else {}

    return {
        "token_info": info,
    }
