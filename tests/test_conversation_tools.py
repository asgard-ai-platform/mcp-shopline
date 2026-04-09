"""
對話工具端對端測試 — 驗證 Conversation API & 工具可正常呼叫
"""
import sys
import os
import json
import inspect
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import tools.conversation_tools  # noqa: F401
from tools.conversation_tools import list_conversations, get_conversation_messages
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
    print("Conversation Tools 端對端測試")
    print("=" * 60)

    results = {}

    results["list_conversations"] = run_test(
        "list_conversations", list_conversations, max_results=5
    )

    # get_conversation_messages: get id from list, skip if empty
    try:
        from tools.base_tool import api_get
        conv_data = api_get("conversations", params={"per_page": 1})
        items = conv_data.get("items", [])
        if items:
            conv_id = str(items[0]["id"])
            results["get_conversation_messages"] = run_test(
                "get_conversation_messages", get_conversation_messages,
                conversation_id=conv_id, max_results=5
            )
        else:
            print("\n⚠️ 無對話資料可測試 get_conversation_messages")
            results["get_conversation_messages"] = False
    except Exception as e:
        print(f"\n❌ 無法取得對話列表: {e}")
        traceback.print_exc()
        results["get_conversation_messages"] = False

    print("\n" + "=" * 60)
    print("Conversation Tools 測試結果")
    print("=" * 60)
    passed = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)
    for name, ok in results.items():
        icon = "✅" if ok else "❌"
        print(f"  {icon} {name}")

    print(f"\n通過: {passed}/{len(results)}, 失敗: {failed}/{len(results)}")

    if failed > 0:
        print("\n⚠️  如果 Conversation API 回 403，請確認 Shopline API token 已授予對話資料權限")
