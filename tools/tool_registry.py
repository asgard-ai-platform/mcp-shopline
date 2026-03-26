"""
Tool Registry — 統一註冊所有 Tools，供 AI Agent 調用
"""
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.order_tools import ORDER_TOOLS
from tools.product_tools import PRODUCT_TOOLS
from tools.analytics_tools import ANALYTICS_TOOLS

# 所有可用 Tools
ALL_TOOLS = ORDER_TOOLS + PRODUCT_TOOLS + ANALYTICS_TOOLS


def get_tool_schemas():
    """回傳所有 Tool 的 schema 列表（供 Claude API tool_use 使用）"""
    return [tool["schema"] for tool in ALL_TOOLS]


def get_tool_by_name(name):
    """依名稱查找 Tool"""
    for tool in ALL_TOOLS:
        if tool["schema"]["name"] == name:
            return tool
    return None


def execute_tool(name, **kwargs):
    """執行指定 Tool"""
    tool = get_tool_by_name(name)
    if not tool:
        return {"error": f"Tool '{name}' not found"}
    try:
        return tool["function"](**kwargs)
    except Exception as e:
        return {"error": str(e)}


def list_tools():
    """列出所有 Tool 的名稱與描述"""
    return [
        {"name": t["schema"]["name"], "description": t["schema"]["description"]}
        for t in ALL_TOOLS
    ]


if __name__ == "__main__":
    print("=" * 60)
    print("可用 AI Agent Tools 列表")
    print("=" * 60)
    for i, t in enumerate(list_tools(), 1):
        print(f"\n  {i}. {t['name']}")
        print(f"     {t['description']}")

    print(f"\n共 {len(ALL_TOOLS)} 個 Tools")

    print("\n\n" + "=" * 60)
    print("Tool Schemas (Claude API format)")
    print("=" * 60)
    schemas = get_tool_schemas()
    print(json.dumps(schemas, ensure_ascii=False, indent=2))
