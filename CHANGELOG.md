# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
