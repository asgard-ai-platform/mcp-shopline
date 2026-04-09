"""
分類工具端對端測試
"""
import sys
import os
import json
import traceback
import inspect
from pydantic.fields import FieldInfo

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import tools.category_tools  # noqa: F401
from tools.category_tools import get_category_tree, get_category_detail


def run_test(name, fn, **kwargs):
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
    print("Category Tools 端對端測試")
    print("=" * 60)

    results = {}

    results["get_category_tree"] = run_test(
        "get_category_tree", get_category_tree
    )

    # get_category_detail: derive category_id from tree result
    try:
        tree_data = get_category_tree()
        flat = tree_data.get("flat", [])
        if flat:
            cid = flat[0]["id"]
            results["get_category_detail"] = run_test(
                "get_category_detail", get_category_detail, category_id=cid
            )
        else:
            print("\n⚠️ 無分類資料可測試 get_category_detail")
            results["get_category_detail"] = False
    except Exception as e:
        print(f"\n❌ 無法取得分類列表: {e}")
        traceback.print_exc()
        results["get_category_detail"] = False

    print("\n" + "=" * 60)
    print("Category Tools 測試結果")
    print("=" * 60)
    passed = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)
    for name, ok in results.items():
        icon = "✅" if ok else "❌"
        print(f"  {icon} {name}")

    print(f"\n通過: {passed}/{len(results)}, 失敗: {failed}/{len(results)}")
