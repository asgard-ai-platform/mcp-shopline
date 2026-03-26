# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Shopline API MCP Server. Wraps the Shopline Open API into 19 AI Agent-callable tools for e-commerce data analysis (orders, products, inventory, customer behavior). Includes a stdio MCP server for Claude Code / Cowork integration.

Code comments and tool descriptions are in Traditional Chinese (zh-Hant). The only external dependency is `requests`.

## Setup & Running

```bash
pip install requests
export SHOPLINE_API_TOKEN=your_token_here

# Run the MCP server directly (stdio JSON-RPC 2.0)
python mcp_server.py

# Or auto-detected via .mcp.json when opened in Claude Code
```

## Running Tests

```bash
# End-to-end test for all 19 tools (hits live Shopline API)
python tests/test_all_tools.py

# API connection & endpoint accessibility check
python scripts/auth/test_connection.py

# Explore raw API response structures
python scripts/auth/inspect_data_structure.py
```

No test framework — tests are standalone scripts. All tests hit the live API and require `SHOPLINE_API_TOKEN` environment variable.

## Architecture

### Request Flow

`mcp_server.py` (stdin JSON-RPC) -> `tool_registry.py` (lookup + dispatch) -> `tools/*_tools.py` (business logic) -> `base_tool.py` (HTTP client) -> `config/settings.py` (URL + auth)

### API Layer (`config/` + `tools/base_tool.py`)

- `config/settings.py` — API base URL, token from env, endpoint map (`ENDPOINTS` dict with path templates)
- `tools/base_tool.py` — Shared HTTP client with retry (exponential backoff), pagination (`fetch_all_pages`), date-segmented pagination for >10k results (`fetch_all_pages_by_date_segments`), and helpers (`money_to_float`, `get_translation`)

### Tools Layer (`tools/`)

Each tool module exports a list of `{"schema": {...}, "function": callable}` dicts:

- `order_tools.py` -> `ORDER_TOOLS` (7): query_orders, get_sales_summary, get_top_products, get_sales_trend, get_channel_comparison, get_order_detail, get_refund_summary
- `product_tools.py` -> `PRODUCT_TOOLS` (6): get_product_list, get_product_variants, get_inventory_overview, get_low_stock_alerts, get_warehouses, get_stock_by_warehouse
- `analytics_tools.py` -> `ANALYTICS_TOOLS` (6): get_rfm_analysis, get_repurchase_analysis, get_customer_geo_analysis, get_inventory_turnover, get_category_sales, get_promotion_analysis

`tool_registry.py` aggregates into `ALL_TOOLS` with `get_tool_schemas()`, `execute_tool()`.

### Tool Pattern

Each tool follows this structure within its module:
1. `TOOL_NAME_SCHEMA` dict — Claude API `tool_use` format with `name`, `description`, `input_schema`
2. Function implementation using `api_get`/`fetch_all_pages` from `base_tool.py`
3. Appended as `{"schema": SCHEMA, "function": fn}` to the module's tool list (e.g., `ORDER_TOOLS`)
4. Auto-registers via `tool_registry.py` imports — no extra wiring needed

### MCP Server (`mcp_server.py`)

Stdio JSON-RPC 2.0 MCP server. Configured via `.mcp.json`. Handles `initialize`, `tools/list`, `tools/call`, `ping`. Notifications (no `id`) are silently consumed.

### Key API Constraints

- Available endpoints (200): Orders, Products, Warehouses, Categories, Return Orders, Promotions, Product Stocks
- Blocked: Customers (403), Channels (422/403, but store info available in order data via `order.channel.created_by_channel_name`)
- Search limit: 10,000 results; use `fetch_all_pages_by_date_segments` for larger queries
- Pagination: `page` + `per_page` (max 50); 0.2s delay between pages for rate limiting
- `orders_search` endpoint does NOT support `sort_by` parameter (handled in `fetch_all_pages`)
- Order status: online = `confirmed`, POS = `completed`; both are in `VALID_ORDER_STATUSES` set used across tool files to filter valid revenue orders
- Channel: `created_from` = `"shop"` (online) / `"pos"` (POS)
- Currency: all monetary values in TWD, returned as float via `money_to_float()` (extracts `dollars` field from Shopline money objects)
