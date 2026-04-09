"""
商品評價工具端對端測試 — 驗證 Product Review API & 工具可正常呼叫
"""
import sys
import os
import json
import inspect
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import tools.review_tools  # noqa: F401
from tools.review_tools import list_product_reviews, get_product_review_detail
from pydantic.fields import FieldInfo


def run_test(name, fn, **kwargs):
    print(f"\n{'─' * 50}")
    print(f"🔧 {name}")
    sig = inspect.signature(fn)
    for pn, p in sig.parameters.items():
        if pn not in kwargs and isinstance(p.default, FieldInfo):
            kwargs[pn] = p.default.default
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
    print("Review Tools 端對端測試")
    print("=" * 60)

    results = {}

    results["list_product_reviews"] = run_test(
        "list_product_reviews", list_product_reviews, max_results=5
    )

    # get_product_review_detail: get id from list, skip if empty
    try:
        from tools.base_tool import api_get
        review_data = api_get("product_review_comments", params={"per_page": 1})
        items = review_data.get("items", [])
        if items:
            comment_id = str(items[0]["id"])
            results["get_product_review_detail"] = run_test(
                "get_product_review_detail", get_product_review_detail,
                comment_id=comment_id
            )
        else:
            print("\n⚠️ 無評價資料可測試 get_product_review_detail")
            results["get_product_review_detail"] = False
    except Exception as e:
        print(f"\n❌ 無法取得評價列表: {e}")
        traceback.print_exc()
        results["get_product_review_detail"] = False

    print("\n" + "=" * 60)
    print("Review Tools 測試結果")
    print("=" * 60)
    passed = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)
    for name, ok in results.items():
        icon = "✅" if ok else "❌"
        print(f"  {icon} {name}")

    print(f"\n通過: {passed}/{len(results)}, 失敗: {failed}/{len(results)}")
