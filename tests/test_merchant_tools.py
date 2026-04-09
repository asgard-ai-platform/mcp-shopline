"""
商家工具端對端測試
"""
import sys
import os
import inspect
import json
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import tools.merchant_tools  # noqa: F401
from tools.merchant_tools import list_merchants, get_merchant_detail


def run_test(name, fn, **kwargs):
    import inspect
    from pydantic.fields import FieldInfo
    sig = inspect.signature(fn)
    for pn, p in sig.parameters.items():
        if pn not in kwargs and isinstance(p.default, FieldInfo):
            kwargs[pn] = p.default.default

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
    print("Merchant Tools 端對端測試")
    print("=" * 60)

    results = {}

    results["list_merchants"] = run_test("list_merchants", list_merchants)

    # get_merchant_detail: get id from list
    try:
        list_result = list_merchants()
        merchants = list_result.get("merchants", [])
        if merchants:
            mid = merchants[0]["id"]
            results["get_merchant_detail"] = run_test(
                "get_merchant_detail", get_merchant_detail, merchant_id=mid
            )
        else:
            print("\n⚠️ 無商家資料可測試 get_merchant_detail")
            results["get_merchant_detail"] = False
    except Exception as e:
        print(f"\n❌ 無法取得商家列表: {e}")
        traceback.print_exc()
        results["get_merchant_detail"] = False

    print("\n" + "=" * 60)
    passed = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)
    for name, ok in results.items():
        print(f"  {'✅' if ok else '❌'} {name}")
    print(f"\n通過: {passed}/{len(results)}, 失敗: {failed}/{len(results)}")
