"""
會員點數規則工具端對端測試
"""
import sys
import os
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import tools.member_point_tools  # noqa: F401
from tools.member_point_tools import list_member_point_rules


if __name__ == "__main__":
    print("=" * 60)
    print("Member Point Rules Tools 端對端測試")
    print("=" * 60)

    print(f"\n{'─' * 50}")
    print(f"🔧 list_member_point_rules")
    try:
        result = list_member_point_rules()
        print(f"   total: {result.get('total')}")
        if result.get("rules"):
            print(f"   first: {result['rules'][0]}")
        print(f"   ✅ OK")
        passed = 1
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        traceback.print_exc()
        passed = 0

    print(f"\n通過: {passed}/1, 失敗: {1 - passed}/1")
