"""
Step 1: API 連線驗證
- 測試 Token 有效性
- 確認基本端點可存取
- 探測 Rate Limit 資訊
"""
import sys
import os
import json
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from config.settings import get_headers, get_url


def test_connection():
    """測試 API 連線與 Token 有效性"""
    print("=" * 60)
    print("Step 1: API 連線驗證")
    print("=" * 60)

    url = get_url("orders")
    params = {"per_page": 1}
    headers = get_headers()

    print(f"\n[1] 測試端點: GET {url}")
    print(f"    Token: ...{headers['Authorization'][-10:]}")

    resp = requests.get(url, headers=headers, params=params)

    print(f"    Status: {resp.status_code}")
    print(f"    Rate Limit Headers:")
    for key, val in resp.headers.items():
        if "rate" in key.lower() or "limit" in key.lower() or "retry" in key.lower():
            print(f"      {key}: {val}")

    if resp.status_code == 200:
        data = resp.json()
        print(f"\n    ✅ 連線成功!")
        if "pagination" in data:
            print(f"    Pagination: {json.dumps(data['pagination'], indent=6)}")
        if "items" in data and len(data["items"]) > 0:
            print(f"    第一筆訂單 keys: {list(data['items'][0].keys())}")
    else:
        print(f"\n    ❌ 連線失敗!")
        print(f"    Response: {resp.text[:500]}")
        return False

    return True


def test_endpoints():
    """測試各主要端點是否可存取"""
    print("\n" + "=" * 60)
    print("Step 1.1: 各端點可存取性測試")
    print("=" * 60)

    headers = get_headers()
    endpoints = {
        "Orders": get_url("orders"),
        "Products": get_url("products"),
        "Categories": get_url("categories"),
        "Customers": get_url("customers"),
        "Warehouses": get_url("warehouses"),
        "Channels": get_url("channels"),
        "Return Orders": get_url("return_orders"),
        "Promotions": get_url("promotions"),
    }

    results = {}
    for name, url in endpoints.items():
        resp = requests.get(url, headers=headers, params={"per_page": 1})
        status = resp.status_code
        count = None
        sample_keys = None

        if status == 200:
            data = resp.json()
            if "pagination" in data:
                count = data["pagination"].get("total_count")
            if "items" in data and len(data["items"]) > 0:
                sample_keys = list(data["items"][0].keys())

        icon = "✅" if status == 200 else "❌"
        print(f"\n  {icon} {name}: {status}")
        print(f"     URL: {url}")
        if count is not None:
            print(f"     Total records: {count}")
        if sample_keys:
            print(f"     Fields: {sample_keys}")

        results[name] = {
            "status": status,
            "total_count": count,
            "sample_keys": sample_keys,
        }

    return results


if __name__ == "__main__":
    ok = test_connection()
    if ok:
        results = test_endpoints()
        print("\n" + "=" * 60)
        print("總結")
        print("=" * 60)
        for name, info in results.items():
            icon = "✅" if info["status"] == 200 else "❌"
            count_str = f" ({info['total_count']} records)" if info["total_count"] is not None else ""
            print(f"  {icon} {name}: HTTP {info['status']}{count_str}")
