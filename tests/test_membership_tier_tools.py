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
