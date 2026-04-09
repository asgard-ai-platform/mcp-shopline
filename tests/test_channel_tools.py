"""
銷售渠道工具端對端測試
"""
import sys
import os
import inspect
import json
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import tools.channel_tools  # noqa: F401
from tools.channel_tools import list_channels, get_channel_detail


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
    print("Channel Tools 端對端測試")
    print("=" * 60)
    print("注意：渠道端點在部分 token 下可能回傳 403/422")

    results = {}

    results["list_channels"] = run_test("list_channels", list_channels)

    # get id from list; skip if empty or list call failed
    try:
        list_result = list_channels()
        channels = list_result.get("channels", [])
        if channels:
            cid = channels[0]["id"]
            results["get_channel_detail"] = run_test(
                "get_channel_detail", get_channel_detail, channel_id=cid
            )
        else:
            print("\n⚠️ 無渠道資料可測試 get_channel_detail（可能為 403/422 或空列表）")
            results["get_channel_detail"] = False
    except Exception as e:
        print(f"\n⚠️ 無法取得渠道列表（可能權限不足）: {e}")
        results["get_channel_detail"] = False

    print("\n" + "=" * 60)
    passed = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)
    for name, ok in results.items():
        print(f"  {'✅' if ok else '❌'} {name}")
    print(f"\n通過: {passed}/{len(results)}, 失敗: {failed}/{len(results)}")
    if failed > 0:
        print("\n⚠️  Channel API 常見回傳 403/422，屬正常現象，渠道資訊可從訂單 channel 欄位取得")
