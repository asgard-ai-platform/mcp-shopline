"""
客戶寫入工具端對端測試 — 需設定 SHOPLINE_TEST_WRITES=1 才會執行

⚠️ 此測試會在正式帳號上建立/修改/刪除客戶資料
"""
import sys
import os
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# Gate: 預設 skip
if os.environ.get("SHOPLINE_TEST_WRITES", "").lower() not in ("1", "true", "yes"):
    print("⚠ Customer write tests skipped. Set SHOPLINE_TEST_WRITES=1 to run.")
    sys.exit(0)

import tools.writes.customer_writes  # noqa: F401
from tools.writes.customer_writes import (
    create_customer, update_customer, delete_customer,
    update_customer_tags, update_customer_store_credits,
    adjust_customer_member_points,
)


if __name__ == "__main__":
    print("=" * 60)
    print("Customer Write Tools 端對端測試")
    print("⚠️  此測試會修改正式資料")
    print("=" * 60)

    results = {}
    test_customer_id = None

    print(f"\n{'─' * 50}")
    print(f"🔧 create_customer")
    try:
        result = create_customer(
            name="MCP 測試客戶",
            email="mcp-test@example.com",
            phone="0900000000",
            tags=["mcp-test"],
        )
        print(f"   success: {result['success']}")
        print(f"   resource_id: {result['resource_id']}")
        test_customer_id = result["resource_id"]
        print(f"   ✅ OK")
        results["create_customer"] = True
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        traceback.print_exc()
        results["create_customer"] = False

    if test_customer_id:
        print(f"\n{'─' * 50}")
        print(f"🔧 update_customer")
        try:
            result = update_customer(customer_id=test_customer_id, name="MCP 測試客戶 (已更新)")
            print(f"   success: {result['success']}")
            print(f"   ✅ OK")
            results["update_customer"] = True
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            traceback.print_exc()
            results["update_customer"] = False

        print(f"\n{'─' * 50}")
        print(f"🔧 update_customer_tags")
        try:
            result = update_customer_tags(customer_id=test_customer_id, tags=["mcp-test", "vip"])
            print(f"   success: {result['success']}")
            print(f"   ✅ OK")
            results["update_customer_tags"] = True
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            traceback.print_exc()
            results["update_customer_tags"] = False

        print(f"\n{'─' * 50}")
        print(f"🔧 delete_customer (cleanup)")
        try:
            result = delete_customer(customer_id=test_customer_id)
            print(f"   success: {result['success']}")
            print(f"   ✅ OK")
            results["delete_customer"] = True
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            traceback.print_exc()
            results["delete_customer"] = False

    print("\n" + "=" * 60)
    print("Customer Write Tools 測試結果")
    print("=" * 60)
    passed = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)
    for name, ok in results.items():
        print(f"  {'✅' if ok else '❌'} {name}")
    print(f"\n通過: {passed}/{len(results)}, 失敗: {failed}/{len(results)}")
