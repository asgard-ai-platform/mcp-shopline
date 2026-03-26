"""Shopline API 設定"""
import os

BASE_URL = "https://open.shopline.io"
API_VERSION = "v1"
ACCESS_TOKEN = os.environ.get("SHOPLINE_API_TOKEN", "")

# 預設分頁設定
DEFAULT_PER_PAGE = 50  # API 建議上限
DEFAULT_SORT = "desc"

# API 端點
ENDPOINTS = {
    "orders": f"/{API_VERSION}/orders",
    "orders_search": f"/{API_VERSION}/orders/search",
    "order_detail": f"/{API_VERSION}/orders/{{order_id}}",
    "products": f"/{API_VERSION}/products",
    "products_search": f"/{API_VERSION}/products/search",
    "product_stocks": f"/{API_VERSION}/products/{{product_id}}/stocks",
    "categories": f"/{API_VERSION}/categories",
    "customers": f"/{API_VERSION}/customers",
    "customers_search": f"/{API_VERSION}/customers/search",
    "customer_detail": f"/{API_VERSION}/customers/{{customer_id}}",
    "warehouses": f"/{API_VERSION}/warehouses",
    "channels": f"/{API_VERSION}/channels",
    "return_orders": f"/{API_VERSION}/return_orders",
    "promotions": f"/{API_VERSION}/promotions",
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
