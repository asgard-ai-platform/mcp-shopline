"""
自訂欄位工具端對端測試
"""
import sys
import os
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import tools.custom_field_tools  # noqa: F401
from tools.custom_field_tools import list_custom_fields


if __name__ == "__main__":
    print("=" * 60)
    print("Custom Field Tools 端對端測試")
    print("=" * 60)

    print(f"\n{'─' * 50}")
    print(f"🔧 list_custom_fields")
    try:
        result = list_custom_fields()
        print(f"   total: {result.get('total')}")
        if result.get("fields"):
            print(f"   first: {result['fields'][0]}")
        print(f"   ✅ OK")
        passed = 1
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        traceback.print_exc()
        passed = 0

    print(f"\n通過: {passed}/1, 失敗: {1 - passed}/1")
