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

    results["list_customers"] = run_test(
        "list_customers", list_customers, max_results=5
    )

    results["list_customers_search"] = run_test(
        "list_customers (search)", list_customers,
        search_keyword="test", max_results=5
    )

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
