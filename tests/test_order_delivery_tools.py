"""
訂單配送工具端對端測試 — 驗證 Order Delivery API & 工具可正常呼叫
"""
import sys
import os
import json
import inspect
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import tools.order_delivery_tools  # noqa: F401
from tools.order_delivery_tools import get_order_delivery
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
    print("Order Delivery Tools 端對端測試")
    print("=" * 60)

    results = {}

    # get_order_delivery: get delivery_id from first order
    try:
        from tools.base_tool import api_get
        order_data = api_get("orders", params={"per_page": 1})
        orders = order_data.get("items", [])
        if orders:
            order = orders[0]
            # delivery id may be in order_delivery or deliveries
            delivery_id = None
            order_delivery = order.get("order_delivery") or {}
            if order_delivery.get("id"):
                delivery_id = str(order_delivery["id"])
            elif order.get("deliveries"):
                delivery_id = str(order["deliveries"][0]["id"])

            if delivery_id:
                results["get_order_delivery"] = run_test(
                    "get_order_delivery", get_order_delivery,
                    delivery_id=delivery_id
                )
            else:
                print("\n⚠️ 訂單無配送單 ID，略過 get_order_delivery")
                results["get_order_delivery"] = False
        else:
            print("\n⚠️ 無訂單資料可測試 get_order_delivery")
            results["get_order_delivery"] = False
    except Exception as e:
        print(f"\n❌ 無法取得訂單資料: {e}")
        traceback.print_exc()
        results["get_order_delivery"] = False

    print("\n" + "=" * 60)
    print("Order Delivery Tools 測試結果")
    print("=" * 60)
    passed = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)
    for name, ok in results.items():
        icon = "✅" if ok else "❌"
        print(f"  {icon} {name}")

    print(f"\n通過: {passed}/{len(results)}, 失敗: {failed}/{len(results)}")
