#!/usr/bin/env python3
"""
Shopline API MCP Server — 供 Claude Code / Claude Cowork 調用

透過 MCP Python SDK stdio 傳輸，暴露 19 個 Shopline API 工具。

使用方式:
  1. 在 .mcp.json 中設定（見專案根目錄範例）
  2. 或手動啟動: python mcp_server.py
"""
import sys
import os

# 確保能 import tools 模組與 app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 匯入工具模組以觸發 @mcp.tool() 裝飾器的副作用（工具註冊）
import tools.order_tools      # noqa: F401
import tools.product_tools    # noqa: F401
import tools.analytics_tools  # noqa: F401

from app import mcp


def main():
    mcp.run()  # 預設 stdio transport


if __name__ == "__main__":
    main()
