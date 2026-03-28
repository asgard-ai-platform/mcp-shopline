# MCP Shopline

[![PyPI version](https://img.shields.io/pypi/v/mcp-shopline)](https://pypi.org/project/mcp-shopline/)
[![Python versions](https://img.shields.io/pypi/pyversions/mcp-shopline)](https://pypi.org/project/mcp-shopline/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[繁體中文](README.zh-TW.md)

An open-source [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) server that wraps the [Shopline Open API](https://open-api.docs.shoplineapp.com/docs/getting-started) into 19 AI-callable tools for e-commerce data analysis.

Built for [Claude Code](https://claude.ai/code), Claude Cowork, and any MCP-compatible AI client. Enables AI agents to query orders, products, inventory, customer behavior, and promotions from Shopline stores through natural language.

## What This Does

- **19 ready-to-use tools** covering orders, products, inventory, customer analytics, and promotions
- **MCP server** (stdio JSON-RPC 2.0) — plug into Claude Code and start asking questions immediately
- **Zero external dependencies** beyond Python 3.9+ standard library and `requests`
- **Built-in pagination, retry, and rate limiting** — tools handle all API complexity internally
- **Designed for AI agents** — structured JSON output with natural language-friendly parameters (dates as `YYYY-MM-DD`, not timestamps)

## API Reference

This project is built on the [Shopline Open API v1](https://open-api.docs.shoplineapp.com/docs/getting-started).

- API Documentation: https://open-api.docs.shoplineapp.com
- Authentication: Bearer token via Shopline merchant admin
- Base URL: `https://open.shopline.io/v1/`

You need a valid Shopline API access token from a Shopline merchant account. Refer to the [Shopline API authentication guide](https://open-api.docs.shoplineapp.com/docs/authentication) for how to obtain one.

---

## Quick Start

### Install

```bash
pip install mcp-shopline
```

Or use uvx (no install needed):

```bash
uvx --from mcp-shopline shopline-mcp
```

Set your API token:

```bash
export SHOPLINE_API_TOKEN=your_token_here
```

### Use with Claude Code

Add the server via the Claude CLI:

```bash
claude mcp add --transport stdio shopline -- shopline-mcp
```

Or with the environment variable inline:

```bash
claude mcp add --transport stdio shopline -e SHOPLINE_API_TOKEN=your_token_here -- shopline-mcp
```

If you clone the repo locally, the `.mcp.json` config will be auto-detected by Claude Code and all 19 tools become available immediately.

### Use with Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "shopline": {
      "command": "shopline-mcp",
      "env": {
        "SHOPLINE_API_TOKEN": "your_token_here"
      }
    }
  }
}
```

Or with uvx:

```json
{
  "mcpServers": {
    "shopline": {
      "command": "uvx",
      "args": ["--from", "mcp-shopline", "shopline-mcp"],
      "env": {
        "SHOPLINE_API_TOKEN": "your_token_here"
      }
    }
  }
}
```

---

## Tools (19)

### Orders (7)

| Tool | Description |
|------|-------------|
| `query_orders` | Query orders by date, status, channel, store |
| `get_sales_summary` | Revenue, AOV, item price, payment/delivery breakdown |
| `get_top_products` | Product sales ranking by quantity or revenue |
| `get_sales_trend` | Daily/weekly/monthly sales trend data |
| `get_channel_comparison` | Compare performance across stores/channels |
| `get_order_detail` | Full order detail with line items |
| `get_refund_summary` | Return order statistics and refund amounts |

### Products & Inventory (6)

| Tool | Description |
|------|-------------|
| `get_product_list` | Search products by keyword, brand |
| `get_product_variants` | SKU variants with size x color matrix |
| `get_inventory_overview` | Total inventory summary by brand |
| `get_low_stock_alerts` | Low stock / out-of-stock SKU alerts |
| `get_warehouses` | List all warehouses and store locations |
| `get_stock_by_warehouse` | Per-warehouse stock distribution matrix |

### Analytics (6)

| Tool | Description |
|------|-------------|
| `get_rfm_analysis` | Customer RFM segmentation |
| `get_repurchase_analysis` | Repurchase rate and cycle analysis |
| `get_customer_geo_analysis` | Customer geographic distribution |
| `get_inventory_turnover` | Stock turnover rate and days |
| `get_category_sales` | Sales breakdown by product category |
| `get_promotion_analysis` | Promotion campaign effectiveness |

---

## API Endpoint Coverage

Based on [Shopline Open API v1](https://open-api.docs.shoplineapp.com):

| Endpoint | Status | Notes |
|----------|--------|-------|
| [Orders](https://open-api.docs.shoplineapp.com/docs/order) | 200 | Full access |
| [Products](https://open-api.docs.shoplineapp.com/docs/product) | 200 | Full access |
| [Warehouses](https://open-api.docs.shoplineapp.com/docs/warehouse) | 200 | Full access |
| [Categories](https://open-api.docs.shoplineapp.com/docs/category) | 200 | Full access |
| [Return Orders](https://open-api.docs.shoplineapp.com/docs/return-order) | 200 | Full access |
| [Promotions](https://open-api.docs.shoplineapp.com/docs/promotion) | 200 | Full access |
| [Product Stocks](https://open-api.docs.shoplineapp.com/docs/product-stock) | 200 | Per-warehouse breakdown |
| [Customers](https://open-api.docs.shoplineapp.com/docs/customer) | 403 | Requires additional permissions |
| Channels | 422/403 | Not needed (store info embedded in order data) |

> **Note:** Endpoint availability depends on your Shopline API token permissions. The status above reflects a typical merchant setup. If you have broader permissions, additional endpoints may work.

---

## Project Structure

```
mcp-shopline/
├── mcp_server.py              # MCP Server (stdio JSON-RPC 2.0)
├── .mcp.json                  # Claude Code MCP auto-discovery config
├── .env.example               # Environment variable template
├── config/
│   └── settings.py            # API config (token from env, endpoints)
├── tools/
│   ├── base_tool.py           # Shared HTTP client (retry, pagination)
│   ├── order_tools.py         # Order tools (7)
│   ├── product_tools.py       # Product/inventory tools (6)
│   ├── analytics_tools.py     # Analytics tools (6)
│   └── tool_registry.py       # Unified tool registry
├── tests/
│   └── test_all_tools.py      # E2E tests for all 19 tools
└── scripts/auth/
    ├── test_connection.py     # API connection validator
    └── inspect_data_structure.py  # API response structure explorer
```

## API Constraints

These are Shopline Open API limitations handled internally by the tools:

- **Pagination**: `page` + `per_page` (max 50), 0.2s delay between pages for rate limiting
- **Search limit**: 10,000 results max; `fetch_all_pages_by_date_segments()` splits large queries by date range
- **Order status**: online orders use `confirmed`, POS uses `completed` — tools include both by default
- **Channel identification**: `created_from` = `"shop"` (online) / `"pos"` (retail); store name from `order.channel.created_by_channel_name`
- **Currency**: all monetary values in TWD (New Taiwan Dollar), returned as float via `money_to_float()`

---

## Development

### Setup from Source

```bash
git clone https://github.com/asgard-ai-platform/mcp-shopline.git
cd mcp-shopline
pip install -e .
```

### Run Tests

```bash
python tests/test_all_tools.py
python scripts/auth/test_connection.py
```

### Adding a New Tool

1. Define a schema dict (Claude API `tool_use` format with `name`, `description`, `input_schema`)
2. Implement the function using `api_get` / `fetch_all_pages` from `base_tool.py`
3. Append `{"schema": ..., "function": ...}` to the module's tool list
4. Auto-registered via `tool_registry.py` and `mcp_server.py` — no extra wiring needed

---

## Roadmap

- [ ] Add Customers API tools (member profiles, demographics, membership tiers)
- [ ] `get_refund_by_store` — return order breakdown by store/channel
- [ ] `get_stock_transfer_suggestions` — auto-generate inter-warehouse transfer recommendations based on sales velocity and stock levels
- [ ] `get_category_tree` — standalone category structure viewer
- [ ] `get_promotion_roi` — cross-reference promotion periods with sales trend data to calculate lift and ROI
- [ ] `get_customer_lifecycle` — compare RFM segments across two periods to track customer migration (upgrade/churn)
- [ ] `get_slow_movers` — identify products with high inventory but low sales for clearance planning
- [ ] Support for multiple Shopline stores (multi-token)
- [ ] Add webhook support for real-time order notifications
- [x] ~~Publish as a standalone MCP package~~ — [available on PyPI](https://pypi.org/project/mcp-shopline/)

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

When adding new tools, follow the existing pattern in `tools/` and ensure the tool passes the E2E test suite.

## License

MIT
