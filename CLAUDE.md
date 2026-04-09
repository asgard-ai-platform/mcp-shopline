# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Shopline API MCP Server. Wraps the Shopline Open API into 143 AI Agent-callable tools (75 read + 68 write) for e-commerce data analysis (orders, products, inventory, customer behavior). Includes a stdio MCP server for Claude Code / Cowork integration.

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
# End-to-end test for all 143 tools (hits live Shopline API)
python tests/test_all_tools.py

# API connection & endpoint accessibility check
python scripts/auth/test_connection.py

# Explore raw API response structures
python scripts/auth/inspect_data_structure.py
```

No test framework — tests are standalone scripts. All tests hit the live API and require `SHOPLINE_API_TOKEN` environment variable.

## Architecture

### Request Flow

`mcp_server.py` (import triggers @mcp.tool registration) -> `tools/*.py` + `tools/writes/*.py` (business logic) -> `base_tool.py` (HTTP client) -> `config/settings.py` (URL + auth)

### API Layer (`config/` + `tools/base_tool.py`)

- `config/settings.py` — API base URL, token from env, endpoint map (`ENDPOINTS` dict with 135 path templates)
- `tools/base_tool.py` — Shared HTTP client with retry (exponential backoff), pagination (`fetch_all_pages`), date-segmented pagination for >10k results (`fetch_all_pages_by_date_segments`), and helpers (`money_to_float`, `get_translation`). Read methods: `api_get`. Write methods: `api_post`, `api_put`, `api_patch`, `api_delete`.

### Tools Layer (`tools/`)

Read tool modules under `tools/` — each decorated with `@mcp.tool()`:

- `order_tools.py` (12): query_orders, get_sales_summary, get_top_products, get_sales_trend, get_channel_comparison, get_order_detail, get_refund_summary, and more
- `product_tools.py` (9): get_product_list, get_product_variants, get_inventory_overview, get_low_stock_alerts, get_warehouses, get_stock_by_warehouse, and more
- `analytics_tools.py` (11): get_rfm_analysis, get_repurchase_analysis, get_customer_geo_analysis, get_inventory_turnover, get_category_sales, get_promotion_analysis, and more
- `customer_tools.py`, `customer_group_tools.py`, `store_credit_tools.py`, `membership_tier_tools.py`, `member_point_tools.py`
- `custom_field_tools.py`, `category_tools.py`, `promotion_tools.py`, `flash_price_tools.py`, `affiliate_tools.py`
- `gift_tools.py`, `addon_product_tools.py`, `subscription_tools.py`, `return_order_tools.py`, `order_delivery_tools.py`
- `conversation_tools.py`, `review_tools.py`, `merchant_tools.py`, `payment_tools.py`, `delivery_option_tools.py`
- `channel_tools.py`, `settings_tools.py`, `tax_tools.py`, `staff_tools.py`, `token_tools.py`, `agent_tools.py`

### Write Tools Layer (`tools/writes/`)

Write tool modules (14) — each tool marked `[WRITE]` in its docstring:

- `order_writes.py`, `customer_writes.py`, `product_writes.py`, and more domain-specific write modules
- All write tools use `api_post`, `api_put`, `api_patch`, or `api_delete` from `base_tool.py`
- Importing a module in `mcp_server.py` triggers `@mcp.tool()` registration automatically — no extra wiring needed

### Tool Pattern

Each tool follows this structure within its module:
1. Decorated with `@mcp.tool()` — no schema dict or tool list needed
2. Typed parameters with `Field()` descriptions (Traditional Chinese)
3. Docstring becomes the MCP `description` field
4. Function implementation using `api_get`/`api_post`/`api_put`/`api_patch`/`api_delete`/`fetch_all_pages` from `base_tool.py`
5. If in a new module, add `import tools.your_new_module  # noqa: F401` to `mcp_server.py`

### Write Tool Convention

- Docstring must start with `[WRITE]` to identify tools with side effects
- Must include a `【副作用】` section in the docstring describing what data will be created, modified, or deleted
- Use `api_post`, `api_put`, `api_patch`, or `api_delete` from `base_tool.py` — never raw HTTP calls
- Return a standardised dict: `{"success": bool, "resource_id": str, "message": str}`
- Place in `tools/writes/{domain}_writes.py`

### Coverage Audit

Run `python scripts/audit/check_coverage.py` to compare implemented tools against the full Shopline Open API endpoint list and identify gaps.

### MCP Server (`mcp_server.py`)

Stdio JSON-RPC 2.0 MCP server. Configured via `.mcp.json`. Handles `initialize`, `tools/list`, `tools/call`, `ping`. Notifications (no `id`) are silently consumed.

### Key API Constraints

- Available endpoints (200): Orders, Products, Warehouses, Categories, Return Orders, Promotions, Product Stocks, Customers, Channels, and many more (135 endpoints mapped in `ENDPOINTS`)
- Search limit: 10,000 results; use `fetch_all_pages_by_date_segments` for larger queries
- Pagination: `page` + `per_page` (max 50); 0.2s delay between pages for rate limiting
- `orders_search` endpoint does NOT support `sort_by` parameter (handled in `fetch_all_pages`)
- Order status: online = `confirmed`, POS = `completed`; both are in `VALID_ORDER_STATUSES` set used across tool files to filter valid revenue orders
- Channel: `created_from` = `"shop"` (online) / `"pos"` (POS)
- Currency: all monetary values in TWD, returned as float via `money_to_float()` (extracts `dollars` field from Shopline money objects)
