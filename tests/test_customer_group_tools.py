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

    print("\n" + "=" * 60)
    passed = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)
    for name, ok in results.items():
        print(f"  {'✅' if ok else '❌'} {name}")
    print(f"\n通過: {passed}/{len(results)}, 失敗: {failed}/{len(results)}")
