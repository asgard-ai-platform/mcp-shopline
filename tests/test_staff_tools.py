"""
員工工具端對端測試
"""
import sys
import os
import inspect
import json
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import tools.staff_tools  # noqa: F401
from tools.staff_tools import get_staff_permissions


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
    print("Staff Tools 端對端測試")
    print("=" * 60)

    results = {}

    # Try to get a staff_id from the merchant info (token_info may carry staff/owner id).
    # Fall back to trying a well-known test value; skip gracefully on 404/403.
    staff_id = None

    try:
        from tools.base_tool import api_get
        # token_info often includes the staff/owner id
        token_data = api_get("token_info")
        info = token_data.get("token_info", token_data) if isinstance(token_data, dict) else {}
        staff_id = (
            info.get("staff_id")
            or info.get("owner_id")
            or info.get("id")
        )
    except Exception as e:
        print(f"\n⚠️ 無法從 token_info 取得 staff_id: {e}")

    if staff_id:
        results["get_staff_permissions"] = run_test(
            "get_staff_permissions", get_staff_permissions, staff_id=str(staff_id)
        )
    else:
        print("\n⚠️ 無法取得 staff_id，嘗試使用預設測試值 '1'")
        try:
            results["get_staff_permissions"] = run_test(
                "get_staff_permissions", get_staff_permissions, staff_id="1"
            )
        except Exception as e:
            print(f"   ⚠️ 使用預設值也失敗，跳過此測試: {e}")
            results["get_staff_permissions"] = False

    print("\n" + "=" * 60)
    passed = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)
    for name, ok in results.items():
        print(f"  {'✅' if ok else '❌'} {name}")
    print(f"\n通過: {passed}/{len(results)}, 失敗: {failed}/{len(results)}")
    if failed > 0:
        print("\n⚠️  若回傳 403/404，請確認 staff_id 正確或 token 已授予員工權限")
