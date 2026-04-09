"""
客戶儲值金工具端對端測試
"""
import sys
import os
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import tools.store_credit_tools  # noqa: F401
from tools.store_credit_tools import list_store_credits


if __name__ == "__main__":
    print("=" * 60)
    print("Store Credit Tools 端對端測試")
    print("=" * 60)

    print(f"\n{'─' * 50}")
    print(f"🔧 list_store_credits")
    try:
        result = list_store_credits(max_results=5)
        print(f"   total_found: {result.get('total_found')}")
        print(f"   returned: {result.get('returned')}")
        print(f"   total_balance: {result.get('total_balance')}")
        if result.get("credits"):
            print(f"   first: {result['credits'][0]}")
        print(f"   ✅ OK")
        passed = 1
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        traceback.print_exc()
        passed = 0

    print(f"\n通過: {passed}/1, 失敗: {1 - passed}/1")
