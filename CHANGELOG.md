# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.3.0] - 2026-04-09

### Added
- Complete Shopline Open API v1 coverage: 143 tools (75 read + 68 write) across 32 resource sections
- 26 new read tool modules covering Customers, Customer Groups, Store Credits, Membership Tiers, Member Points, Custom Fields, Categories, Promotions, Flash Price Campaigns, Affiliate Campaigns, Gifts, Addon Products, Subscriptions, Return Orders, Order Delivery, Conversations, Reviews, Merchants, Payments, Delivery Options, Channels, Settings, Taxes, Staff, Token, Agents
- 14 write tool modules in `tools/writes/` for order, customer, product, promotion, category, return order, conversation, review, gift, purchase order, media, order delivery, delivery option, and merchant operations
- `api_post`, `api_put`, `api_patch`, `api_delete` in `base_tool.py` with differentiated retry strategy (4xx no-retry for writes)
- 5 Roadmap analytics tools: `get_refund_by_store`, `get_stock_transfer_suggestions`, `get_promotion_roi`, `get_customer_lifecycle`, `get_slow_movers`
- 5 new order read tools: archived orders, labels, tags, action logs, transactions
- 3 new product read tools: locked inventory, purchase orders
- `scripts/audit/check_coverage.py` for endpoint coverage verification
- Write tool docstrings include `[WRITE]` prefix and `【副作用】` (side effects) documentation
- `reference/shopline-api-inventory.md` — complete 129-endpoint catalog

### Changed
- `config/settings.py` ENDPOINTS expanded from 14 to 135 path templates
- `base_tool.py` refactored: shared `_api_request()` internal function, HTTP 204 handling
- `app.py` updated to use `FastMCP` from standard `mcp` package
- `mcp_server.py` registers all 40 tool modules (26 read + 14 write)
- README.md: added write tools warning section, expanded tool tables, updated API coverage
- CLAUDE.md: fixed stale `tool_registry.py` references, updated architecture
- CONTRIBUTING.md: added write tool conventions and docstring spec

### Removed
- `reference/` removed from `.gitignore` (now tracked)

## [0.2.0] - 2026-03-30

### Added
- MCP Python SDK integration — server now uses `MCPServer` and `@mcp.tool()` decorator pattern (replaces hand-rolled JSON-RPC 2.0 stdio loop)
- `app.py`: MCPServer singleton module to avoid circular imports between tool modules

### Changed
- Renamed CLI entry point from `shopline-mcp` to `mcp-shopline` (aligns with PyPI package name)
- Converted all 19 tool definitions to typed function signatures with `pydantic.Field()` parameter descriptions; tool descriptions now come from docstrings
- Bumped `requires-python` to `>=3.10` (MCP SDK requirement)
- Added `mcp` as a project dependency
- Updated CONTRIBUTING.md: new `@mcp.tool()` decorator guide replaces schema-dict instructions

### Removed
- `tools/tool_registry.py` — superseded by `@mcp.tool()` automatic registration

## [0.1.0] - 2025-06-01

### Added

- MCP server (stdio JSON-RPC 2.0) with Claude Code auto-discovery via `.mcp.json`
- **Order tools (7)**: `query_orders`, `get_sales_summary`, `get_top_products`, `get_sales_trend`, `get_channel_comparison`, `get_order_detail`, `get_refund_summary`
- **Product & inventory tools (6)**: `get_product_list`, `get_product_variants`, `get_inventory_overview`, `get_low_stock_alerts`, `get_warehouses`, `get_stock_by_warehouse`
- **Analytics tools (6)**: `get_rfm_analysis`, `get_repurchase_analysis`, `get_customer_geo_analysis`, `get_inventory_turnover`, `get_category_sales`, `get_promotion_analysis`
- Shared HTTP client with exponential backoff retry, pagination, and date-segmented pagination for >10k results
- E2E test suite for all 19 tools
- API connection test and data structure inspection scripts
