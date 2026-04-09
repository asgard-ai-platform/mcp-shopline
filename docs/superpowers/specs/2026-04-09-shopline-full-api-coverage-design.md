# Shopline MCP Server — Full API Coverage Design Spec

> **Date**: 2026-04-09
> **Version target**: 0.3.0
> **Scope**: Complete Shopline Open API v1 coverage (Read + Write), excluding Webhooks, Multi-token, and Live Streaming.

---

## 1. Goal

Extend the existing 19-tool MCP server to cover **all 129 endpoints** across **32 resource sections** of the Shopline Open API. The result should be ~55–65 tools (read analytics + 1:1 writes) with a verifiable coverage guarantee via an endpoint-to-tool mapping.

### Out of Scope

- Multi-Shopline-store support (multi-token)
- Webhook subscriptions / real-time notifications
- Live Streaming endpoints
- Environment-variable-based write-tool gate (Shopline API token scope is the security boundary; README documents this)

---

## 2. Approach: Layered Coverage

### Read Tools — Analytics-grade Aggregation

Read tools are NOT 1:1 endpoint wrappers. They answer **business questions** by aggregating related GET endpoints into a single tool call. When a resource section has multiple related GETs, prefer merging into one tool that tells the "full story."

**Example**: `get_customer_profile(customer_id)` calls 5 endpoints internally:
- `GET /v1/customers/{id}`
- `GET /v1/customers/{id}/store-credit-history`
- `GET /v1/customers/{id}/member-points`
- `GET /v1/customers/{id}/membership-tier-history`
- `GET /v1/customers/{id}/promotions`

**Exception**: Split into separate tools when return data shapes differ vastly, payload is too large, or call cost is too high (e.g., `get_customer_store_credit_history` as standalone for paginated history).

### Write Tools — Near 1:1 Action Mapping

Write tools map almost 1:1 to endpoints. Each write has unique semantics; aggregating writes creates confusing parameter matrices and makes failure attribution ambiguous.

**Exception**: Multiple endpoints updating different fields of the same concept may merge. E.g., `update_order_status(order_id, status=None, delivery_status=None, payment_status=None)` internally dispatches to 1–3 PATCH endpoints.

---

## 3. Docstring Specification (Mandatory)

All tool docstrings use Traditional Chinese (zh-Hant). This is a **hard requirement**.

### Read Tool Docstring

```
第一行：工具商業用途一句話描述。

【用途】
詳細說明何時使用此工具、適合回答什麼問題、與其他工具的區別。

【呼叫的 Shopline API】
- GET /v1/path
- GET /v1/path/{id}/sub

【回傳結構】
dict 結構說明，含頂層 key、金額單位、分頁行為等。
```

### Write Tool Docstring

```
[WRITE] 動作描述一句話。

【用途】
何時使用、適用場景。

【呼叫的 Shopline API】
- POST /v1/path

【回傳結構】
dict 至少含 success: bool, resource_id: str, message: str。

【副作用】
- 列出所有狀態變更
- 是否可復原
- 連帶影響（例如不自動退款）
```

**Hard rules:**
1. Write tools: docstring line 1 MUST start with `[WRITE]`
2. Write tools MUST include `【副作用】` section
3. ALL tools MUST list called endpoints in `【呼叫的 Shopline API】` (used by coverage audit script)
4. Read tools need no `[READ]` prefix — absence of `[WRITE]` implies read

---

## 4. File Structure

### Read Tool Modules

Existing files are **modified** (new tools added); new domains get **one file per Shopline resource section**.

```
tools/
├── base_tool.py                      # Shared HTTP client (modified: add write methods)
│
│  # === Existing (modified — new tools added) ===
├── order_tools.py                    # Existing 7 + new: archived_orders, order_labels, order_tags, order_action_logs, order_transactions
├── product_tools.py                  # Existing 6 + new: locked_inventory, purchase_order reads
├── analytics_tools.py                # Existing 6 + new: get_refund_by_store, get_stock_transfer_suggestions, get_promotion_roi, get_customer_lifecycle, get_slow_movers
│
│  # === New — Customer domain (one per resource section) ===
├── customer_tools.py                 # Customer: list / search / profile
├── customer_group_tools.py           # Customer Group: list / search / members
├── store_credit_tools.py             # Store Credits: list / history
├── membership_tier_tools.py          # Membership Tiers: list / tier history
├── member_point_tools.py             # Member Point Rules: list
├── custom_field_tools.py             # Custom Fields: list
│
│  # === New — Product/Promotion domain ===
├── category_tools.py                 # Category: tree / list / detail
├── promotion_tools.py                # Promotion: search / detail (distinct from analytics get_promotion_analysis)
├── flash_price_tools.py              # Flash Price Campaign: list / detail
├── affiliate_tools.py                # Affiliate Campaign: list / detail / order_usage
├── gift_tools.py                     # Gifts: list / search
├── addon_product_tools.py            # Addon Products: list / search
├── subscription_tools.py             # Product Subscription: list / detail
│
│  # === New — Order extended domain ===
├── return_order_tools.py             # Return Order: list / detail (existing get_refund_summary stays in order_tools.py)
├── order_delivery_tools.py           # Order Delivery: get
├── conversation_tools.py             # Conversation: list / messages
├── review_tools.py                   # Product Review Comments: list / detail
│
│  # === New — Store settings domain ===
├── merchant_tools.py                 # Merchant: list / detail
├── payment_tools.py                  # Payment: list
├── delivery_option_tools.py          # Delivery Options: list / detail / time_slots
├── channel_tools.py                  # Channel: list / detail
├── settings_tools.py                 # Settings: app (deprecated but covered)
├── tax_tools.py                      # Tax: list
├── staff_tools.py                    # Staff: permissions
├── token_tools.py                    # Token: info
├── agent_tools.py                    # Agents: list
│
│  # === Write tools ===
└── writes/
    ├── __init__.py
    ├── order_writes.py               # cancel / shipment / bulk_shipment / split / update / status / delivery_status / payment_status / tags
    ├── customer_writes.py            # create / update / delete / tags / store_credits / member_points
    ├── product_writes.py             # create / update / delete / price / quantity / variations / images / tags / bulk_quantities / bulk_categories
    ├── category_writes.py            # create / update / delete
    ├── promotion_writes.py           # promotion CRUD + coupons send/redeem/claim + flash price CRUD + affiliate CRUD
    ├── return_order_writes.py        # create / update
    ├── conversation_writes.py        # order_message / shop_message
    ├── gift_writes.py                # create / update / quantity_by_sku + addon_product create / update / quantity
    ├── review_writes.py              # create / bulk_create / update / bulk_update / delete / bulk_delete
    ├── purchase_order_writes.py      # create / delete
    ├── media_writes.py               # upload media + create metafield
    ├── order_delivery_writes.py      # update order delivery
    ├── delivery_option_writes.py     # update pickup store
    └── merchant_writes.py            # update merchant
```

### `mcp_server.py` — Explicit imports

All modules are explicitly imported in `mcp_server.py` (reads and writes alike). The Shopline API token scope is the security boundary, not conditional imports.

---

## 5. Infrastructure Changes

### 5.1 `config/settings.py`

Expand `ENDPOINTS` dict from ~8 to ~60+ path templates covering all 129 endpoints. Organized by domain with section comments.

Naming convention: `{resource}_{action}` or `{resource}_{sub_resource}`.

Examples:
```python
"order_cancel": f"/{API_VERSION}/orders/{{order_id}}/cancel",
"customer_store_credit_history": f"/{API_VERSION}/customers/{{customer_id}}/store-credit-history",
"flash_price_campaigns": f"/{API_VERSION}/flash_price_campaigns",
```

### 5.2 `base_tool.py`

**New internal function:**
```python
def _api_request(method, endpoint_key, json_body=None, params=None,
                 path_params=None, retries=3, retry_on_client_error=True):
```

**New public functions:**
```python
def api_post(endpoint_key, json_body=None, params=None, path_params=None, retries=3)
def api_put(endpoint_key, json_body=None, params=None, path_params=None, retries=3)
def api_patch(endpoint_key, json_body=None, params=None, path_params=None, retries=3)
def api_delete(endpoint_key, params=None, path_params=None, retries=3)
```

**Retry strategy:**
- `api_get`: retry on timeout, connection error, AND 5xx (existing behavior preserved)
- `api_post/put/patch/delete`: retry on timeout, connection error, 5xx only. **4xx = immediate ShoplineAPIError, no retry** (prevents duplicate writes)

**Unchanged:**
- `fetch_all_pages()` — pagination, GET only
- `fetch_all_pages_by_date_segments()` — date-segmented pagination, GET only
- `money_to_float()` — currency conversion
- `get_translation()` — i18n text extraction

---

## 6. Parameter & Return Conventions (Continuing Existing)

### Parameters
- Dates: `start_date` / `end_date` as `YYYY-MM-DD`
- Pagination: `max_results` (not page+per_page); internal `fetch_all_pages` handles
- Channel: `channel: Literal["online", "pos", "all"]`
- Language: `lang: Literal["zh-hant", "en"]`, default `"zh-hant"`
- Optional params: `Optional[T] = Field(default=None, description="...")`

### Return Values — Read
- Always `dict`
- Top-level metadata: `period`, `total_found`, or resource-appropriate context
- Monetary values via `money_to_float()` → `float` (TWD)
- Translated fields via `get_translation()`

### Return Values — Write
- Always `dict`
- Minimum keys: `success: bool`, `resource_id: str`, `message: str`
- On failure: `ShoplineAPIError` is raised (not caught by tool)

---

## 7. Testing Strategy

### File Structure
```
tests/
├── test_order_tools.py
├── test_product_tools.py
├── test_analytics_tools.py
├── test_customer_tools.py
├── test_customer_group_tools.py
├── test_store_credit_tools.py
├── test_membership_tier_tools.py
├── test_member_point_tools.py
├── test_custom_field_tools.py
├── test_category_tools.py
├── test_promotion_tools.py
├── test_conversation_tools.py
├── test_settings_tools.py
├── test_subscription_tools.py
├── test_review_tools.py
├── test_token_tools.py
├── test_gift_tools.py
├── test_addon_product_tools.py
├── test_flash_price_tools.py
├── test_affiliate_tools.py
├── test_agent_tools.py
├── test_order_delivery_tools.py
├── test_return_order_tools.py
├── test_merchant_tools.py
├── test_payment_tools.py
├── test_delivery_option_tools.py
├── test_channel_tools.py
├── test_tax_tools.py
├── test_staff_tools.py
├── test_purchase_order_tools.py
│
├── test_writes/
│   ├── test_order_writes.py
│   ├── test_customer_writes.py
│   ├── test_product_writes.py
│   ├── ... (mirrors tools/writes/)
│   └── run_write_tests.py           # SHOPLINE_TEST_WRITES=1 gate
│
├── test_all_tools.py                # Aggregator: runs all read tests
└── test_coverage.py                 # Runs scripts/audit/check_coverage.py
```

### Read Tests
- Standalone scripts, live API, no mocks (continuing existing pattern)
- Import tool function directly, call with known test data, assert response shape
- `test_all_tools.py` = aggregator that imports and runs all read test modules

### Write Tests
- Default **SKIP** unless `SHOPLINE_TEST_WRITES=1`
- Pattern: create → verify (via read tool/API) → cleanup (if API supports)
- Destructive writes (cancel, delete): require pre-existing test data, documented in README

### Coverage Test
- `scripts/audit/check_coverage.py`: parse all `@mcp.tool()` docstrings → extract `【呼叫的 Shopline API】` endpoints → diff against `reference/shopline-api-inventory.md`
- Exit 1 if any endpoint is uncovered

---

## 8. Documentation Updates

| File | Changes |
|------|---------|
| `CLAUDE.md` | Fix stale tool_registry.py references; update architecture diagram; add writes layer; update tool count; add coverage script section |
| `README.md` | Add "Write Tools" warning section; expand Tools table (read/write separated); update API Endpoint Coverage; update Project Structure; check Roadmap items |
| `README.zh-TW.md` | Sync with README.md |
| `CONTRIBUTING.md` | Add docstring spec (4-section / 5-section format); document writes/ directory; update test instructions |
| `CHANGELOG.md` | Add v0.3.0 entry |
| `pyproject.toml` | version = "0.3.0" |
| `app.py` | version = "0.3.0" |

---

## 9. Implementation Phases

### Phase 0 — Infrastructure
- `base_tool.py`: refactor to `_api_request()` + add `api_post`/`api_put`/`api_patch`/`api_delete`
- `config/settings.py`: expand ENDPOINTS to all 129 paths

### Phase 1 — Customer Domain (verify API access first)
1. `customer_tools.py` — list / search / profile
2. `customer_group_tools.py`
3. `store_credit_tools.py`
4. `membership_tier_tools.py`
5. `member_point_tools.py`
6. `custom_field_tools.py`
7. Corresponding 6 test files
8. `writes/customer_writes.py` + test

**Gate**: If Customer API still returns 403, report to user immediately before proceeding.

### Phase 2 — Expand Existing Files
- `order_tools.py` += archived / labels / tags / action-logs / transactions
- `product_tools.py` += locked-inventory / purchase order reads
- `analytics_tools.py` += get_refund_by_store / get_stock_transfer_suggestions / get_promotion_roi / get_customer_lifecycle / get_slow_movers
- Update existing 3 test files

### Phase 3 — New Domain Read Modules

**Batch A (Product/Promotion domain):**
category, promotion, flash_price, affiliate, gift, addon_product, subscription

**Batch B (Order extended domain):**
return_order, order_delivery, conversation, review

**Batch C (Store settings domain):**
merchant, payment, delivery_option, channel, settings, tax, staff, token, agent

Batches A / B / C are independent and can run in parallel.

### Phase 4 — All Write Tools
All 14 write modules in `tools/writes/` + corresponding `test_writes/` tests.
Depends on read tools being complete (write tests verify via reads).

### Phase 5 — Finalization
- `scripts/audit/check_coverage.py`
- `test_all_tools.py` aggregator rewrite
- `test_coverage.py`
- All documentation updates (CLAUDE.md, README.md, README.zh-TW.md, CONTRIBUTING.md, CHANGELOG.md)
- Version bump to 0.3.0

### Dependency Graph
```
Phase 0 (infra)
  ├─→ Phase 1 (customer — run FIRST to verify API access)
  │     then:
  ├─→ Phase 2 (expand existing files)
  ├─→ Phase 3A (product/promotion reads)  ─┐
  ├─→ Phase 3B (order extended reads)     ─┼─→ Phase 4 (all writes)
  └─→ Phase 3C (store settings reads)    ─┘         │
                                                      └─→ Phase 5 (finalization)
```

---

## 10. Coverage Matrix

The complete endpoint-to-tool mapping will be maintained as a separate appendix file (`reference/coverage-matrix.md`) generated and verified by `scripts/audit/check_coverage.py`. It will be populated during implementation and verified at Phase 5.

**Contract**: Every one of the 129 endpoints listed in `reference/shopline-api-inventory.md` MUST map to at least one tool. The check_coverage.py script enforces this at CI/review time.
