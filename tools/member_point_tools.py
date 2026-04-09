"""
會員點數規則 Tools — 點數規則查詢
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import mcp
from tools.base_tool import api_get


@mcp.tool()
def list_member_point_rules() -> dict:
    """取得商店的會員點數規則設定。

    【用途】
    查看商店設定的點數回饋規則（消費回饋比例、點數到期規則等）。
    用於分析會員忠誠度計畫或對照客戶點數異動。

    【呼叫的 Shopline API】
    - GET /v1/member_point_rules

    【回傳結構】
    dict 含 total, rules[]。
    每條規則含 id, name, type, value, conditions 等。
    """
    data = api_get("member_point_rules")
    rules = data.get("items", []) if isinstance(data, dict) else []

    results = []
    for r in rules:
        results.append({
            "id": r.get("id"),
            "name": r.get("name"),
            "type": r.get("type"),
            "value": r.get("value"),
            "status": r.get("status"),
            "conditions": r.get("conditions"),
            "created_at": r.get("created_at"),
        })

    return {
        "total": len(results),
        "rules": results,
    }
