"""
商店設定 Tools — 應用程式設定查詢
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import mcp
from tools.base_tool import api_get


@mcp.tool()
def get_app_settings() -> dict:
    """取得商店應用程式設定。

    【用途】
    查詢商店層級的應用程式設定，包含功能開關、主題設定等。
    適合確認商店目前的功能啟用狀態。

    注意：此端點已被 Shopline 標記為 deprecated（已棄用），
    但仍可使用，涵蓋以求完整性。建議優先使用其他設定端點
    取得最新商店資訊。

    【呼叫的 Shopline API】
    - GET /v1/settings/app

    【回傳結構】
    dict 含 settings，包含各應用程式層級設定欄位。
    實際欄位依商店設定而定。
    """
    data = api_get("settings_app")
    settings = data.get("settings", data) if isinstance(data, dict) else {}

    return {
        "settings": settings,
    }
