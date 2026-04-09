"""
代理人 Tools — 商店代理人帳號查詢
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import mcp
from tools.base_tool import api_get, get_translation


@mcp.tool()
def list_agents() -> dict:
    """取得商店的代理人帳號清單。

    【用途】
    查看商店目前設定的代理人帳號，代理人通常用於
    客服、業務等特定角色的操作授權。適合確認代理人
    配置或了解有哪些外部帳號有商店操作權限。

    【呼叫的 Shopline API】
    - GET /v1/agents

    【回傳結構】
    dict 含 total, agents[]。
    每個 agent 包含 id, name, email, role,
    enabled, created_at 等。
    """
    data = api_get("agents")
    items = data.get("items", []) if isinstance(data, dict) else []

    results = []
    for a in items:
        results.append({
            "id": a.get("id"),
            "name": get_translation(a.get("name_translations")) or a.get("name"),
            "email": a.get("email"),
            "role": a.get("role"),
            "enabled": a.get("enabled"),
            "created_at": a.get("created_at"),
        })

    return {
        "total": len(results),
        "agents": results,
    }
