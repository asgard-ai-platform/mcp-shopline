"""
配送方式工具端對端測試
"""
import sys
import os
import inspect
import json
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import tools.delivery_option_tools  # noqa: F401
from tools.delivery_option_tools import (
    list_delivery_options,
    get_delivery_option_detail,
    get_delivery_time_slots,
)


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
    print("Delivery Option Tools 端對端測試")
    print("=" * 60)

    results = {}

    results["list_delivery_options"] = run_test(
        "list_delivery_options", list_delivery_options
    )

    # get id from list; skip if empty
    try:
        list_result = list_delivery_options()
        options = list_result.get("delivery_options", [])
        if options:
            did = options[0]["id"]
            results["get_delivery_option_detail"] = run_test(
                "get_delivery_option_detail",
                get_delivery_option_detail,
                delivery_option_id=did,
            )
            results["get_delivery_time_slots"] = run_test(
                "get_delivery_time_slots",
                get_delivery_time_slots,
                delivery_option_id=did,
            )
        else:
            print("\n⚠️ 無配送方式資料可測試 get_delivery_option_detail / get_delivery_time_slots")
            results["get_delivery_option_detail"] = False
            results["get_delivery_time_slots"] = False
    except Exception as e:
        print(f"\n❌ 無法取得配送方式列表: {e}")
        traceback.print_exc()
        results["get_delivery_option_detail"] = False
        results["get_delivery_time_slots"] = False

    print("\n" + "=" * 60)
    passed = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)
    for name, ok in results.items():
        print(f"  {'✅' if ok else '❌'} {name}")
    print(f"\n通過: {passed}/{len(results)}, 失敗: {failed}/{len(results)}")
