"""
員工 Tools — 員工權限查詢
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import mcp
from tools.base_tool import api_get


@mcp.tool()
def get_staff_permissions(staff_id: str) -> dict:
    """取得指定員工的權限設定。

    【用途】
    查詢特定員工帳號在商店後台的存取權限範圍，
    例如可操作的功能模組及操作層級。適合確認員工
    權限配置或排查存取問題。

    【呼叫的 Shopline API】
    - GET /v1/staffs/{staff_id}/permissions

    【回傳結構】
    dict 含 staff_id, permissions[]。
    每個 permission 包含 resource, actions 等，
    描述該員工可操作的資源與動作。
    """
    data = api_get(
        "staff_permissions",
        path_params={"staff_id": staff_id},
    )
    permissions = data.get("permissions", []) if isinstance(data, dict) else []

    return {
        "staff_id": staff_id,
        "permissions": permissions,
    }
