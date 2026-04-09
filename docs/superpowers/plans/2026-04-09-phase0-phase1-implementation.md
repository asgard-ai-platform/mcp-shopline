# Phase 0 + Phase 1: Infrastructure & Customer Domain Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the MCP server infrastructure to support write operations, expand endpoint coverage to all 129 Shopline API paths, and implement the complete Customer domain (6 read modules + 1 write module) — verifying Customer API access along the way.

**Architecture:** Refactor `base_tool.py` to extract a shared `_api_request()` internal function that handles GET/POST/PUT/PATCH/DELETE with differentiated retry strategies. Expand `config/settings.py` with all Shopline API endpoint paths. Add Customer domain tools following existing `@mcp.tool()` decorator pattern with Traditional Chinese docstrings.

**Tech Stack:** Python 3.10+, MCP Python SDK, requests, pydantic

**Spec:** `docs/superpowers/specs/2026-04-09-shopline-full-api-coverage-design.md`
**Endpoint inventory:** `reference/shopline-api-inventory.md`

---

## File Map

### Phase 0 — Infrastructure
| Action | File | Purpose |
|--------|------|---------|
| Modify | `tools/base_tool.py` | Add `_api_request`, `api_post`, `api_put`, `api_patch`, `api_delete` |
| Modify | `config/settings.py` | Expand ENDPOINTS from ~14 to ~70 path templates |

### Phase 1 — Customer Domain
| Action | File | Purpose |
|--------|------|---------|
| Create | `tools/customer_tools.py` | `list_customers`, `get_customer_profile` |
| Create | `tools/customer_group_tools.py` | `list_customer_groups`, `get_customer_group_members` |
| Create | `tools/store_credit_tools.py` | `list_store_credits` |
| Create | `tools/membership_tier_tools.py` | `list_membership_tiers`, `get_customer_tier_history` |
| Create | `tools/member_point_tools.py` | `list_member_point_rules` |
| Create | `tools/custom_field_tools.py` | `list_custom_fields` |
| Modify | `mcp_server.py` | Import all new modules |
| Create | `tools/writes/__init__.py` | Package init |
| Create | `tools/writes/customer_writes.py` | `create_customer`, `update_customer`, `delete_customer`, `update_customer_tags`, `update_customer_store_credits`, `adjust_customer_member_points` |
| Create | `tests/test_customer_tools.py` | Tests for customer read tools |
| Create | `tests/test_customer_group_tools.py` | Tests for customer group tools |
| Create | `tests/test_store_credit_tools.py` | Tests for store credit tools |
| Create | `tests/test_membership_tier_tools.py` | Tests for membership tier tools |
| Create | `tests/test_member_point_tools.py` | Tests for member point rules tools |
| Create | `tests/test_custom_field_tools.py` | Tests for custom field tools |
| Create | `tests/test_writes/test_customer_writes.py` | Tests for customer write tools (gated) |

---

## Task 1: Refactor `base_tool.py` — Add Write HTTP Methods

**Files:**
- Modify: `tools/base_tool.py`

- [ ] **Step 1: Write the updated `base_tool.py`**

Replace the entire `api_get` function and add new functions. The existing `api_get` signature and behavior MUST remain identical so the 19 existing tools are unaffected.

```python
"""
Shopline API 基底工具 — 認證、分頁、錯誤處理共用邏輯
"""
import requests
import time
from config.settings import get_headers, get_url, DEFAULT_PER_PAGE


class ShoplineAPIError(Exception):
    def __init__(self, status_code, message, endpoint=""):
        self.status_code = status_code
        self.message = message
        self.endpoint = endpoint
        super().__init__(f"[{status_code}] {endpoint}: {message}")


def _api_request(method, endpoint_key, json_body=None, params=None,
                 path_params=None, retries=3, retry_on_client_error=True):
    """
    內部共用 HTTP 請求函數。不直接由 tool 呼叫。

    retry_on_client_error:
      - True (GET): 任何非 200 都重試（保持既有行為）
      - False (POST/PUT/PATCH/DELETE): 4xx 直接拋錯不重試，僅 5xx/網路層重試
    """
    path_params = path_params or {}
    url = get_url(endpoint_key, **path_params)
    headers = get_headers()

    for attempt in range(retries):
        try:
            resp = requests.request(
                method, url, headers=headers, params=params,
                json=json_body, timeout=60
            )
            if resp.status_code in (200, 201):
                return resp.json()
            if resp.status_code == 204:
                return {}  # No Content（常見於 DELETE 回應）

            is_client_error = 400 <= resp.status_code < 500
            is_server_error = resp.status_code >= 500

            if is_client_error and not retry_on_client_error:
                raise ShoplineAPIError(resp.status_code, resp.text[:500], url)

            if is_server_error or (is_client_error and retry_on_client_error):
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise ShoplineAPIError(resp.status_code, resp.text[:500], url)

            # 其他非預期狀態碼
            raise ShoplineAPIError(resp.status_code, resp.text[:500], url)

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise


def api_get(endpoint_key, params=None, path_params=None, retries=3):
    """發送 GET 請求到 Shopline API，回傳 JSON。含自動重試。"""
    return _api_request("GET", endpoint_key, params=params,
                        path_params=path_params, retries=retries,
                        retry_on_client_error=True)


def api_post(endpoint_key, json_body=None, params=None, path_params=None, retries=3):
    """發送 POST 請求到 Shopline API。4xx 不重試。"""
    return _api_request("POST", endpoint_key, json_body=json_body,
                        params=params, path_params=path_params, retries=retries,
                        retry_on_client_error=False)


def api_put(endpoint_key, json_body=None, params=None, path_params=None, retries=3):
    """發送 PUT 請求到 Shopline API。4xx 不重試。"""
    return _api_request("PUT", endpoint_key, json_body=json_body,
                        params=params, path_params=path_params, retries=retries,
                        retry_on_client_error=False)


def api_patch(endpoint_key, json_body=None, params=None, path_params=None, retries=3):
    """發送 PATCH 請求到 Shopline API。4xx 不重試。"""
    return _api_request("PATCH", endpoint_key, json_body=json_body,
                        params=params, path_params=path_params, retries=retries,
                        retry_on_client_error=False)


def api_delete(endpoint_key, params=None, path_params=None, retries=3):
    """發送 DELETE 請求到 Shopline API。4xx 不重試。"""
    return _api_request("DELETE", endpoint_key, params=params,
                        path_params=path_params, retries=retries,
                        retry_on_client_error=False)


def fetch_all_pages(endpoint_key, params=None, path_params=None, max_pages=None):
    """自動分頁遍歷，回傳所有 items"""
    params = dict(params or {})
    params.setdefault("per_page", DEFAULT_PER_PAGE)
    # orders_search 不支援 sort_by 參數
    if "search" not in endpoint_key:
        params.setdefault("sort_by", "desc")

    all_items = []
    page = 1

    while True:
        if max_pages and page > max_pages:
            break

        params["page"] = page
        data = api_get(endpoint_key, params=params, path_params=path_params)

        items = data.get("items", [])
        all_items.extend(items)

        pagination = data.get("pagination", {})
        total_pages = pagination.get("total_pages", 1)

        if page >= total_pages:
            break

        page += 1
        time.sleep(0.2)  # Rate limit 保護

    return all_items


def fetch_all_pages_by_date_segments(endpoint_key, start_date, end_date, params=None):
    """
    對於超過 10,000 筆的查詢，用日期分段拉取。
    start_date / end_date 格式: "YYYY-MM-DDTHH:MM:SSZ"
    """
    from datetime import datetime, timedelta

    params = dict(params or {})
    all_items = []

    start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
    end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
    segment_days = 30

    current = start
    while current < end:
        seg_end = min(current + timedelta(days=segment_days), end)
        params["created_after"] = current.strftime("%Y-%m-%dT%H:%M:%SZ")
        params["created_before"] = seg_end.strftime("%Y-%m-%dT%H:%M:%SZ")

        items = fetch_all_pages(endpoint_key, params=params)
        all_items.extend(items)

        current = seg_end

    return all_items


def money_to_float(money_obj):
    """將 Shopline 金額物件轉為 float，例如 {"cents": 2720, "dollars": 2720.0} → 2720.0"""
    if not money_obj:
        return 0.0
    return float(money_obj.get("dollars", 0) or 0)


def get_translation(obj, lang="zh-hant", fallback="en"):
    """取得翻譯文字"""
    if not obj:
        return ""
    if isinstance(obj, str):
        return obj
    return obj.get(lang, obj.get(fallback, ""))
```

- [ ] **Step 2: Run existing tests to verify no regression**

Run: `python tests/test_all_tools.py`
Expected: All 19 existing tools still pass. The refactored `api_get` uses `_api_request` internally but maintains identical behavior.

- [ ] **Step 3: Commit**

```bash
git add tools/base_tool.py
git commit -m "refactor: extract _api_request and add api_post/put/patch/delete to base_tool.py"
```

---

## Task 2: Expand `config/settings.py` — All Endpoint Paths

**Files:**
- Modify: `config/settings.py`

- [ ] **Step 1: Replace ENDPOINTS dict with full coverage**

```python
"""Shopline API 設定"""
import os

BASE_URL = "https://open.shopline.io"
API_VERSION = "v1"
ACCESS_TOKEN = os.environ.get("SHOPLINE_API_TOKEN", "")

# 預設分頁設定
DEFAULT_PER_PAGE = 50  # API 建議上限
DEFAULT_SORT = "desc"

# API 端點 — 完整 Shopline Open API v1 覆蓋
# 命名規則: {resource}_{action} 或 {resource}_{sub_resource}
ENDPOINTS = {
    # === Orders ===
    "orders": f"/{API_VERSION}/orders",
    "orders_search": f"/{API_VERSION}/orders/search",
    "order_detail": f"/{API_VERSION}/orders/{{order_id}}",
    "order_labels": f"/{API_VERSION}/orders/{{order_id}}/labels",
    "order_tags": f"/{API_VERSION}/orders/{{order_id}}/tags",
    "order_action_logs": f"/{API_VERSION}/orders/{{order_id}}/action-logs",
    "order_transactions": f"/{API_VERSION}/orders/{{order_id}}/transactions",
    "orders_archived": f"/{API_VERSION}/orders/archived",
    "order_create": f"/{API_VERSION}/orders",
    "order_update": f"/{API_VERSION}/orders/{{order_id}}",
    "order_shipment": f"/{API_VERSION}/orders/{{order_id}}/shipment",
    "orders_shipment_bulk": f"/{API_VERSION}/orders/shipment/bulk",
    "order_split": f"/{API_VERSION}/orders/{{order_id}}/split",
    "order_cancel": f"/{API_VERSION}/orders/{{order_id}}/cancel",
    "order_status": f"/{API_VERSION}/orders/{{order_id}}/status",
    "order_delivery_status": f"/{API_VERSION}/orders/{{order_id}}/delivery-status",
    "order_payment_status": f"/{API_VERSION}/orders/{{order_id}}/payment-status",
    "order_tags_update": f"/{API_VERSION}/orders/{{order_id}}/tags",

    # === Customers ===
    "customers": f"/{API_VERSION}/customers",
    "customers_search": f"/{API_VERSION}/customers/search",
    "customer_detail": f"/{API_VERSION}/customers/{{customer_id}}",
    "customer_store_credit_history": f"/{API_VERSION}/customers/{{customer_id}}/store-credit-history",
    "customer_member_points": f"/{API_VERSION}/customers/{{customer_id}}/member-points",
    "customer_promotions": f"/{API_VERSION}/customers/{{customer_id}}/promotions",
    "customer_create": f"/{API_VERSION}/customers",
    "customer_update": f"/{API_VERSION}/customers/{{customer_id}}",
    "customer_delete": f"/{API_VERSION}/customers/{{customer_id}}",
    "customer_tags": f"/{API_VERSION}/customers/{{customer_id}}/tags",
    "customer_store_credits_update": f"/{API_VERSION}/customers/{{customer_id}}/store-credits",
    "customer_member_points_update": f"/{API_VERSION}/customers/{{customer_id}}/member-points",

    # === Customer Groups ===
    "customer_groups": f"/{API_VERSION}/customer-groups",
    "customer_groups_search": f"/{API_VERSION}/customer-groups/search",
    "customer_group_customers": f"/{API_VERSION}/customer-groups/{{group_id}}/customers",

    # === Store Credits ===
    "user_credits": f"/{API_VERSION}/user_credits",

    # === Custom Fields ===
    "custom_fields": f"/{API_VERSION}/custom_fields",

    # === Membership Tiers ===
    "membership_tiers": f"/{API_VERSION}/membership_tiers",
    "customer_membership_tier_history": f"/{API_VERSION}/customers/{{customer_id}}/membership-tier-history",

    # === Member Point Rules ===
    "member_point_rules": f"/{API_VERSION}/member_point_rules",

    # === Products ===
    "products": f"/{API_VERSION}/products",
    "products_search": f"/{API_VERSION}/products/search",
    "product_detail": f"/{API_VERSION}/products/{{product_id}}",
    "product_stocks": f"/{API_VERSION}/products/{{product_id}}/stocks",
    "products_locked_inventory": f"/{API_VERSION}/products/locked-inventory",
    "product_create": f"/{API_VERSION}/products",
    "product_update": f"/{API_VERSION}/products/{{product_id}}",
    "product_delete": f"/{API_VERSION}/products/{{product_id}}",
    "product_images": f"/{API_VERSION}/products/{{product_id}}/images",
    "product_variations_create": f"/{API_VERSION}/products/{{product_id}}/variations",
    "product_variation_update": f"/{API_VERSION}/products/{{product_id}}/variations/{{variation_id}}",
    "product_variation_delete": f"/{API_VERSION}/products/{{product_id}}/variations/{{variation_id}}",
    "product_variation_quantity": f"/{API_VERSION}/products/{{product_id}}/variations/{{variation_id}}/quantity",
    "product_variation_price": f"/{API_VERSION}/products/{{product_id}}/variations/{{variation_id}}/price",
    "product_quantity": f"/{API_VERSION}/products/{{product_id}}/quantity",
    "product_price": f"/{API_VERSION}/products/{{product_id}}/price",
    "product_tags": f"/{API_VERSION}/products/{{product_id}}/tags",
    "products_bulk_quantities": f"/{API_VERSION}/products/bulk-update-quantities",
    "products_bulk_categories": f"/{API_VERSION}/products/bulk-assign-categories",

    # === Categories ===
    "categories": f"/{API_VERSION}/categories",
    "category_detail": f"/{API_VERSION}/categories/{{category_id}}",
    "category_create": f"/{API_VERSION}/categories",
    "category_update": f"/{API_VERSION}/categories/{{category_id}}",
    "category_delete": f"/{API_VERSION}/categories/{{category_id}}",

    # === Promotions ===
    "promotions": f"/{API_VERSION}/promotions",
    "promotion_detail": f"/{API_VERSION}/promotions/{{promotion_id}}",
    "promotions_search": f"/{API_VERSION}/promotions/search",
    "promotion_create": f"/{API_VERSION}/promotions",
    "promotion_update": f"/{API_VERSION}/promotions/{{promotion_id}}",
    "promotion_delete": f"/{API_VERSION}/promotions/{{promotion_id}}",
    "coupon_send": f"/{API_VERSION}/coupons/send",
    "coupon_redeem": f"/{API_VERSION}/coupons/redeem",
    "coupon_claim": f"/{API_VERSION}/coupons/claim",

    # === Warehouses ===
    "warehouses": f"/{API_VERSION}/warehouses",

    # === Return Orders ===
    "return_orders": f"/{API_VERSION}/return_orders",
    "return_order_detail": f"/{API_VERSION}/return_orders/{{return_order_id}}",
    "return_order_create": f"/{API_VERSION}/return_orders",
    "return_order_update": f"/{API_VERSION}/return_orders/{{return_order_id}}",

    # === Channels ===
    "channels": f"/{API_VERSION}/channels",
    "channel_detail": f"/{API_VERSION}/channels/{{channel_id}}",

    # === Token ===
    "token_info": f"/{API_VERSION}/token/info",

    # === Conversations ===
    "conversations": f"/{API_VERSION}/conversations",
    "conversation_messages": f"/{API_VERSION}/conversations/{{conversation_id}}/messages",
    "conversation_order_message": f"/{API_VERSION}/conversations/order-messages",
    "conversation_shop_message": f"/{API_VERSION}/conversations/shop-messages",

    # === Gifts ===
    "gifts": f"/{API_VERSION}/gifts",
    "gifts_search": f"/{API_VERSION}/gifts/search",
    "gift_create": f"/{API_VERSION}/gifts",
    "gift_update": f"/{API_VERSION}/gifts/{{gift_id}}",
    "gift_quantity_by_sku": f"/{API_VERSION}/gifts/quantity-by-sku",

    # === Addon Products ===
    "addon_products": f"/{API_VERSION}/addon_products",
    "addon_products_search": f"/{API_VERSION}/addon_products/search",
    "addon_product_create": f"/{API_VERSION}/addon_products",
    "addon_product_update": f"/{API_VERSION}/addon_products/{{addon_product_id}}",
    "addon_product_quantity": f"/{API_VERSION}/addon_products/{{addon_product_id}}/quantity",
    "addon_product_sku_quantity": f"/{API_VERSION}/addon_products/sku/quantity",

    # === Settings ===
    "settings_app": f"/{API_VERSION}/settings/app",

    # === Payment ===
    "payments": f"/{API_VERSION}/payments",

    # === Delivery Options ===
    "delivery_options": f"/{API_VERSION}/delivery_options",
    "delivery_option_detail": f"/{API_VERSION}/delivery_options/{{delivery_option_id}}",
    "delivery_option_time_slots": f"/{API_VERSION}/delivery_options/{{delivery_option_id}}/time_slots",
    "delivery_option_pickup_store": f"/{API_VERSION}/delivery_options/{{delivery_option_id}}/pickup_store",

    # === Merchant ===
    "merchants": f"/{API_VERSION}/merchants",
    "merchant_detail": f"/{API_VERSION}/merchants/{{merchant_id}}",
    "merchant_update": f"/{API_VERSION}/merchants/{{merchant_id}}",

    # === Staff ===
    "staff_permissions": f"/{API_VERSION}/staffs/{{staff_id}}/permissions",

    # === Tax ===
    "taxes": f"/{API_VERSION}/taxes",

    # === Product Review Comments ===
    "product_review_comments": f"/{API_VERSION}/product_review_comments",
    "product_review_comment_detail": f"/{API_VERSION}/product_review_comments/{{comment_id}}",
    "product_review_comment_create": f"/{API_VERSION}/product_review_comments",
    "product_review_comments_bulk_create": f"/{API_VERSION}/product_review_comments/bulk",
    "product_review_comment_update": f"/{API_VERSION}/product_review_comments/{{comment_id}}",
    "product_review_comments_bulk_update": f"/{API_VERSION}/product_review_comments",
    "product_review_comment_delete": f"/{API_VERSION}/product_review_comments/{{comment_id}}",
    "product_review_comments_bulk_delete": f"/{API_VERSION}/product_review_comments",

    # === Agents ===
    "agents": f"/{API_VERSION}/agents",

    # === Product Subscription ===
    "product_subscriptions": f"/{API_VERSION}/product_subscriptions",
    "product_subscription_detail": f"/{API_VERSION}/product_subscriptions/{{subscription_id}}",

    # === Media ===
    "media_create": f"/{API_VERSION}/media",

    # === Order Delivery ===
    "order_delivery_detail": f"/{API_VERSION}/order_deliveries/{{delivery_id}}",
    "order_delivery_update": f"/{API_VERSION}/order_deliveries/{{delivery_id}}",

    # === Flash Price Campaign ===
    "flash_price_campaigns": f"/{API_VERSION}/flash_price_campaigns",
    "flash_price_campaign_detail": f"/{API_VERSION}/flash_price_campaigns/{{campaign_id}}",
    "flash_price_campaign_create": f"/{API_VERSION}/flash_price_campaigns",
    "flash_price_campaign_update": f"/{API_VERSION}/flash_price_campaigns/{{campaign_id}}",
    "flash_price_campaign_delete": f"/{API_VERSION}/flash_price_campaigns/{{campaign_id}}",

    # === Affiliate Campaign ===
    "affiliate_campaigns": f"/{API_VERSION}/affiliate_campaigns",
    "affiliate_campaign_detail": f"/{API_VERSION}/affiliate_campaigns/{{campaign_id}}",
    "affiliate_campaign_order_usage": f"/{API_VERSION}/affiliate_campaigns/{{campaign_id}}/order_usage",
    "affiliate_campaign_create": f"/{API_VERSION}/affiliate_campaigns",
    "affiliate_campaign_update": f"/{API_VERSION}/affiliate_campaigns/{{campaign_id}}",
    "affiliate_campaign_delete": f"/{API_VERSION}/affiliate_campaigns/{{campaign_id}}",

    # === Metafields ===
    "metafield_create": "/merchants/current/app-metafields",

    # === Purchase Orders ===
    "purchase_orders": f"/{API_VERSION}/pos/purchase_orders",
    "purchase_order_detail": f"/{API_VERSION}/pos/purchase_orders/{{purchase_order_id}}",
    "purchase_order_create": f"/{API_VERSION}/pos/purchase_orders",
    "purchase_order_delete": f"/{API_VERSION}/pos/purchase_orders",
}


def get_headers():
    if not ACCESS_TOKEN:
        raise RuntimeError(
            "SHOPLINE_API_TOKEN environment variable is not set. "
            "Run: export SHOPLINE_API_TOKEN=your_token_here"
        )
    return {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }


def get_url(endpoint_key, **kwargs):
    """取得完整 API URL，支援路徑參數替換"""
    path = ENDPOINTS[endpoint_key].format(**kwargs)
    return f"{BASE_URL}{path}"
```

- [ ] **Step 2: Run existing tests to verify no regression**

Run: `python tests/test_all_tools.py`
Expected: All 19 existing tools still pass. Only ENDPOINTS dict was extended; existing keys unchanged.

- [ ] **Step 3: Commit**

```bash
git add config/settings.py
git commit -m "feat: expand ENDPOINTS to cover all 129 Shopline API paths"
```

---

## Task 3: Create `customer_tools.py` — Customer Read Tools

**Files:**
- Create: `tools/customer_tools.py`
- Create: `tests/test_customer_tools.py`

- [ ] **Step 1: Create `tools/customer_tools.py`**

```python
"""
客戶相關 Tools — 客戶列表、搜尋、完整個人檔案
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import Optional
from pydantic import Field

from app import mcp
from tools.base_tool import (
    api_get, fetch_all_pages, money_to_float, get_translation
)


# ============================================================
# Tool 1: list_customers — 客戶列表/搜尋
# ============================================================
@mcp.tool()
def list_customers(
    search_keyword: Optional[str] = Field(default=None, description="搜尋關鍵字（姓名、email、電話）"),
    max_results: int = Field(default=50, description="最多回傳筆數"),
) -> dict:
    """取得客戶列表，支援依關鍵字搜尋客戶。

    【用途】
    查詢特定客戶或瀏覽客戶清單。可用姓名、email、電話搜尋。
    若要取得單一客戶的完整資訊（含儲值金、點數、等級），請改用 get_customer_profile。

    【呼叫的 Shopline API】
    - GET /v1/customers（無搜尋條件時）
    - GET /v1/customers/search（有搜尋條件時）

    【回傳結構】
    dict 含 total_found, returned, customers[]。
    每個 customer 包含 id, name, email, phone, tags, created_at。
    """
    if search_keyword:
        params = {"keyword": search_keyword, "per_page": min(max_results, 50)}
        data = api_get("customers_search", params=params)
        customers = data.get("items", [])
    else:
        customers = fetch_all_pages("customers", max_pages=max(1, max_results // 50))

    results = []
    for c in customers[:max_results]:
        results.append({
            "id": c.get("id"),
            "name": c.get("name"),
            "email": c.get("email"),
            "phone": c.get("phone"),
            "gender": c.get("gender"),
            "birthday": c.get("birthday"),
            "tags": c.get("tags", []),
            "membership_tier": c.get("membership_tier_id"),
            "total_spent": money_to_float(c.get("total_spent")),
            "orders_count": c.get("orders_count", 0),
            "created_at": c.get("created_at"),
        })

    return {
        "total_found": len(customers),
        "returned": len(results),
        "customers": results,
    }


# ============================================================
# Tool 2: get_customer_profile — 客戶完整輪廓
# ============================================================
@mcp.tool()
def get_customer_profile(
    customer_id: str = Field(description="客戶內部 ID（由 list_customers 回傳的 id 欄位）"),
) -> dict:
    """取得單一客戶的完整輪廓（基本資料 + 儲值金紀錄 + 會員點數 + 會員等級變動 + 優惠券）。

    【用途】
    回答「這位客戶是誰、消費狀況、會員狀態」等完整客戶概況問題。適合客服
    場景或個別會員分析。若要批次分析客戶行為請改用 get_rfm_analysis。

    【呼叫的 Shopline API】
    - GET /v1/customers/{customer_id}
    - GET /v1/customers/{customer_id}/store-credit-history
    - GET /v1/customers/{customer_id}/member-points
    - GET /v1/customers/{customer_id}/membership-tier-history
    - GET /v1/customers/{customer_id}/promotions

    【回傳結構】
    dict 包含 profile / store_credits / member_points / tier_history / promotions 五大區塊。
    金額皆為 float (TWD)。
    """
    path_params = {"customer_id": customer_id}

    # 基本資料
    detail = api_get("customer_detail", path_params=path_params)
    c = detail if "name" in detail else detail.get("item", detail)

    profile = {
        "id": c.get("id"),
        "name": c.get("name"),
        "email": c.get("email"),
        "phone": c.get("phone"),
        "gender": c.get("gender"),
        "birthday": c.get("birthday"),
        "tags": c.get("tags", []),
        "total_spent": money_to_float(c.get("total_spent")),
        "orders_count": c.get("orders_count", 0),
        "membership_tier_id": c.get("membership_tier_id"),
        "created_at": c.get("created_at"),
        "updated_at": c.get("updated_at"),
    }

    # 儲值金紀錄
    store_credits = []
    try:
        sc_data = api_get("customer_store_credit_history", path_params=path_params)
        for sc in (sc_data.get("items", []) if isinstance(sc_data, dict) else []):
            store_credits.append({
                "amount": money_to_float(sc.get("amount")),
                "balance": money_to_float(sc.get("balance")),
                "type": sc.get("type"),
                "note": sc.get("note"),
                "created_at": sc.get("created_at"),
            })
    except Exception:
        store_credits = [{"error": "無法取得儲值金紀錄"}]

    # 會員點數紀錄
    member_points = []
    try:
        mp_data = api_get("customer_member_points", path_params=path_params)
        for mp in (mp_data.get("items", []) if isinstance(mp_data, dict) else []):
            member_points.append({
                "points": mp.get("points", 0),
                "balance": mp.get("balance", 0),
                "type": mp.get("type"),
                "note": mp.get("note"),
                "created_at": mp.get("created_at"),
            })
    except Exception:
        member_points = [{"error": "無法取得會員點數紀錄"}]

    # 會員等級變動
    tier_history = []
    try:
        th_data = api_get("customer_membership_tier_history", path_params=path_params)
        for th in (th_data.get("items", []) if isinstance(th_data, dict) else []):
            tier_history.append({
                "from_tier": th.get("from_tier"),
                "to_tier": th.get("to_tier"),
                "reason": th.get("reason"),
                "created_at": th.get("created_at"),
            })
    except Exception:
        tier_history = [{"error": "無法取得會員等級變動紀錄"}]

    # 客戶可用優惠
    promotions = []
    try:
        promo_data = api_get("customer_promotions", path_params=path_params)
        for p in (promo_data.get("items", []) if isinstance(promo_data, dict) else []):
            promotions.append({
                "id": p.get("id"),
                "title": get_translation(p.get("title_translations")),
                "status": p.get("status"),
                "discount_type": p.get("discount_type"),
            })
    except Exception:
        promotions = [{"error": "無法取得客戶優惠"}]

    return {
        "profile": profile,
        "store_credits": store_credits,
        "member_points": member_points,
        "tier_history": tier_history,
        "promotions": promotions,
    }
```

- [ ] **Step 2: Create `tests/test_customer_tools.py`**

```python
"""
客戶工具端對端測試 — 驗證 Customer API 權限 & 工具可正常呼叫
"""
import sys
import os
import json
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import tools.customer_tools  # noqa: F401
from tools.customer_tools import list_customers, get_customer_profile


def run_test(name, fn, **kwargs):
    """執行一個 Tool 並印出結果摘要"""
    print(f"\n{'─' * 50}")
    print(f"🔧 {name}")
    print(f"   params: {kwargs}")
    try:
        result = fn(**kwargs)
        if isinstance(result, dict) and "error" in result and result["error"]:
            print(f"   ❌ Error: {result['error']}")
            return False

        for k, v in result.items():
            if isinstance(v, list):
                print(f"   {k}: [{len(v)} items]")
                if v and isinstance(v[0], dict):
                    print(f"     first: {json.dumps(v[0], ensure_ascii=False)[:200]}")
            elif isinstance(v, dict) and len(str(v)) > 200:
                print(f"   {k}: {{...{len(v)} keys}}")
            else:
                print(f"   {k}: {v}")

        print(f"   ✅ OK")
        return True
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Customer Tools 端對端測試")
    print("=" * 60)

    results = {}

    # --- list_customers (無篩選) ---
    results["list_customers"] = run_test(
        "list_customers", list_customers, max_results=5
    )

    # --- list_customers (搜尋) ---
    results["list_customers_search"] = run_test(
        "list_customers (search)", list_customers,
        search_keyword="test", max_results=5
    )

    # --- get_customer_profile ---
    # 先取一個 customer ID
    from tools.base_tool import api_get
    try:
        cust_data = api_get("customers", params={"per_page": 1})
        customers = cust_data.get("items", [])
        if customers:
            cid = customers[0]["id"]
            results["get_customer_profile"] = run_test(
                "get_customer_profile", get_customer_profile, customer_id=cid
            )
        else:
            print("\n⚠️ 無客戶資料可測試 get_customer_profile")
            results["get_customer_profile"] = False
    except Exception as e:
        print(f"\n❌ 無法取得客戶列表: {e}")
        traceback.print_exc()
        results["get_customer_profile"] = False

    # --- 總結 ---
    print("\n" + "=" * 60)
    print("Customer Tools 測試結果")
    print("=" * 60)
    passed = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)
    for name, ok in results.items():
        icon = "✅" if ok else "❌"
        print(f"  {icon} {name}")

    print(f"\n通過: {passed}/{len(results)}, 失敗: {failed}/{len(results)}")

    if failed > 0:
        print("\n⚠️  如果 Customer API 回 403，請確認 Shopline API token 已授予客戶資料權限")
```

- [ ] **Step 3: Run the customer test**

Run: `python tests/test_customer_tools.py`
Expected: All tests pass. If Customer API returns 403, **STOP and report to user** before proceeding.

- [ ] **Step 4: Commit**

```bash
git add tools/customer_tools.py tests/test_customer_tools.py
git commit -m "feat: add customer read tools (list_customers, get_customer_profile)"
```

---

## Task 4: Create `customer_group_tools.py` — Customer Group Tools

**Files:**
- Create: `tools/customer_group_tools.py`
- Create: `tests/test_customer_group_tools.py`

- [ ] **Step 1: Create `tools/customer_group_tools.py`**

```python
"""
客戶群組 Tools — 客戶分群列表、成員查詢
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import Optional
from pydantic import Field

from app import mcp
from tools.base_tool import api_get, fetch_all_pages


# ============================================================
# Tool 1: list_customer_groups — 客戶群組列表
# ============================================================
@mcp.tool()
def list_customer_groups(
    search_keyword: Optional[str] = Field(default=None, description="群組名稱搜尋關鍵字"),
    max_results: int = Field(default=50, description="最多回傳筆數"),
) -> dict:
    """取得客戶群組列表，支援依名稱搜尋。

    【用途】
    瀏覽或搜尋已建立的客戶群組（分群）。可用於確認客戶標籤分群策略、
    取得群組 ID 後進一步查詢群組成員。

    【呼叫的 Shopline API】
    - GET /v1/customer-groups（無搜尋條件時）
    - GET /v1/customer-groups/search（有搜尋條件時）

    【回傳結構】
    dict 含 total_found, returned, groups[]。
    每個 group 包含 id, name, customers_count, created_at。
    """
    if search_keyword:
        params = {"keyword": search_keyword, "per_page": min(max_results, 50)}
        data = api_get("customer_groups_search", params=params)
        groups = data.get("items", [])
    else:
        groups = fetch_all_pages("customer_groups", max_pages=max(1, max_results // 50))

    results = []
    for g in groups[:max_results]:
        results.append({
            "id": g.get("id"),
            "name": g.get("name"),
            "customers_count": g.get("customers_count", 0),
            "created_at": g.get("created_at"),
            "updated_at": g.get("updated_at"),
        })

    return {
        "total_found": len(groups),
        "returned": len(results),
        "groups": results,
    }


# ============================================================
# Tool 2: get_customer_group_members — 群組成員列表
# ============================================================
@mcp.tool()
def get_customer_group_members(
    group_id: str = Field(description="客戶群組 ID（由 list_customer_groups 回傳）"),
) -> dict:
    """取得指定客戶群組中的所有客戶 ID 列表。

    【用途】
    查詢特定群組包含哪些客戶。回傳客戶 ID 列表，可搭配 get_customer_profile 取得個別客戶詳情。

    【呼叫的 Shopline API】
    - GET /v1/customer-groups/{group_id}/customers

    【回傳結構】
    dict 含 group_id, total_members, customer_ids[]。
    """
    data = api_get("customer_group_customers", path_params={"group_id": group_id})
    customer_ids = data.get("items", data.get("customer_ids", []))

    return {
        "group_id": group_id,
        "total_members": len(customer_ids),
        "customer_ids": customer_ids,
    }
```

- [ ] **Step 2: Create `tests/test_customer_group_tools.py`**

```python
"""
客戶群組工具端對端測試
"""
import sys
import os
import json
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import tools.customer_group_tools  # noqa: F401
from tools.customer_group_tools import list_customer_groups, get_customer_group_members


def run_test(name, fn, **kwargs):
    print(f"\n{'─' * 50}")
    print(f"🔧 {name}")
    print(f"   params: {kwargs}")
    try:
        result = fn(**kwargs)
        for k, v in result.items():
            if isinstance(v, list):
                print(f"   {k}: [{len(v)} items]")
            else:
                print(f"   {k}: {v}")
        print(f"   ✅ OK")
        return True
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Customer Group Tools 端對端測試")
    print("=" * 60)

    results = {}

    results["list_customer_groups"] = run_test(
        "list_customer_groups", list_customer_groups, max_results=5
    )

    # 取一個 group ID 測試成員查詢
    try:
        from tools.base_tool import api_get
        grp_data = api_get("customer_groups", params={"per_page": 1})
        groups = grp_data.get("items", [])
        if groups:
            gid = groups[0]["id"]
            results["get_customer_group_members"] = run_test(
                "get_customer_group_members", get_customer_group_members, group_id=gid
            )
        else:
            print("\n⚠️ 無客戶群組可測試")
            results["get_customer_group_members"] = False
    except Exception as e:
        print(f"\n⚠️ 無法取得客戶群組: {e}")
        results["get_customer_group_members"] = False

    # 總結
    print("\n" + "=" * 60)
    passed = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)
    for name, ok in results.items():
        print(f"  {'✅' if ok else '❌'} {name}")
    print(f"\n通過: {passed}/{len(results)}, 失敗: {failed}/{len(results)}")
```

- [ ] **Step 3: Run the test**

Run: `python tests/test_customer_group_tools.py`
Expected: All tests pass.

- [ ] **Step 4: Commit**

```bash
git add tools/customer_group_tools.py tests/test_customer_group_tools.py
git commit -m "feat: add customer group tools (list_customer_groups, get_customer_group_members)"
```

---

## Task 5: Create `store_credit_tools.py` — Store Credit Tools

**Files:**
- Create: `tools/store_credit_tools.py`
- Create: `tests/test_store_credit_tools.py`

- [ ] **Step 1: Create `tools/store_credit_tools.py`**

```python
"""
客戶儲值金 Tools — 儲值金餘額查詢
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import Optional
from pydantic import Field

from app import mcp
from tools.base_tool import api_get, fetch_all_pages, money_to_float


# ============================================================
# Tool 1: list_store_credits — 客戶儲值金列表
# ============================================================
@mcp.tool()
def list_store_credits(
    max_results: int = Field(default=50, description="最多回傳筆數"),
) -> dict:
    """取得所有客戶的儲值金餘額列表。

    【用途】
    瀏覽客戶儲值金餘額概況，了解儲值金發放與使用狀況。
    可用於計算儲值金負債、找出高餘額客戶。

    【呼叫的 Shopline API】
    - GET /v1/user_credits

    【回傳結構】
    dict 含 total_found, returned, credits[]。
    每個 credit 包含 customer_id, balance (TWD float)。
    """
    credits_list = fetch_all_pages("user_credits", max_pages=max(1, max_results // 50))

    results = []
    for cr in credits_list[:max_results]:
        results.append({
            "customer_id": cr.get("customer_id") or cr.get("user_id"),
            "customer_name": cr.get("customer_name") or cr.get("name"),
            "balance": money_to_float(cr.get("balance")),
            "updated_at": cr.get("updated_at"),
        })

    total_balance = sum(r["balance"] for r in results)

    return {
        "total_found": len(credits_list),
        "returned": len(results),
        "total_balance": round(total_balance, 2),
        "credits": results,
    }
```

- [ ] **Step 2: Create `tests/test_store_credit_tools.py`**

```python
"""
客戶儲值金工具端對端測試
"""
import sys
import os
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import tools.store_credit_tools  # noqa: F401
from tools.store_credit_tools import list_store_credits


if __name__ == "__main__":
    print("=" * 60)
    print("Store Credit Tools 端對端測試")
    print("=" * 60)

    results = {}

    print(f"\n{'─' * 50}")
    print(f"🔧 list_store_credits")
    try:
        result = list_store_credits(max_results=5)
        print(f"   total_found: {result.get('total_found')}")
        print(f"   returned: {result.get('returned')}")
        print(f"   total_balance: {result.get('total_balance')}")
        if result.get("credits"):
            print(f"   first: {result['credits'][0]}")
        print(f"   ✅ OK")
        results["list_store_credits"] = True
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        traceback.print_exc()
        results["list_store_credits"] = False

    passed = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)
    print(f"\n通過: {passed}/{len(results)}, 失敗: {failed}/{len(results)}")
```

- [ ] **Step 3: Run the test**

Run: `python tests/test_store_credit_tools.py`
Expected: Pass.

- [ ] **Step 4: Commit**

```bash
git add tools/store_credit_tools.py tests/test_store_credit_tools.py
git commit -m "feat: add store credit tool (list_store_credits)"
```

---

## Task 6: Create `membership_tier_tools.py` — Membership Tier Tools

**Files:**
- Create: `tools/membership_tier_tools.py`
- Create: `tests/test_membership_tier_tools.py`

- [ ] **Step 1: Create `tools/membership_tier_tools.py`**

```python
"""
會員等級 Tools — 會員等級列表、個別會員等級變動歷程
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pydantic import Field

from app import mcp
from tools.base_tool import api_get, fetch_all_pages


# ============================================================
# Tool 1: list_membership_tiers — 會員等級列表
# ============================================================
@mcp.tool()
def list_membership_tiers() -> dict:
    """取得商店的所有會員等級定義。

    【用途】
    查看商店設定了哪些會員等級、升等門檻、各等級權益。
    用於分析會員結構或確認等級設定。

    【呼叫的 Shopline API】
    - GET /v1/membership_tiers

    【回傳結構】
    dict 含 total, tiers[]。
    每個 tier 包含 id, name, threshold, benefits 等。
    """
    data = api_get("membership_tiers")
    tiers = data.get("items", []) if isinstance(data, dict) else []

    results = []
    for t in tiers:
        results.append({
            "id": t.get("id"),
            "name": t.get("name"),
            "threshold": t.get("threshold"),
            "description": t.get("description"),
            "benefits": t.get("benefits"),
            "created_at": t.get("created_at"),
        })

    return {
        "total": len(results),
        "tiers": results,
    }


# ============================================================
# Tool 2: get_customer_tier_history — 個別客戶等級變動
# ============================================================
@mcp.tool()
def get_customer_tier_history(
    customer_id: str = Field(description="客戶內部 ID"),
) -> dict:
    """取得指定客戶的會員等級變動歷程。

    【用途】
    追蹤客戶會員等級升降紀錄，了解是升等還是降級、原因為何。
    搭配 list_membership_tiers 對照等級名稱。

    【呼叫的 Shopline API】
    - GET /v1/customers/{customer_id}/membership-tier-history

    【回傳結構】
    dict 含 customer_id, total_changes, history[]。
    每筆含 from_tier, to_tier, reason, created_at。
    """
    data = api_get("customer_membership_tier_history",
                   path_params={"customer_id": customer_id})
    items = data.get("items", []) if isinstance(data, dict) else []

    history = []
    for h in items:
        history.append({
            "from_tier": h.get("from_tier"),
            "to_tier": h.get("to_tier"),
            "reason": h.get("reason"),
            "created_at": h.get("created_at"),
        })

    return {
        "customer_id": customer_id,
        "total_changes": len(history),
        "history": history,
    }
```

- [ ] **Step 2: Create `tests/test_membership_tier_tools.py`**

```python
"""
會員等級工具端對端測試
"""
import sys
import os
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import tools.membership_tier_tools  # noqa: F401
from tools.membership_tier_tools import list_membership_tiers, get_customer_tier_history


if __name__ == "__main__":
    print("=" * 60)
    print("Membership Tier Tools 端對端測試")
    print("=" * 60)

    results = {}

    print(f"\n{'─' * 50}")
    print(f"🔧 list_membership_tiers")
    try:
        result = list_membership_tiers()
        print(f"   total: {result.get('total')}")
        if result.get("tiers"):
            print(f"   first: {result['tiers'][0]}")
        print(f"   ✅ OK")
        results["list_membership_tiers"] = True
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        traceback.print_exc()
        results["list_membership_tiers"] = False

    # 取一個 customer ID 測試 tier history
    print(f"\n{'─' * 50}")
    print(f"🔧 get_customer_tier_history")
    try:
        from tools.base_tool import api_get
        cust_data = api_get("customers", params={"per_page": 1})
        customers = cust_data.get("items", [])
        if customers:
            cid = customers[0]["id"]
            result = get_customer_tier_history(customer_id=cid)
            print(f"   customer_id: {result.get('customer_id')}")
            print(f"   total_changes: {result.get('total_changes')}")
            print(f"   ✅ OK")
            results["get_customer_tier_history"] = True
        else:
            print(f"   ⚠️ 無客戶可測試")
            results["get_customer_tier_history"] = False
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        traceback.print_exc()
        results["get_customer_tier_history"] = False

    passed = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)
    print(f"\n通過: {passed}/{len(results)}, 失敗: {failed}/{len(results)}")
```

- [ ] **Step 3: Run the test**

Run: `python tests/test_membership_tier_tools.py`
Expected: Pass.

- [ ] **Step 4: Commit**

```bash
git add tools/membership_tier_tools.py tests/test_membership_tier_tools.py
git commit -m "feat: add membership tier tools (list_membership_tiers, get_customer_tier_history)"
```

---

## Task 7: Create `member_point_tools.py` — Member Point Rules

**Files:**
- Create: `tools/member_point_tools.py`
- Create: `tests/test_member_point_tools.py`

- [ ] **Step 1: Create `tools/member_point_tools.py`**

```python
"""
會員點數規則 Tools — 點數規則查詢
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import mcp
from tools.base_tool import api_get


# ============================================================
# Tool 1: list_member_point_rules — 點數規則列表
# ============================================================
@mcp.tool()
def list_member_point_rules() -> dict:
    """取得商店的會員點數規則設定。

    【用途】
    查看商店設定的點數回饋規則（消費回饋比例、點數到期規則等）。
    用於分析會員忠誠度計畫或對照客戶點數異動。

    【呼叫的 Shopline API】
    - GET /v1/member_point_rules

    【回傳結構】
    dict 含 total, rules[]。
    每條規則含 id, name, type, value, conditions 等。
    """
    data = api_get("member_point_rules")
    rules = data.get("items", []) if isinstance(data, dict) else []

    results = []
    for r in rules:
        results.append({
            "id": r.get("id"),
            "name": r.get("name"),
            "type": r.get("type"),
            "value": r.get("value"),
            "status": r.get("status"),
            "conditions": r.get("conditions"),
            "created_at": r.get("created_at"),
        })

    return {
        "total": len(results),
        "rules": results,
    }
```

- [ ] **Step 2: Create `tests/test_member_point_tools.py`**

```python
"""
會員點數規則工具端對端測試
"""
import sys
import os
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import tools.member_point_tools  # noqa: F401
from tools.member_point_tools import list_member_point_rules


if __name__ == "__main__":
    print("=" * 60)
    print("Member Point Rules Tools 端對端測試")
    print("=" * 60)

    print(f"\n{'─' * 50}")
    print(f"🔧 list_member_point_rules")
    try:
        result = list_member_point_rules()
        print(f"   total: {result.get('total')}")
        if result.get("rules"):
            print(f"   first: {result['rules'][0]}")
        print(f"   ✅ OK")
        passed = 1
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        traceback.print_exc()
        passed = 0

    print(f"\n通過: {passed}/1, 失敗: {1 - passed}/1")
```

- [ ] **Step 3: Run the test**

Run: `python tests/test_member_point_tools.py`
Expected: Pass.

- [ ] **Step 4: Commit**

```bash
git add tools/member_point_tools.py tests/test_member_point_tools.py
git commit -m "feat: add member point rules tool (list_member_point_rules)"
```

---

## Task 8: Create `custom_field_tools.py` — Custom Fields

**Files:**
- Create: `tools/custom_field_tools.py`
- Create: `tests/test_custom_field_tools.py`

- [ ] **Step 1: Create `tools/custom_field_tools.py`**

```python
"""
自訂欄位 Tools — 客戶自訂欄位定義查詢
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import mcp
from tools.base_tool import api_get, get_translation


# ============================================================
# Tool 1: list_custom_fields — 自訂欄位列表
# ============================================================
@mcp.tool()
def list_custom_fields() -> dict:
    """取得商店定義的客戶自訂欄位清單。

    【用途】
    查看商店在客戶資料上設定了哪些額外自訂欄位（如生日、偏好、備註等）。
    用於了解客戶資料結構或分析資料完整度。

    【呼叫的 Shopline API】
    - GET /v1/custom_fields

    【回傳結構】
    dict 含 total, fields[]。
    每個 field 包含 id, name, type, options 等。
    """
    data = api_get("custom_fields")
    fields = data.get("items", []) if isinstance(data, dict) else []

    results = []
    for f in fields:
        results.append({
            "id": f.get("id"),
            "name": get_translation(f.get("name_translations")) or f.get("name"),
            "type": f.get("type"),
            "required": f.get("required", False),
            "options": f.get("options", []),
            "created_at": f.get("created_at"),
        })

    return {
        "total": len(results),
        "fields": results,
    }
```

- [ ] **Step 2: Create `tests/test_custom_field_tools.py`**

```python
"""
自訂欄位工具端對端測試
"""
import sys
import os
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import tools.custom_field_tools  # noqa: F401
from tools.custom_field_tools import list_custom_fields


if __name__ == "__main__":
    print("=" * 60)
    print("Custom Field Tools 端對端測試")
    print("=" * 60)

    print(f"\n{'─' * 50}")
    print(f"🔧 list_custom_fields")
    try:
        result = list_custom_fields()
        print(f"   total: {result.get('total')}")
        if result.get("fields"):
            print(f"   first: {result['fields'][0]}")
        print(f"   ✅ OK")
        passed = 1
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        traceback.print_exc()
        passed = 0

    print(f"\n通過: {passed}/1, 失敗: {1 - passed}/1")
```

- [ ] **Step 3: Run the test**

Run: `python tests/test_custom_field_tools.py`
Expected: Pass.

- [ ] **Step 4: Commit**

```bash
git add tools/custom_field_tools.py tests/test_custom_field_tools.py
git commit -m "feat: add custom field tool (list_custom_fields)"
```

---

## Task 9: Register New Modules in `mcp_server.py`

**Files:**
- Modify: `mcp_server.py`

- [ ] **Step 1: Add imports for all Phase 1 modules**

Update `mcp_server.py` to:

```python
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

# --- Phase 1: Customer domain write tools ---
import tools.writes.customer_writes  # noqa: F401

from app import mcp


def main():
    mcp.run()  # 預設 stdio transport


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify tool count**

Run: `python -c "import sys; sys.path.insert(0,'.'); import mcp_server; from app import mcp; import asyncio; tools=asyncio.run(mcp.list_tools()); print(f'Total tools: {len(tools)}')"`

Expected: Total tools should be 19 (existing) + new tools from Phase 1. The exact count depends on how many customer write tools are registered (Task 10 hasn't run yet, so this verification can happen after Task 10).

- [ ] **Step 3: Commit**

```bash
git add mcp_server.py
git commit -m "feat: register Phase 1 customer domain modules in mcp_server.py"
```

---

## Task 10: Create `writes/customer_writes.py` — Customer Write Tools

**Files:**
- Create: `tools/writes/__init__.py`
- Create: `tools/writes/customer_writes.py`
- Create: `tests/test_writes/test_customer_writes.py`

- [ ] **Step 1: Create `tools/writes/__init__.py`**

```python
```

(Empty file — just marks the directory as a Python package.)

- [ ] **Step 2: Create `tools/writes/customer_writes.py`**

```python
"""
客戶寫入 Tools — 建立、更新、刪除客戶；標籤、儲值金、點數調整
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from typing import Optional, List
from pydantic import Field

from app import mcp
from tools.base_tool import api_post, api_put, api_delete


# ============================================================
# Tool 1: create_customer — 建立客戶
# ============================================================
@mcp.tool()
def create_customer(
    name: str = Field(description="客戶姓名"),
    email: Optional[str] = Field(default=None, description="Email"),
    phone: Optional[str] = Field(default=None, description="電話"),
    gender: Optional[str] = Field(default=None, description="性別 (male/female/other)"),
    birthday: Optional[str] = Field(default=None, description="生日 YYYY-MM-DD"),
    tags: Optional[List[str]] = Field(default=None, description="標籤列表"),
) -> dict:
    """[WRITE] 建立新客戶。

    【用途】
    在 Shopline 商店中建立新的客戶記錄。適合客服手動建檔或批次匯入場景。

    【呼叫的 Shopline API】
    - POST /v1/customers

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str, customer: dict。

    【副作用】
    - 在商店客戶列表中新增一筆客戶
    - 如果 email 或 phone 已存在，可能會失敗（Shopline 可能不允許重複）
    """
    body = {"name": name}
    if email:
        body["email"] = email
    if phone:
        body["phone"] = phone
    if gender:
        body["gender"] = gender
    if birthday:
        body["birthday"] = birthday
    if tags:
        body["tags"] = tags

    result = api_post("customer_create", json_body=body)

    customer = result if "id" in result else result.get("item", result)
    return {
        "success": True,
        "resource_id": customer.get("id", ""),
        "message": f"客戶 {name} 建立成功",
        "customer": customer,
    }


# ============================================================
# Tool 2: update_customer — 更新客戶資料
# ============================================================
@mcp.tool()
def update_customer(
    customer_id: str = Field(description="客戶內部 ID"),
    name: Optional[str] = Field(default=None, description="新姓名"),
    email: Optional[str] = Field(default=None, description="新 Email"),
    phone: Optional[str] = Field(default=None, description="新電話"),
    gender: Optional[str] = Field(default=None, description="性別 (male/female/other)"),
    birthday: Optional[str] = Field(default=None, description="生日 YYYY-MM-DD"),
) -> dict:
    """[WRITE] 更新客戶基本資料。

    【用途】
    修改客戶姓名、聯絡方式、生日等基本資料。僅傳入要修改的欄位，未傳入的欄位不會被覆蓋。

    【呼叫的 Shopline API】
    - PUT /v1/customers/{customer_id}

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 修改客戶資料，變更立即生效
    - 不可復原（無版本歷史），但可再次呼叫此工具覆蓋
    """
    body = {}
    if name is not None:
        body["name"] = name
    if email is not None:
        body["email"] = email
    if phone is not None:
        body["phone"] = phone
    if gender is not None:
        body["gender"] = gender
    if birthday is not None:
        body["birthday"] = birthday

    if not body:
        return {"success": False, "resource_id": customer_id, "message": "未提供任何要更新的欄位"}

    api_put("customer_update", json_body=body, path_params={"customer_id": customer_id})
    return {
        "success": True,
        "resource_id": customer_id,
        "message": f"客戶 {customer_id} 資料已更新",
    }


# ============================================================
# Tool 3: delete_customer — 刪除客戶
# ============================================================
@mcp.tool()
def delete_customer(
    customer_id: str = Field(description="客戶內部 ID"),
) -> dict:
    """[WRITE] 刪除客戶。

    【用途】
    從 Shopline 商店中刪除客戶記錄。通常用於清除測試資料或 GDPR 合規需求。

    【呼叫的 Shopline API】
    - DELETE /v1/customers/{customer_id}

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 永久刪除客戶記錄，不可復原
    - 客戶相關的訂單紀錄可能仍保留（取決於 Shopline 實作）
    """
    api_delete("customer_delete", path_params={"customer_id": customer_id})
    return {
        "success": True,
        "resource_id": customer_id,
        "message": f"客戶 {customer_id} 已刪除",
    }


# ============================================================
# Tool 4: update_customer_tags — 更新客戶標籤
# ============================================================
@mcp.tool()
def update_customer_tags(
    customer_id: str = Field(description="客戶內部 ID"),
    tags: List[str] = Field(description="標籤列表（會取代現有標籤）"),
) -> dict:
    """[WRITE] 設定客戶標籤（覆蓋現有標籤）。

    【用途】
    為客戶設定標籤，常用於行銷分群、VIP 標記等。注意：會覆蓋客戶現有的所有標籤。

    【呼叫的 Shopline API】
    - PUT /v1/customers/{customer_id}/tags

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 覆蓋客戶的所有現有標籤為新的標籤列表
    - 若要新增標籤而非覆蓋，請先用 get_customer_profile 取得現有標籤再合併
    """
    api_put("customer_tags", json_body={"tags": tags},
            path_params={"customer_id": customer_id})
    return {
        "success": True,
        "resource_id": customer_id,
        "message": f"客戶 {customer_id} 標籤已更新為 {tags}",
    }


# ============================================================
# Tool 5: update_customer_store_credits — 調整客戶儲值金
# ============================================================
@mcp.tool()
def update_customer_store_credits(
    customer_id: str = Field(description="客戶內部 ID"),
    amount: float = Field(description="調整金額（正數=增加，負數=扣除）"),
    note: Optional[str] = Field(default=None, description="調整備註/原因"),
) -> dict:
    """[WRITE] 調整客戶儲值金餘額。

    【用途】
    增加或扣除客戶儲值金，常用於儲值金充值、退款補償、活動贈送等場景。

    【呼叫的 Shopline API】
    - PUT /v1/customers/{customer_id}/store-credits

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 客戶儲值金餘額立即變動
    - 異動紀錄會寫入客戶的儲值金歷史（可透過 get_customer_profile 查看）
    - 扣除後如餘額不足，API 可能回傳錯誤
    """
    body = {"amount": amount}
    if note:
        body["note"] = note

    api_put("customer_store_credits_update", json_body=body,
            path_params={"customer_id": customer_id})
    return {
        "success": True,
        "resource_id": customer_id,
        "message": f"客戶 {customer_id} 儲值金已調整 {amount:+.2f}",
    }


# ============================================================
# Tool 6: adjust_customer_member_points — 調整客戶會員點數
# ============================================================
@mcp.tool()
def adjust_customer_member_points(
    customer_id: str = Field(description="客戶內部 ID"),
    points: int = Field(description="調整點數（正數=增加，負數=扣除）"),
    note: Optional[str] = Field(default=None, description="調整備註/原因"),
) -> dict:
    """[WRITE] 調整客戶會員點數。

    【用途】
    增加或扣除客戶會員點數，常用於手動補點、活動贈點、客訴補償等場景。

    【呼叫的 Shopline API】
    - PUT /v1/customers/{customer_id}/member-points

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 客戶點數餘額立即變動
    - 異動紀錄會寫入客戶的點數歷史（可透過 get_customer_profile 查看）
    - 扣除後如點數不足，API 可能回傳錯誤
    """
    body = {"points": points}
    if note:
        body["note"] = note

    api_put("customer_member_points_update", json_body=body,
            path_params={"customer_id": customer_id})
    return {
        "success": True,
        "resource_id": customer_id,
        "message": f"客戶 {customer_id} 會員點數已調整 {points:+d}",
    }
```

- [ ] **Step 3: Create `tests/test_writes/test_customer_writes.py`**

```python
"""
客戶寫入工具端對端測試 — 需設定 SHOPLINE_TEST_WRITES=1 才會執行

⚠️ 此測試會在正式帳號上建立/修改/刪除客戶資料
"""
import sys
import os
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# Gate: 預設 skip
if os.environ.get("SHOPLINE_TEST_WRITES", "").lower() not in ("1", "true", "yes"):
    print("⚠ Customer write tests skipped. Set SHOPLINE_TEST_WRITES=1 to run.")
    sys.exit(0)

import tools.writes.customer_writes  # noqa: F401
from tools.writes.customer_writes import (
    create_customer, update_customer, delete_customer,
    update_customer_tags, update_customer_store_credits,
    adjust_customer_member_points,
)


if __name__ == "__main__":
    print("=" * 60)
    print("Customer Write Tools 端對端測試")
    print("⚠️  此測試會修改正式資料")
    print("=" * 60)

    results = {}
    test_customer_id = None

    # --- create_customer ---
    print(f"\n{'─' * 50}")
    print(f"🔧 create_customer")
    try:
        result = create_customer(
            name="MCP 測試客戶",
            email="mcp-test@example.com",
            phone="0900000000",
            tags=["mcp-test"],
        )
        print(f"   success: {result['success']}")
        print(f"   resource_id: {result['resource_id']}")
        test_customer_id = result["resource_id"]
        print(f"   ✅ OK")
        results["create_customer"] = True
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        traceback.print_exc()
        results["create_customer"] = False

    if test_customer_id:
        # --- update_customer ---
        print(f"\n{'─' * 50}")
        print(f"🔧 update_customer")
        try:
            result = update_customer(customer_id=test_customer_id, name="MCP 測試客戶 (已更新)")
            print(f"   success: {result['success']}")
            print(f"   ✅ OK")
            results["update_customer"] = True
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            traceback.print_exc()
            results["update_customer"] = False

        # --- update_customer_tags ---
        print(f"\n{'─' * 50}")
        print(f"🔧 update_customer_tags")
        try:
            result = update_customer_tags(customer_id=test_customer_id, tags=["mcp-test", "vip"])
            print(f"   success: {result['success']}")
            print(f"   ✅ OK")
            results["update_customer_tags"] = True
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            traceback.print_exc()
            results["update_customer_tags"] = False

        # --- delete_customer (cleanup) ---
        print(f"\n{'─' * 50}")
        print(f"🔧 delete_customer (cleanup)")
        try:
            result = delete_customer(customer_id=test_customer_id)
            print(f"   success: {result['success']}")
            print(f"   ✅ OK")
            results["delete_customer"] = True
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            traceback.print_exc()
            results["delete_customer"] = False

    # Note: update_customer_store_credits and adjust_customer_member_points
    # are NOT tested here to avoid affecting real customer balances.
    # Test these manually with a known test customer.

    # --- 總結 ---
    print("\n" + "=" * 60)
    print("Customer Write Tools 測試結果")
    print("=" * 60)
    passed = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)
    for name, ok in results.items():
        print(f"  {'✅' if ok else '❌'} {name}")
    print(f"\n通過: {passed}/{len(results)}, 失敗: {failed}/{len(results)}")
```

- [ ] **Step 4: Create `tests/test_writes/` directory init**

Create an empty `tests/test_writes/__init__.py` (not needed for script execution, but create a `run_write_tests.py` placeholder):

```python
# tests/test_writes/run_write_tests.py
"""
寫入工具測試統一入口

使用: SHOPLINE_TEST_WRITES=1 python tests/test_writes/run_write_tests.py
"""
import os
import sys
import subprocess

if os.environ.get("SHOPLINE_TEST_WRITES", "").lower() not in ("1", "true", "yes"):
    print("⚠ Write tests skipped. Set SHOPLINE_TEST_WRITES=1 to run.")
    sys.exit(0)

test_dir = os.path.dirname(os.path.abspath(__file__))

# 自動找出所有 test_*.py 檔案
test_files = sorted(
    f for f in os.listdir(test_dir)
    if f.startswith("test_") and f.endswith(".py")
)

print(f"Found {len(test_files)} write test files\n")

failed = []
for tf in test_files:
    print(f"\n{'=' * 60}")
    print(f"Running {tf}")
    print(f"{'=' * 60}")
    result = subprocess.run([sys.executable, os.path.join(test_dir, tf)])
    if result.returncode != 0:
        failed.append(tf)

print(f"\n{'=' * 60}")
if failed:
    print(f"❌ {len(failed)} test file(s) failed: {failed}")
    sys.exit(1)
else:
    print(f"✅ All {len(test_files)} write test files passed")
```

- [ ] **Step 5: Run write tests (only if SHOPLINE_TEST_WRITES is set)**

Run: `SHOPLINE_TEST_WRITES=1 python tests/test_writes/test_customer_writes.py`
Expected: Creates test customer, updates, adds tags, deletes. All pass.

If you do NOT want to run write tests against production, skip this step. The read tests in Tasks 3-8 already verify Customer API access.

- [ ] **Step 6: Commit**

```bash
git add tools/writes/__init__.py tools/writes/customer_writes.py tests/test_writes/test_customer_writes.py tests/test_writes/run_write_tests.py
git commit -m "feat: add customer write tools (create/update/delete/tags/credits/points)"
```

---

## Task 11: Full Phase 0+1 Integration Test & Final Commit

- [ ] **Step 1: Run all existing tests to verify no regression**

Run: `python tests/test_all_tools.py`
Expected: All 19 existing tools still pass.

- [ ] **Step 2: Run all Phase 1 read tests**

Run these sequentially:
```bash
python tests/test_customer_tools.py
python tests/test_customer_group_tools.py
python tests/test_store_credit_tools.py
python tests/test_membership_tier_tools.py
python tests/test_member_point_tools.py
python tests/test_custom_field_tools.py
```
Expected: All pass. If any Customer-related test returns 403, report to user.

- [ ] **Step 3: Verify total tool count**

Run: `python -c "import sys; sys.path.insert(0,'.'); import mcp_server; from app import mcp; import asyncio; tools=asyncio.run(mcp.list_tools()); print(f'Total tools: {len(tools)}'); [print(f'  - {t.name}') for t in tools]"`

Expected: 19 existing + 10 new read tools + 6 write tools = ~35 tools total.

New tools should include:
- Read: `list_customers`, `get_customer_profile`, `list_customer_groups`, `get_customer_group_members`, `list_store_credits`, `list_membership_tiers`, `get_customer_tier_history`, `list_member_point_rules`, `list_custom_fields`
- Write: `create_customer`, `update_customer`, `delete_customer`, `update_customer_tags`, `update_customer_store_credits`, `adjust_customer_member_points`

- [ ] **Step 4: Final commit (if any uncommitted changes)**

```bash
git status
# If clean, no action needed. If not, commit remaining changes.
```

---

## Next Steps

After Phase 0+1 is complete and all tests pass:

1. **If Customer API returned 403:** Report to user. Do not proceed to Phase 2.
2. **If all pass:** Write implementation plans for Phase 2 (expand existing files) and Phase 3 (new domain reads). These phases can be planned and executed in parallel.

Phase 2-5 plans will be written as separate documents:
- `docs/superpowers/plans/2026-04-XX-phase2-existing-expansion.md`
- `docs/superpowers/plans/2026-04-XX-phase3-new-domains.md`
- `docs/superpowers/plans/2026-04-XX-phase4-write-tools.md`
- `docs/superpowers/plans/2026-04-XX-phase5-finalization.md`
