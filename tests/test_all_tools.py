"""
端對端測試 — 驗證所有 Tools 可正常呼叫 Shopline API 並回傳結果
"""
import sys
import os
import json
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.tool_registry import execute_tool, list_tools


def run_test(name, **kwargs):
    """執行一個 Tool 並印出結果摘要"""
    print(f"\n{'─' * 50}")
    print(f"🔧 {name}")
    print(f"   params: {kwargs}")
    try:
        result = execute_tool(name, **kwargs)
        if "error" in result and result["error"]:
            print(f"   ❌ Error: {result['error']}")
            return False

        # 印出 key-level 摘要
        for k, v in result.items():
            if isinstance(v, list):
                print(f"   {k}: [{len(v)} items]")
                if v and len(v) > 0:
                    first = v[0]
                    if isinstance(first, dict):
                        print(f"     first: {json.dumps(first, ensure_ascii=False)[:200]}")
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
    print("Shopline API Tools 端對端測試")
    print("=" * 60)

    tools = list_tools()
    print(f"共 {len(tools)} 個 Tools 待測試\n")

    results = {}

    # --- 訂單類 ---
    results["query_orders"] = run_test(
        "query_orders",
        start_date="2026-03-01", end_date="2026-03-19",
        status="completed", channel="all", max_results=5
    )

    results["get_sales_summary"] = run_test(
        "get_sales_summary",
        start_date="2026-03-01", end_date="2026-03-19",
        status="completed", channel="all"
    )

    results["get_top_products"] = run_test(
        "get_top_products",
        start_date="2026-03-01", end_date="2026-03-19",
        top_n=5, sort_by="revenue"
    )

    results["get_sales_trend"] = run_test(
        "get_sales_trend",
        start_date="2026-03-01", end_date="2026-03-19",
        granularity="daily"
    )

    results["get_channel_comparison"] = run_test(
        "get_channel_comparison",
        start_date="2026-03-01", end_date="2026-03-19"
    )

    # 取一筆訂單 ID 來測試 detail
    from tools.base_tool import api_get
    first_order = api_get("orders", params={"per_page": 1, "status": "completed"})
    oid = first_order["items"][0]["id"]
    results["get_order_detail"] = run_test(
        "get_order_detail", order_id=oid
    )

    # --- 商品類 ---
    results["get_product_list"] = run_test(
        "get_product_list", max_results=5
    )

    # 取第一個有 variations 的商品
    from tools.base_tool import fetch_all_pages
    prods = fetch_all_pages("products", max_pages=1)
    prod_with_vars = None
    for p in prods:
        if p.get("variations") and len(p["variations"]) > 0:
            prod_with_vars = p["id"]
            break
    if prod_with_vars:
        results["get_product_variants"] = run_test(
            "get_product_variants", product_id=prod_with_vars
        )
    else:
        print("\n⚠️ 無可測試的商品變體")
        results["get_product_variants"] = False

    results["get_inventory_overview"] = run_test(
        "get_inventory_overview"
    )

    results["get_low_stock_alerts"] = run_test(
        "get_low_stock_alerts", threshold=3
    )

    results["get_warehouses"] = run_test(
        "get_warehouses"
    )

    # --- 分析類 ---
    results["get_rfm_analysis"] = run_test(
        "get_rfm_analysis",
        start_date="2026-01-01", end_date="2026-03-19"
    )

    results["get_repurchase_analysis"] = run_test(
        "get_repurchase_analysis",
        start_date="2026-01-01", end_date="2026-03-19"
    )

    results["get_customer_geo_analysis"] = run_test(
        "get_customer_geo_analysis",
        start_date="2026-03-01", end_date="2026-03-19"
    )

    results["get_inventory_turnover"] = run_test(
        "get_inventory_turnover",
        start_date="2026-03-01", end_date="2026-03-19"
    )

    # --- 新增 Tools (Combo 用) ---
    results["get_refund_summary"] = run_test(
        "get_refund_summary",
        start_date="2026-03-01", end_date="2026-03-24"
    )

    results["get_stock_by_warehouse"] = run_test(
        "get_stock_by_warehouse",
        product_id=prod_with_vars  # 用前面找到的有 variations 的商品
    )

    results["get_category_sales"] = run_test(
        "get_category_sales",
        start_date="2026-03-01", end_date="2026-03-19"
    )

    results["get_promotion_analysis"] = run_test(
        "get_promotion_analysis",
        status="all"
    )

    # --- 總結 ---
    print("\n" + "=" * 60)
    print("測試結果總結")
    print("=" * 60)
    passed = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)
    for name, ok in results.items():
        icon = "✅" if ok else "❌"
        print(f"  {icon} {name}")

    print(f"\n通過: {passed}/{len(results)}, 失敗: {failed}/{len(results)}")
