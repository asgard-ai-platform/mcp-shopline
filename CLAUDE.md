# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Shopline API MCP Server. Wraps the Shopline Open API into 19 AI Agent-callable tools for e-commerce data analysis (orders, products, inventory, customer behavior). Includes a stdio MCP server for Claude Code / Cowork integration.

## Setup

```bash
export SHOPLINE_API_TOKEN=your_token_here
```

## Running Tests

```bash
# End-to-end test for all 19 tools (hits live Shopline API)
python tests/test_all_tools.py

# API connection & endpoint accessibility check
python scripts/auth/test_connection.py
```

No test framework — tests are standalone scripts. All tests hit the live API and require `SHOPLINE_API_TOKEN` environment variable.

## Architecture

### API Layer (`config/` + `tools/base_tool.py`)

- `config/settings.py` — API base URL, token from env, endpoint map
- `tools/base_tool.py` — Shared HTTP client with retry, pagination (`fetch_all_pages`), date-segmented pagination for >10k results, and helpers (`money_to_float`, `get_translation`)

### Tools Layer (`tools/`)

Each tool module exports `[{"schema": {...}, "function": callable}]`:

- `order_tools.py` -> `ORDER_TOOLS` (7): query_orders, get_sales_summary, get_top_products, get_sales_trend, get_channel_comparison, get_order_detail, get_refund_summary
- `product_tools.py` -> `PRODUCT_TOOLS` (6): get_product_list, get_product_variants, get_inventory_overview, get_low_stock_alerts, get_warehouses, get_stock_by_warehouse
- `analytics_tools.py` -> `ANALYTICS_TOOLS` (6): get_rfm_analysis, get_repurchase_analysis, get_customer_geo_analysis, get_inventory_turnover, get_category_sales, get_promotion_analysis

`tool_registry.py` aggregates into `ALL_TOOLS` with `get_tool_schemas()`, `execute_tool()`.

### MCP Server (`mcp_server.py`)

Stdio JSON-RPC 2.0 MCP server. Configured via `.mcp.json`. Supports `initialize`, `tools/list`, `tools/call`.

### Adding a New Tool

1. Define schema dict (Claude API `tool_use` format)
2. Implement function using `api_get`/`fetch_all_pages` from `base_tool.py`
3. Append to module's tool list (e.g., `ORDER_TOOLS`)
4. Auto-registers via `tool_registry.py` and `mcp_server.py`

### Key API Constraints

- Available endpoints (200): Orders, Products, Warehouses, Categories, Return Orders, Promotions, Product Stocks
- Blocked: Customers (403), Channels (422/403, but store info in order data)
- Search limit: 10,000 results; use `fetch_all_pages_by_date_segments` for more
- Pagination: `page` + `per_page` (max 50); 0.2s delay between pages
- Order status: online = `confirmed`, POS = `completed`; include both for revenue
- Channel: `created_from` = `"shop"` (online) / `"pos"` (POS)
