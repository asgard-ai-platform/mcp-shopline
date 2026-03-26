"""
Step 2: 深入檢查訂單與商品的資料結構
- 檢查訂單的 channel、payment、delivery、line items 等嵌套欄位
- 檢查商品的 variations、cost、brand 等欄位
- 檢查倉庫結構
"""
import sys
import os
import json
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from config.settings import get_headers, get_url


def inspect_order():
    """取得一筆訂單，詳細檢查欄位結構"""
    print("=" * 60)
    print("訂單欄位結構檢查")
    print("=" * 60)

    headers = get_headers()
    url = get_url("orders")
    resp = requests.get(url, headers=headers, params={"per_page": 3})
    data = resp.json()

    for i, order in enumerate(data["items"][:3]):
        print(f"\n--- 訂單 #{i+1}: {order.get('order_number')} ---")
        print(f"  status: {order.get('status')}")
        print(f"  channel: {json.dumps(order.get('channel'), ensure_ascii=False)}")
        print(f"  created_from: {order.get('created_from')}")
        print(f"  order_source: {json.dumps(order.get('order_source'), ensure_ascii=False)}")
        print(f"  subtotal: {json.dumps(order.get('subtotal'), ensure_ascii=False)}")
        print(f"  order_discount: {json.dumps(order.get('order_discount'), ensure_ascii=False)}")
        print(f"  total: {json.dumps(order.get('total'), ensure_ascii=False)}")
        print(f"  order_payment: {json.dumps(order.get('order_payment'), ensure_ascii=False)}")
        print(f"  order_delivery: {json.dumps(order.get('order_delivery'), ensure_ascii=False)}")
        print(f"  delivery_address: {json.dumps(order.get('delivery_address'), ensure_ascii=False)}")
        print(f"  customer_id: {order.get('customer_id')}")
        print(f"  customer_name: {order.get('customer_name')}")
        print(f"  utm_data: {json.dumps(order.get('utm_data'), ensure_ascii=False)}")
        print(f"  default_warehouse_id: {order.get('default_warehouse_id')}")
        print(f"  membership_tier_data: {json.dumps(order.get('membership_tier_data'), ensure_ascii=False)}")
        print(f"  created_at: {order.get('created_at')}")

        # subtotal_items (line items)
        items = order.get("subtotal_items", [])
        print(f"\n  subtotal_items ({len(items)} items):")
        for j, item in enumerate(items[:2]):
            print(f"    Item {j+1}: {json.dumps(item, ensure_ascii=False, indent=6)}")

        # promotion_items
        promos = order.get("promotion_items", [])
        print(f"\n  promotion_items ({len(promos)} items):")
        for p in promos[:2]:
            print(f"    {json.dumps(p, ensure_ascii=False, indent=6)}")


def inspect_product():
    """取得商品，檢查 variations、cost、brand 等"""
    print("\n" + "=" * 60)
    print("商品欄位結構檢查")
    print("=" * 60)

    headers = get_headers()
    url = get_url("products")
    resp = requests.get(url, headers=headers, params={"per_page": 3})
    data = resp.json()

    for i, prod in enumerate(data["items"][:3]):
        print(f"\n--- 商品 #{i+1}: {prod.get('title_translations', {}).get('zh-hant', '')} ---")
        print(f"  id: {prod.get('id')}")
        print(f"  sku: {prod.get('sku')}")
        print(f"  brand: {prod.get('brand')}")
        print(f"  supplier: {json.dumps(prod.get('supplier'), ensure_ascii=False)}")
        print(f"  cost: {json.dumps(prod.get('cost'), ensure_ascii=False)}")
        print(f"  price: {json.dumps(prod.get('price'), ensure_ascii=False)}")
        print(f"  price_sale: {json.dumps(prod.get('price_sale'), ensure_ascii=False)}")
        print(f"  quantity: {prod.get('quantity')}")
        print(f"  category_ids: {prod.get('category_ids')}")
        print(f"  tags: {prod.get('tags')}")
        print(f"  field_titles: {json.dumps(prod.get('field_titles'), ensure_ascii=False)}")

        # variations
        variations = prod.get("variations", [])
        print(f"\n  variations ({len(variations)} variants):")
        for v in variations[:3]:
            print(f"    {json.dumps(v, ensure_ascii=False, indent=6)}")

        # variant_options
        print(f"  variant_options: {json.dumps(prod.get('variant_options'), ensure_ascii=False)}")


def inspect_warehouses():
    """取得倉庫列表"""
    print("\n" + "=" * 60)
    print("倉庫列表")
    print("=" * 60)

    headers = get_headers()
    url = get_url("warehouses")
    resp = requests.get(url, headers=headers, params={"per_page": 50})
    data = resp.json()

    for w in data.get("items", []):
        print(f"  {w.get('id')} | {w.get('name')} | status: {w.get('status')}")


def inspect_product_stocks(product_id):
    """取得特定商品的各倉庫庫存"""
    print("\n" + "=" * 60)
    print(f"商品庫存（product_id: {product_id}）")
    print("=" * 60)

    headers = get_headers()
    url = get_url("product_stocks", product_id=product_id)
    resp = requests.get(url, headers=headers)
    print(f"  Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"  Response: {json.dumps(data, ensure_ascii=False, indent=4)[:2000]}")
    else:
        print(f"  Error: {resp.text[:500]}")


def inspect_order_search_filters():
    """測試 Orders Search 的各種篩選條件"""
    print("\n" + "=" * 60)
    print("Orders Search 篩選測試")
    print("=" * 60)

    headers = get_headers()
    url = get_url("orders_search")

    # 測試依狀態篩選
    for status in ["completed", "pending", "confirmed", "cancelled"]:
        resp = requests.get(url, headers=headers, params={"per_page": 1, "status": status})
        if resp.status_code == 200:
            count = resp.json().get("pagination", {}).get("total_count", "?")
            print(f"  status={status}: {count} orders")
        else:
            print(f"  status={status}: HTTP {resp.status_code}")

    # 測試依日期篩選
    resp = requests.get(url, headers=headers, params={
        "per_page": 1,
        "created_after": "2025-01-01T00:00:00Z",
        "created_before": "2025-12-31T23:59:59Z",
    })
    if resp.status_code == 200:
        count = resp.json().get("pagination", {}).get("total_count", "?")
        print(f"  2025 年度訂單: {count} orders")


if __name__ == "__main__":
    inspect_order()
    inspect_product()
    inspect_warehouses()

    # 用第一個商品 ID 測試庫存
    headers = get_headers()
    resp = requests.get(get_url("products"), headers=headers, params={"per_page": 1})
    if resp.status_code == 200:
        pid = resp.json()["items"][0]["id"]
        inspect_product_stocks(pid)

    inspect_order_search_filters()
