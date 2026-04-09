# MCP Shopline

[![PyPI version](https://img.shields.io/pypi/v/mcp-shopline)](https://pypi.org/project/mcp-shopline/)
[![Python versions](https://img.shields.io/pypi/pyversions/mcp-shopline)](https://pypi.org/project/mcp-shopline/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub stars](https://img.shields.io/github/stars/asgard-ai-platform/mcp-shopline)](https://github.com/asgard-ai-platform/mcp-shopline/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/asgard-ai-platform/mcp-shopline)](https://github.com/asgard-ai-platform/mcp-shopline/issues)
[![GitHub last commit](https://img.shields.io/github/last-commit/asgard-ai-platform/mcp-shopline)](https://github.com/asgard-ai-platform/mcp-shopline/commits/main)

[繁體中文](README.zh-TW.md)

An open-source [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) server that wraps the [Shopline Open API](https://open-api.docs.shoplineapp.com/docs/getting-started) into 143 AI-callable tools (75 read + 68 write) for e-commerce data analysis.

Built for [Claude Code](https://claude.ai/code), Claude Cowork, and any MCP-compatible AI client. Enables AI agents to query orders, products, inventory, customer behavior, and promotions from Shopline stores through natural language.

## What This Does

- **143 ready-to-use tools** covering orders, products, inventory, customers, promotions, categories, subscriptions, conversations, reviews, and more
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
uvx --from mcp-shopline mcp-shopline
```

Set your API token:

```bash
export SHOPLINE_API_TOKEN=your_token_here
```

### Use with Claude Code

Add the server via the Claude CLI:

```bash
claude mcp add --transport stdio shopline -- mcp-shopline
```

Or with the environment variable inline:

```bash
claude mcp add --transport stdio shopline -e SHOPLINE_API_TOKEN=your_token_here -- mcp-shopline
```

If you clone the repo locally, the `.mcp.json` config will be auto-detected by Claude Code and all 143 tools become available immediately.

### Use with Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "shopline": {
      "command": "mcp-shopline",
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
      "args": ["--from", "mcp-shopline", "mcp-shopline"],
      "env": {
        "SHOPLINE_API_TOKEN": "your_token_here"
      }
    }
  }
}
```

---

## Important: Write Tools

This server includes tools that **create, update, and delete** data in your Shopline store.
Your API token's permission scope controls which operations are available.

- Review your token permissions in Shopline merchant admin
- Restrict to only the scopes you need
- Write tools are clearly marked with `[WRITE]` prefix in their descriptions
- Write tests require `SHOPLINE_TEST_WRITES=1` to run

---

## Tools (143)

### Read Tools (75)

#### Orders (12)

| Tool | Description |
|------|-------------|
| `query_orders` | Query orders by date, status, channel, store |
| `get_sales_summary` | Revenue, AOV, item price, payment/delivery breakdown |
| `get_top_products` | Product sales ranking by quantity or revenue |
| `get_sales_trend` | Daily/weekly/monthly sales trend data |
| `get_channel_comparison` | Compare performance across stores/channels |
| `get_order_detail` | Full order detail with line items |
| `get_refund_summary` | Return order statistics and refund amounts |
| `get_archived_orders` | Query archived/closed orders |
| `get_order_labels` | List labels attached to orders |
| `get_order_tags` | List tags attached to orders |
| `get_order_action_logs` | Retrieve action/audit logs for an order |
| `get_order_transactions` | Payment transaction records for an order |

#### Products & Inventory (9)

| Tool | Description |
|------|-------------|
| `get_product_list` | Search products by keyword, brand |
| `get_product_variants` | SKU variants with size x color matrix |
| `get_inventory_overview` | Total inventory summary by brand |
| `get_low_stock_alerts` | Low stock / out-of-stock SKU alerts |
| `get_warehouses` | List all warehouses and store locations |
| `get_stock_by_warehouse` | Per-warehouse stock distribution matrix |
| `get_locked_inventory` | View inventory locked by pending orders |
| `list_purchase_orders` | List purchase/replenishment orders |
| `get_purchase_order_detail` | Full detail of a single purchase order |

#### Analytics (11)

| Tool | Description |
|------|-------------|
| `get_rfm_analysis` | Customer RFM segmentation |
| `get_repurchase_analysis` | Repurchase rate and cycle analysis |
| `get_customer_geo_analysis` | Customer geographic distribution |
| `get_inventory_turnover` | Stock turnover rate and days |
| `get_category_sales` | Sales breakdown by product category |
| `get_promotion_analysis` | Promotion campaign effectiveness |
| `get_refund_by_store` | Return order breakdown by store/channel |
| `get_stock_transfer_suggestions` | Auto-generate inter-warehouse transfer recommendations |
| `get_promotion_roi` | Cross-reference promotion periods with sales trend to calculate lift and ROI |
| `get_customer_lifecycle` | Compare RFM segments across two periods to track customer migration |
| `get_slow_movers` | Identify products with high inventory but low sales for clearance planning |

#### Customers (9)

| Tool | Description |
|------|-------------|
| `list_customers` | Search and list customer profiles |
| `get_customer_profile` | Full profile for a single customer |
| `list_customer_groups` | List customer segmentation groups |
| `get_customer_group_members` | Members within a customer group |
| `list_store_credits` | Store credit balances and history |
| `list_membership_tiers` | Membership tier definitions |
| `get_customer_tier_history` | Tier upgrade/downgrade history for a customer |
| `list_member_point_rules` | Point earning and redemption rules |
| `list_custom_fields` | Custom field definitions for customer profiles |

#### Categories & Promotions (14)

| Tool | Description |
|------|-------------|
| `get_category_tree` | Full category hierarchy tree |
| `get_category_detail` | Detail for a single category |
| `list_promotions` | List all promotion campaigns |
| `get_promotion_detail` | Full detail for a single promotion |
| `search_promotions` | Search promotions by keyword or status |
| `list_flash_price_campaigns` | List flash sale / limited-time price campaigns |
| `get_flash_price_campaign_detail` | Detail for a single flash price campaign |
| `list_affiliate_campaigns` | List affiliate marketing campaigns |
| `get_affiliate_campaign_detail` | Detail for a single affiliate campaign |
| `get_affiliate_campaign_usage` | Usage and performance stats for an affiliate campaign |
| `list_gifts` | List gift-with-purchase promotions |
| `list_addon_products` | List add-on product promotions |
| `list_product_subscriptions` | List product subscription plans |
| `get_product_subscription_detail` | Detail for a single subscription plan |

#### Order Extended (8)

| Tool | Description |
|------|-------------|
| `list_return_orders` | List return/refund orders |
| `get_return_order_detail` | Full detail for a single return order |
| `get_order_delivery` | Delivery tracking and logistics info for an order |
| `list_conversations` | List customer service conversations |
| `get_conversation_messages` | Messages within a conversation thread |
| `list_product_reviews` | List product reviews |
| `get_product_review_detail` | Full detail for a single product review |

#### Store Settings (12)

| Tool | Description |
|------|-------------|
| `list_merchants` | List merchant accounts |
| `get_merchant_detail` | Detail for a single merchant |
| `list_payments` | List configured payment methods |
| `list_delivery_options` | List configured delivery options |
| `get_delivery_option_detail` | Detail for a single delivery option |
| `get_delivery_time_slots` | Available delivery time slots |
| `list_channels` | List sales channels (online, POS, etc.) |
| `get_channel_detail` | Detail for a single channel |
| `get_app_settings` | App-level configuration settings |
| `list_taxes` | List tax configurations |
| `get_staff_permissions` | Staff account permission settings |
| `get_token_info` | Info and scope of the current API token |
| `list_agents` | List customer service agent accounts |

---

### Write Tools (68)

Write tools are marked with `[WRITE]` in their descriptions. They require appropriate token permissions and `SHOPLINE_TEST_WRITES=1` to run in tests.

| Domain | Tools |
|--------|-------|
| Order Operations | 8 tools — update status, add notes, assign labels/tags, cancel, fulfill |
| Customer Operations | 6 tools — create/update customer, adjust store credits, update group membership |
| Product Operations | 15 tools — create/update/delete products, manage variants, update stock |
| Promotion/Coupon/Campaign Operations | 12 tools — create/update/delete promotions, coupons, flash sales, affiliate campaigns |
| Category Operations | 3 tools — create, update, delete categories |
| Return Order Operations | 2 tools — approve/reject return orders |
| Conversation Operations | 2 tools — reply to conversations, update conversation status |
| Review Operations | 6 tools — reply to reviews, approve/reject/hide reviews |
| Gift/Addon Operations | 7 tools — create/update/delete gift and add-on promotions |
| Purchase Order Operations | 2 tools — create and receive purchase orders |
| Media/Metafield Operations | 2 tools — upload media, set metafields |
| Delivery/Merchant Operations | 3 tools — update delivery info, manage merchant settings |

---

## API Endpoint Coverage

Based on [Shopline Open API v1](https://open-api.docs.shoplineapp.com):

| Endpoint | Status | Notes |
|----------|--------|-------|
| [Orders](https://open-api.docs.shoplineapp.com/docs/order) | 200 | Full access (read + write) |
| [Products](https://open-api.docs.shoplineapp.com/docs/product) | 200 | Full access (read + write) |
| [Warehouses](https://open-api.docs.shoplineapp.com/docs/warehouse) | 200 | Full access |
| [Categories](https://open-api.docs.shoplineapp.com/docs/category) | 200 | Full access (read + write) |
| [Return Orders](https://open-api.docs.shoplineapp.com/docs/return-order) | 200 | Full access (read + write) |
| [Promotions](https://open-api.docs.shoplineapp.com/docs/promotion) | 200 | Full access (read + write) |
| [Product Stocks](https://open-api.docs.shoplineapp.com/docs/product-stock) | 200 | Per-warehouse breakdown |
| [Customers](https://open-api.docs.shoplineapp.com/docs/customer) | 200 | Full access (read + write) |
| Channels | 200 | Full access |
| Conversations | 200 | Customer service threads (read + write) |
| Reviews | 200 | Product reviews (read + write) |
| Subscriptions | 200 | Product subscription plans |
| Affiliate Campaigns | 200 | Affiliate marketing (read + write) |
| Flash Price Campaigns | 200 | Flash sales (read + write) |
| Purchase Orders | 200 | Replenishment orders (read + write) |
| Gifts & Add-ons | 200 | Gift-with-purchase promotions (read + write) |
| Store Settings | 200 | Payments, delivery, taxes, staff permissions |

> **Note:** Endpoint availability depends on your Shopline API token permissions. The status above reflects full-permission access. Restrict your token to only the scopes you need.

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
│   ├── order_tools.py         # Order read tools (12)
│   ├── product_tools.py       # Product/inventory read tools (9)
│   ├── analytics_tools.py     # Analytics read tools (11)
│   ├── customer_tools.py      # Customer read tools (9)
│   ├── category_tools.py      # Category & promotion read tools (14)
│   ├── extended_tools.py      # Order extended read tools (8)
│   ├── settings_tools.py      # Store settings read tools (12)
│   ├── writes/
│   │   ├── order_writes.py    # Order write tools (8)
│   │   ├── customer_writes.py # Customer write tools (6)
│   │   ├── product_writes.py  # Product write tools (15)
│   │   ├── promotion_writes.py # Promotion/coupon write tools (12)
│   │   ├── category_writes.py # Category write tools (3)
│   │   ├── return_writes.py   # Return order write tools (2)
│   │   ├── conversation_writes.py # Conversation write tools (2)
│   │   ├── review_writes.py   # Review write tools (6)
│   │   ├── gift_writes.py     # Gift/addon write tools (7)
│   │   ├── purchase_writes.py # Purchase order write tools (2)
│   │   ├── media_writes.py    # Media/metafield write tools (2)
│   │   └── delivery_writes.py # Delivery/merchant write tools (3)
│   └── tool_registry.py       # Unified tool registry
├── tests/
│   └── test_all_tools.py      # E2E tests for all 143 tools
└── scripts/
    ├── auth/
    │   ├── test_connection.py     # API connection validator
    │   └── inspect_data_structure.py  # API response structure explorer
    └── audit/
        └── scope_check.py     # Token scope and permission auditor
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
# Read tools (no side effects)
python tests/test_all_tools.py

# Include write tools (creates/updates/deletes data)
SHOPLINE_TEST_WRITES=1 python tests/test_all_tools.py

python scripts/auth/test_connection.py
```

### Adding a New Tool

1. Define a schema dict (Claude API `tool_use` format with `name`, `description`, `input_schema`)
2. Implement the function using `api_get` / `fetch_all_pages` from `base_tool.py`
3. Append `{"schema": ..., "function": ...}` to the module's tool list
4. Auto-registered via `tool_registry.py` and `mcp_server.py` — no extra wiring needed

---

## Roadmap

- [x] `get_refund_by_store` — return order breakdown by store/channel
- [x] `get_stock_transfer_suggestions` — auto-generate inter-warehouse transfer recommendations based on sales velocity and stock levels
- [x] `get_category_tree` — standalone category structure viewer
- [x] `get_promotion_roi` — cross-reference promotion periods with sales trend data to calculate lift and ROI
- [x] `get_customer_lifecycle` — compare RFM segments across two periods to track customer migration (upgrade/churn)
- [x] `get_slow_movers` — identify products with high inventory but low sales for clearance planning
- [x] Customers API tools (member profiles, demographics, membership tiers)
- [ ] Support for multiple Shopline stores (multi-token)
- [ ] Add webhook support for real-time order notifications

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

When adding new tools, follow the existing pattern in `tools/` and ensure the tool passes the E2E test suite.

## License

MIT
