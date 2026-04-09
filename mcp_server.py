#!/usr/bin/env python3
"""
Shopline API MCP Server — 供 Claude Code / Claude Cowork 調用

透過 MCP Python SDK stdio 傳輸，暴露 Shopline API 工具。

使用方式:
  1. 在 .mcp.json 中設定（見專案根目錄範例）
  2. 或手動啟動: python mcp_server.py
"""
import sys
import os

# 確保能 import tools 模組與 app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 匯入工具模組以觸發 @mcp.tool() 裝飾器的副作用（工具註冊）
# --- 既有 read tools ---
import tools.order_tools          # noqa: F401
import tools.product_tools        # noqa: F401
import tools.analytics_tools      # noqa: F401

# --- Phase 1: Customer domain read tools ---
import tools.customer_tools       # noqa: F401
import tools.customer_group_tools # noqa: F401
import tools.store_credit_tools   # noqa: F401
import tools.membership_tier_tools  # noqa: F401
import tools.member_point_tools   # noqa: F401
import tools.custom_field_tools   # noqa: F401

# --- Phase 3A: Product/Promotion domain read tools ---
import tools.category_tools        # noqa: F401
import tools.promotion_tools       # noqa: F401
import tools.flash_price_tools     # noqa: F401
import tools.affiliate_tools       # noqa: F401
import tools.gift_tools            # noqa: F401
import tools.addon_product_tools   # noqa: F401
import tools.subscription_tools    # noqa: F401

# --- Phase 3B: Order extended domain read tools ---
import tools.return_order_tools    # noqa: F401
import tools.order_delivery_tools  # noqa: F401
import tools.conversation_tools    # noqa: F401
import tools.review_tools          # noqa: F401

# --- Phase 3C: Store settings domain read tools ---
import tools.merchant_tools        # noqa: F401
import tools.payment_tools         # noqa: F401
import tools.delivery_option_tools # noqa: F401
import tools.channel_tools         # noqa: F401
import tools.settings_tools        # noqa: F401
import tools.tax_tools             # noqa: F401
import tools.staff_tools           # noqa: F401
import tools.token_tools           # noqa: F401
import tools.agent_tools           # noqa: F401

# --- Write tools ---
import tools.writes.customer_writes  # noqa: F401

from app import mcp


def main():
    mcp.run()  # 預設 stdio transport


if __name__ == "__main__":
    main()
