"""
數據分析計算 Tools — RFM 分群、回購率、庫存周轉等需合併多 API 的分析
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import Optional, Literal
from pydantic import Field

from app import mcp
from tools.base_tool import (
    api_get, fetch_all_pages, money_to_float, get_translation
)
from collections import defaultdict
from datetime import datetime

VALID_ORDER_STATUSES = {"completed", "confirmed"}


# ============================================================
# Tool 1: get_rfm_analysis — RFM 分群分析
# ============================================================
@mcp.tool()
def get_rfm_analysis(
    start_date: str = Field(description="分析區間起始 YYYY-MM-DD"),
    end_date: str = Field(description="分析區間結束 YYYY-MM-DD"),
    r_days_threshold: int = Field(default=30, description="Recency 門檻天數（最近消費 ≤ 此值為高 R）"),
    f_threshold: int = Field(default=2, description="Frequency 門檻（消費 ≥ 此值為高 F）"),
    m_threshold: float = Field(default=5000, description="Monetary 門檻金額（累計 ≥ 此值為高 M）"),
) -> dict:
    """根據訂單資料進行 RFM（Recency/Frequency/Monetary）分群分析。注意：僅能分析有下單紀錄的客戶（Customers API 為 403）。"""
    params = {
        "created_after": f"{start_date}T00:00:00Z",
        "created_before": f"{end_date}T23:59:59Z",
    }
    orders = fetch_all_pages("orders_search", params=params, max_pages=200)
    orders = [o for o in orders if o.get("status") in VALID_ORDER_STATUSES]

    # 依 customer_id 彙總
    now = datetime.fromisoformat(f"{end_date}T23:59:59+00:00")
    customers = defaultdict(lambda: {
        "name": "", "orders": [], "total_spent": 0.0
    })

    for o in orders:
        cid = o.get("customer_id")
        if not cid:
            continue
        customers[cid]["name"] = o.get("customer_name", "")
        created = o.get("created_at", "")
        customers[cid]["orders"].append(created)
        customers[cid]["total_spent"] += money_to_float(o.get("total"))

    # 計算 RFM
    rfm_data = []
    segment_counts = defaultdict(int)

    for cid, data in customers.items():
        dates = sorted(data["orders"])
        latest = dates[-1] if dates else ""
        if latest:
            latest_dt = datetime.fromisoformat(latest.replace("+00:00", "+00:00"))
            recency = (now - latest_dt).days
        else:
            recency = 999

        frequency = len(dates)
        monetary = data["total_spent"]

        r_high = recency <= r_days_threshold
        f_high = frequency >= f_threshold
        m_high = monetary >= m_threshold

        segment = f"{'H' if r_high else 'L'}{'H' if f_high else 'L'}{'H' if m_high else 'L'}"

        segment_labels = {
            "HHH": "最佳客戶", "HHL": "高頻低消", "HLH": "近期高消",
            "HLL": "近期新客", "LHH": "流失高價值", "LHL": "流失高頻",
            "LLH": "流失高消", "LLL": "流失低價值",
        }

        segment_counts[segment] += 1
        rfm_data.append({
            "customer_id": cid,
            "customer_name": data["name"],
            "recency_days": recency,
            "frequency": frequency,
            "monetary": round(monetary, 2),
            "segment": segment,
            "segment_label": segment_labels.get(segment, segment),
        })

    rfm_data.sort(key=lambda x: -x["monetary"])

    return {
        "period": f"{start_date} ~ {end_date}",
        "thresholds": {
            "recency_days": r_days_threshold,
            "frequency": f_threshold,
            "monetary": m_threshold,
        },
        "total_customers": len(rfm_data),
        "segment_distribution": {
            f"{seg} ({labels.get(seg, seg)})": count
            for seg, count in sorted(segment_counts.items(), key=lambda x: -x[1])
            for labels in [{"HHH": "最佳客戶", "HHL": "高頻低消", "HLH": "近期高消",
                           "HLL": "近期新客", "LHH": "流失高價值", "LHL": "流失高頻",
                           "LLH": "流失高消", "LLL": "流失低價值"}]
        },
        "top_customers": rfm_data[:20],
    }


# ============================================================
# Tool 2: get_repurchase_analysis — 回購率分析
# ============================================================
@mcp.tool()
def get_repurchase_analysis(
    start_date: str = Field(description="分析區間起始 YYYY-MM-DD"),
    end_date: str = Field(description="分析區間結束 YYYY-MM-DD"),
) -> dict:
    """分析客戶回購率與回購週期。計算新客 vs 舊客比例、回購率、平均回購天數。"""
    params = {
        "created_after": f"{start_date}T00:00:00Z",
        "created_before": f"{end_date}T23:59:59Z",
    }
    orders = fetch_all_pages("orders_search", params=params, max_pages=200)
    orders = [o for o in orders if o.get("status") in VALID_ORDER_STATUSES]

    customer_orders = defaultdict(list)
    customer_revenue = defaultdict(float)
    customer_names = {}

    for o in orders:
        cid = o.get("customer_id")
        if not cid:
            continue
        customer_orders[cid].append(o.get("created_at", ""))
        customer_revenue[cid] += money_to_float(o.get("total"))
        customer_names[cid] = o.get("customer_name", "")

    total_customers = len(customer_orders)
    new_customers = sum(1 for dates in customer_orders.values() if len(dates) == 1)
    returning_customers = total_customers - new_customers
    repurchase_rate = returning_customers / total_customers * 100 if total_customers else 0

    # 計算回購週期
    repurchase_gaps = []
    for cid, dates in customer_orders.items():
        if len(dates) < 2:
            continue
        sorted_dates = sorted(dates)
        for i in range(1, len(sorted_dates)):
            try:
                d1 = datetime.fromisoformat(sorted_dates[i - 1].replace("+00:00", "+00:00"))
                d2 = datetime.fromisoformat(sorted_dates[i].replace("+00:00", "+00:00"))
                gap = (d2 - d1).days
                if gap > 0:
                    repurchase_gaps.append(gap)
            except (ValueError, TypeError):
                continue

    avg_gap = sum(repurchase_gaps) / len(repurchase_gaps) if repurchase_gaps else 0

    new_revenue = sum(customer_revenue[cid] for cid, dates in customer_orders.items() if len(dates) == 1)
    returning_revenue = sum(customer_revenue[cid] for cid, dates in customer_orders.items() if len(dates) >= 2)

    return {
        "period": f"{start_date} ~ {end_date}",
        "total_orders": len(orders),
        "total_customers": total_customers,
        "new_customers": new_customers,
        "returning_customers": returning_customers,
        "repurchase_rate": f"{round(repurchase_rate, 1)}%",
        "avg_repurchase_days": round(avg_gap, 1),
        "median_repurchase_days": sorted(repurchase_gaps)[len(repurchase_gaps) // 2] if repurchase_gaps else 0,
        "new_customer_revenue": round(new_revenue, 2),
        "returning_customer_revenue": round(returning_revenue, 2),
        "new_customer_revenue_share": f"{round(new_revenue / (new_revenue + returning_revenue) * 100, 1)}%" if (new_revenue + returning_revenue) else "0%",
        "returning_customer_revenue_share": f"{round(returning_revenue / (new_revenue + returning_revenue) * 100, 1)}%" if (new_revenue + returning_revenue) else "0%",
    }


# ============================================================
# Tool 3: get_customer_geo_analysis — 客戶地區分析
# ============================================================
@mcp.tool()
def get_customer_geo_analysis(
    start_date: str = Field(description="分析區間起始 YYYY-MM-DD"),
    end_date: str = Field(description="分析區間結束 YYYY-MM-DD"),
    channel: Literal["online", "pos", "all"] = Field(default="all", description="通路篩選"),
) -> dict:
    """根據訂單的收件地址分析客戶地區分佈（縣市層級）。"""
    params = {
        "created_after": f"{start_date}T00:00:00Z",
        "created_before": f"{end_date}T23:59:59Z",
    }
    orders = fetch_all_pages("orders_search", params=params, max_pages=200)
    orders = [o for o in orders if o.get("status") in VALID_ORDER_STATUSES]

    if channel == "online":
        orders = [o for o in orders if o.get("created_from") == "shop"]
    elif channel == "pos":
        orders = [o for o in orders if o.get("created_from") == "pos"]

    city_stats = defaultdict(lambda: {"orders": 0, "revenue": 0.0, "customers": set()})

    for o in orders:
        addr = o.get("delivery_address") or {}
        city = addr.get("city") or "未填寫"
        revenue = money_to_float(o.get("total"))
        cid = o.get("customer_id", "")

        city_stats[city]["orders"] += 1
        city_stats[city]["revenue"] += revenue
        if cid:
            city_stats[city]["customers"].add(cid)

    total_orders = sum(c["orders"] for c in city_stats.values())
    result = []
    for city, data in sorted(city_stats.items(), key=lambda x: -x[1]["orders"]):
        result.append({
            "city": city,
            "orders": data["orders"],
            "revenue": round(data["revenue"], 2),
            "unique_customers": len(data["customers"]),
            "order_share": f"{round(data['orders'] / total_orders * 100, 1)}%" if total_orders else "0%",
        })

    return {
        "period": f"{start_date} ~ {end_date}",
        "total_orders": total_orders,
        "total_cities": len(result),
        "cities": result,
    }


# ============================================================
# Tool 4: get_inventory_turnover — 庫存周轉分析
# ============================================================
@mcp.tool()
def get_inventory_turnover(
    start_date: str = Field(description="分析區間起始 YYYY-MM-DD"),
    end_date: str = Field(description="分析區間結束 YYYY-MM-DD"),
) -> dict:
    """計算庫存周轉指標：周轉天數、周轉率。需要商品庫存 + 銷售數據。"""
    # 取得商品庫存
    products = fetch_all_pages("products", max_pages=10)

    # 取得銷售數據
    params = {
        "created_after": f"{start_date}T00:00:00Z",
        "created_before": f"{end_date}T23:59:59Z",
    }
    orders = fetch_all_pages("orders_search", params=params, max_pages=200)
    orders = [o for o in orders if o.get("status") in VALID_ORDER_STATUSES]

    # 計算天數
    d1 = datetime.strptime(start_date, "%Y-%m-%d")
    d2 = datetime.strptime(end_date, "%Y-%m-%d")
    period_days = (d2 - d1).days or 1

    # 依商品 ID 彙總銷售
    sales_by_product = defaultdict(lambda: {"qty": 0, "revenue": 0.0})
    for o in orders:
        for item in o.get("subtotal_items", []):
            pid = item.get("item_id", "")
            sales_by_product[pid]["qty"] += item.get("quantity", 1)
            sales_by_product[pid]["revenue"] += money_to_float(item.get("total"))

    # 依商品計算周轉
    product_turnover = []
    for p in products:
        pid = p.get("id")
        title = get_translation(p.get("title_translations"))
        variations = p.get("variations", [])
        current_stock = sum(v.get("quantity", 0) or 0 for v in variations)
        if not variations:
            current_stock = p.get("quantity", 0) or 0

        sales = sales_by_product.get(pid, {"qty": 0, "revenue": 0.0})
        daily_sales = sales["qty"] / period_days if period_days else 0

        days_of_stock = current_stock / daily_sales if daily_sales > 0 else float("inf")
        turnover_rate = sales["qty"] / current_stock if current_stock > 0 else float("inf")

        product_turnover.append({
            "title": title,
            "product_id": pid,
            "current_stock": current_stock,
            "period_sales_qty": sales["qty"],
            "period_sales_revenue": round(sales["revenue"], 2),
            "daily_sales_rate": round(daily_sales, 2),
            "estimated_days_of_stock": round(days_of_stock, 1) if days_of_stock != float("inf") else "無銷售",
            "turnover_rate": round(turnover_rate, 2) if turnover_rate != float("inf") else "無庫存",
        })

    # 排序：周轉天數最短的排前面（健康度高）
    product_turnover.sort(
        key=lambda x: x["estimated_days_of_stock"] if isinstance(x["estimated_days_of_stock"], (int, float)) else 99999
    )

    return {
        "period": f"{start_date} ~ {end_date}",
        "period_days": period_days,
        "total_products": len(product_turnover),
        "products": product_turnover,
    }


# ============================================================
# Tool 5: get_category_sales — 商品分類銷售分析
# ============================================================
@mcp.tool()
def get_category_sales(
    start_date: str = Field(description="起始日期 YYYY-MM-DD"),
    end_date: str = Field(description="結束日期 YYYY-MM-DD"),
    channel: Literal["online", "pos", "all"] = Field(default="all", description="通路篩選"),
) -> dict:
    """依商品分類（Category）彙總銷售數據：各分類的營業額、銷量、商品數。需交叉 Categories API + Products + Orders。"""
    from tools.base_tool import api_get

    # Step 1: 取得分類結構
    cat_data = api_get("categories", params={"per_page": 50})
    categories = cat_data.get("items", [])

    # 建立 category_id → name 對照（含子分類）
    cat_map = {}
    for c in categories:
        cid = c.get("id")
        cname = get_translation(c.get("name_translations"))
        cat_map[cid] = cname
        for child in c.get("children", []):
            cat_map[child.get("id")] = get_translation(child.get("name_translations"))

    # Step 2: 取得商品列表，建立 product_id → category 對照
    products = fetch_all_pages("products", max_pages=10)
    product_categories = {}  # product_id → [category_names]
    for p in products:
        pid = p.get("id")
        cat_ids = p.get("category_ids", [])
        cat_names = [cat_map.get(cid, "未分類") for cid in cat_ids]
        if not cat_names:
            cat_names = ["未分類"]
        product_categories[pid] = cat_names

    # 也建立 sku → product_id 對照
    sku_to_pid = {}
    for p in products:
        pid = p.get("id")
        for v in p.get("variations", []):
            sku = v.get("sku", "")
            if sku:
                sku_to_pid[sku] = pid

    # Step 3: 取得訂單，彙總到分類
    params = {
        "created_after": f"{start_date}T00:00:00Z",
        "created_before": f"{end_date}T23:59:59Z",
    }
    orders = fetch_all_pages("orders_search", params=params, max_pages=200)
    orders = [o for o in orders if o.get("status") in VALID_ORDER_STATUSES]

    if channel == "online":
        orders = [o for o in orders if o.get("created_from") == "shop"]
    elif channel == "pos":
        orders = [o for o in orders if o.get("created_from") == "pos"]

    cat_stats = defaultdict(lambda: {
        "revenue": 0.0, "quantity": 0, "orders": set(), "products": set()
    })

    for o in orders:
        oid = o.get("id", "")
        for item in o.get("subtotal_items", []):
            sku = item.get("sku", "")
            item_id = item.get("item_id", "")
            qty = item.get("quantity", 1)
            rev = money_to_float(item.get("total"))

            pid = sku_to_pid.get(sku, item_id)
            cat_names = product_categories.get(pid, ["未分類"])

            for cname in cat_names:
                cat_stats[cname]["revenue"] += rev
                cat_stats[cname]["quantity"] += qty
                cat_stats[cname]["orders"].add(oid)
                cat_stats[cname]["products"].add(pid)

    total_revenue = sum(c["revenue"] for c in cat_stats.values())

    result = []
    for cname, data in sorted(cat_stats.items(), key=lambda x: -x[1]["revenue"]):
        result.append({
            "category": cname,
            "revenue": round(data["revenue"], 2),
            "revenue_share": f"{round(data['revenue'] / total_revenue * 100, 1)}%" if total_revenue else "0%",
            "quantity": data["quantity"],
            "order_count": len(data["orders"]),
            "product_count": len(data["products"]),
            "avg_item_price": round(data["revenue"] / data["quantity"], 2) if data["quantity"] else 0,
        })

    return {
        "period": f"{start_date} ~ {end_date}",
        "channel_filter": channel,
        "total_categories": len(result),
        "total_revenue": round(total_revenue, 2),
        "categories": result,
    }


# ============================================================
# Tool 6: get_promotion_analysis — 促銷活動分析
# ============================================================
@mcp.tool()
def get_promotion_analysis(
    status: Literal["active", "inactive", "hidden", "all"] = Field(default="all", description="活動狀態篩選"),
    discount_type: Optional[str] = Field(default=None, description="折扣類型篩選（amount/percentage/free_shipping/addon）"),
) -> dict:
    """分析促銷活動效果：各活動的使用次數、折扣類型、狀態分佈。可搭配銷售數據評估促銷 ROI。"""
    from tools.base_tool import api_get

    promotions = fetch_all_pages("promotions", max_pages=10)

    if status != "all":
        promotions = [p for p in promotions if p.get("status") == status]
    if discount_type:
        promotions = [p for p in promotions if p.get("discount_type") == discount_type]

    type_breakdown = defaultdict(lambda: {"count": 0, "total_use_count": 0})
    status_breakdown = defaultdict(int)

    results = []
    for p in promotions:
        title = get_translation(p.get("title_translations"))
        dtype = p.get("discount_type", "")
        pstatus = p.get("status", "")
        use_count = p.get("use_count", 0) or 0
        sum_use_count = p.get("sum_use_count", 0) or 0
        max_use = p.get("max_use_count", 0) or 0

        type_breakdown[dtype]["count"] += 1
        type_breakdown[dtype]["total_use_count"] += sum_use_count
        status_breakdown[pstatus] += 1

        results.append({
            "id": p.get("id"),
            "title": title,
            "discount_type": dtype,
            "discount_amount": p.get("discount_amount", 0) or 0,
            "discount_percentage": p.get("discount_percentage", 0) or 0,
            "status": pstatus,
            "use_count": use_count,
            "sum_use_count": sum_use_count,
            "max_use_count": max_use,
            "utilization": f"{round(sum_use_count / max_use * 100, 1)}%" if max_use else "無上限",
            "start_at": p.get("start_at"),
            "end_at": p.get("end_at"),
            "codes": p.get("codes", []),
            "platforms": p.get("available_platforms", []),
        })

    # 依使用次數排序
    results.sort(key=lambda x: -(x["sum_use_count"] or 0))

    return {
        "total_promotions": len(results),
        "status_breakdown": dict(status_breakdown),
        "type_breakdown": {k: v for k, v in sorted(type_breakdown.items(), key=lambda x: -x[1]["count"])},
        "promotions": results,
    }


# ============================================================
# Tool 7: get_refund_by_store — 各門市/通路退貨退款分析
# ============================================================
@mcp.tool()
def get_refund_by_store(
    start_date: str = Field(description="起始日期 YYYY-MM-DD"),
    end_date: str = Field(description="結束日期 YYYY-MM-DD"),
) -> dict:
    """依門市/通路分析退貨退款分佈。

    【用途】取得指定時間區間內的退貨單，並依關聯訂單的門市/通路分群，
    計算各門市的退貨筆數、退款金額、最常被退貨的商品，協助評估各通路退貨狀況。
    【呼叫的 Shopline API】
    - GET /v1/return_orders（退貨單列表）
    - GET /v1/orders/{order_id}（取得關聯訂單的通路資訊）
    【回傳結構】dict 含 period、total_return_orders、stores（各門市退貨統計）。
    """
    import time as _time

    params = {
        "created_after": f"{start_date}T00:00:00Z",
        "created_before": f"{end_date}T23:59:59Z",
    }
    return_orders = fetch_all_pages("return_orders", params=params, max_pages=50)

    # 收集需要查詢的 order_id
    order_ids = set()
    for ro in return_orders:
        oid = ro.get("order_id")
        if oid:
            order_ids.add(oid)

    # 批次查詢關聯訂單以取得通路資訊
    order_channel_map = {}  # order_id -> store_name
    for oid in order_ids:
        try:
            data = api_get("order_detail", path_params={"order_id": oid})
            o = data if "order_number" in data else data.get("item", data)
            if o.get("created_from") == "pos":
                ch = o.get("channel") or {}
                store_name = get_translation(ch.get("created_by_channel_name")) or "未知門市"
            else:
                store_name = "線上官網"
            order_channel_map[oid] = store_name
            _time.sleep(0.2)
        except Exception:
            order_channel_map[oid] = "未知通路"

    # 依門市彙總退貨
    store_stats = defaultdict(lambda: {
        "refund_count": 0, "refund_amount": 0.0, "items": defaultdict(int)
    })

    for ro in return_orders:
        oid = ro.get("order_id")
        store_name = order_channel_map.get(oid, "未知通路")
        refund_amount = money_to_float(ro.get("total"))

        store_stats[store_name]["refund_count"] += 1
        store_stats[store_name]["refund_amount"] += refund_amount

        for item in ro.get("items", []):
            obj_data = item.get("object_data") or {}
            title = get_translation(obj_data.get("title_translations"))
            sku = obj_data.get("sku") or ""
            qty = item.get("quantity", 1)
            key = sku or title or "unknown"
            store_stats[store_name]["items"][key] += qty

    # 整理結果
    stores = []
    for store_name, data in sorted(store_stats.items(), key=lambda x: -x[1]["refund_amount"]):
        top_items = sorted(data["items"].items(), key=lambda x: -x[1])[:10]
        stores.append({
            "store_name": store_name,
            "refund_count": data["refund_count"],
            "refund_amount": round(data["refund_amount"], 2),
            "top_refunded_items": [
                {"item": item, "quantity": qty} for item, qty in top_items
            ],
        })

    return {
        "period": f"{start_date} ~ {end_date}",
        "total_return_orders": len(return_orders),
        "stores": stores,
    }


# ============================================================
# Tool 8: get_stock_transfer_suggestions — 跨倉庫調撥建議
# ============================================================
@mcp.tool()
def get_stock_transfer_suggestions(
    min_stock_diff: int = Field(default=10, description="倉庫間庫存差距門檻，差距 >= 此值才建議調撥"),
) -> dict:
    """自動產生跨倉庫庫存調撥建議。

    【用途】逐商品查詢各倉庫庫存，若同商品在不同倉庫之間的庫存差距過大
    （差值 >= min_stock_diff），則建議從庫存多的倉庫調撥到庫存少的倉庫。
    僅分析前 30 個商品以避免 API 速率限制。
    【呼叫的 Shopline API】
    - GET /v1/products（商品列表）
    - GET /v1/products/{product_id}/stocks（各倉庫庫存）
    - GET /v1/warehouses（倉庫名稱對照）
    【回傳結構】dict 含 products_analyzed、suggestions_count、suggestions 列表。
    """
    import time as _time

    # 取得倉庫名稱對照
    wh_data = api_get("warehouses", params={"per_page": 50})
    wh_map = {w["id"]: w.get("name", w["id"]) for w in wh_data.get("items", [])}

    # 取得商品列表（限前 30 個）
    products = fetch_all_pages("products", max_pages=10)
    products = products[:30]

    suggestions = []

    for p in products:
        pid = p.get("id")
        title = get_translation(p.get("title_translations"))

        try:
            stock_data = api_get("product_stocks", path_params={"product_id": pid})
            _time.sleep(0.2)
        except Exception:
            continue

        for v in stock_data.get("variations", []):
            sku = v.get("sku", "")
            fields = v.get("fields_translations", {}).get("zh-hant", [])
            variant_label = sku or " / ".join(fields) or "default"

            stocks = v.get("stocks", [])
            if len(stocks) < 2:
                continue

            # 找出各倉庫庫存
            wh_stocks = []
            for s in stocks:
                wid = s.get("warehouse_id", "")
                qty = s.get("quantity", 0) or 0
                wname = wh_map.get(wid, wid)
                wh_stocks.append({"warehouse_id": wid, "warehouse_name": wname, "quantity": qty})

            # 排序：庫存多到少
            wh_stocks.sort(key=lambda x: -x["quantity"])

            # 比較最高與最低
            highest = wh_stocks[0]
            lowest = wh_stocks[-1]
            diff = highest["quantity"] - lowest["quantity"]

            if diff >= min_stock_diff:
                suggested_qty = diff // 2  # 建議調撥差距的一半以平衡庫存
                suggestions.append({
                    "product_title": title,
                    "variant": variant_label,
                    "from_warehouse": highest["warehouse_name"],
                    "from_quantity": highest["quantity"],
                    "to_warehouse": lowest["warehouse_name"],
                    "to_quantity": lowest["quantity"],
                    "stock_diff": diff,
                    "suggested_transfer_qty": suggested_qty,
                })

    suggestions.sort(key=lambda x: -x["stock_diff"])

    return {
        "min_stock_diff": min_stock_diff,
        "products_analyzed": len(products),
        "suggestions_count": len(suggestions),
        "suggestions": suggestions,
    }


# ============================================================
# Tool 9: get_promotion_roi — 促銷活動 ROI 分析
# ============================================================
@mcp.tool()
def get_promotion_roi(
    start_date: str = Field(description="起始日期 YYYY-MM-DD"),
    end_date: str = Field(description="結束日期 YYYY-MM-DD"),
) -> dict:
    """交叉比對促銷活動與銷售數據，計算各活動的 ROI。

    【用途】取得指定時間區間內活躍的促銷活動，並比對訂單中的 promotion_items，
    統計每個活動帶來的訂單數、營業額、折扣金額，計算平均每單折扣與折扣占比。
    【呼叫的 Shopline API】
    - GET /v1/promotions（促銷活動列表）
    - GET /v1/orders/search（訂單查詢）
    【回傳結構】dict 含 period、total_promotions、promotions（各活動 ROI 明細）。
    """
    # Step 1: 取得促銷活動
    promotions = fetch_all_pages("promotions", max_pages=10)

    # 建立促銷 ID → 資訊對照
    promo_map = {}
    for p in promotions:
        pid = p.get("id")
        title = get_translation(p.get("title_translations"))
        promo_map[pid] = {
            "title": title,
            "discount_type": p.get("discount_type", ""),
            "status": p.get("status", ""),
            "start_at": p.get("start_at"),
            "end_at": p.get("end_at"),
        }

    # Step 2: 取得訂單
    params = {
        "created_after": f"{start_date}T00:00:00Z",
        "created_before": f"{end_date}T23:59:59Z",
    }
    orders = fetch_all_pages("orders_search", params=params, max_pages=200)
    orders = [o for o in orders if o.get("status") in VALID_ORDER_STATUSES]

    # Step 3: 統計各促銷活動的訂單和金額
    promo_stats = defaultdict(lambda: {
        "orders_count": 0, "total_revenue": 0.0,
        "total_discount": 0.0, "order_ids": set()
    })

    for o in orders:
        oid = o.get("id", "")
        order_revenue = money_to_float(o.get("total"))
        promotion_items = o.get("promotion_items", [])

        for pi in promotion_items:
            promo = pi.get("promotion") or {}
            promo_id = promo.get("id") or pi.get("promotion_id")
            if not promo_id:
                continue

            discounted = money_to_float(pi.get("discounted_amount"))

            # 避免同一訂單重複計算
            if oid not in promo_stats[promo_id]["order_ids"]:
                promo_stats[promo_id]["orders_count"] += 1
                promo_stats[promo_id]["total_revenue"] += order_revenue
                promo_stats[promo_id]["order_ids"].add(oid)

            promo_stats[promo_id]["total_discount"] += discounted

    # Step 4: 整理結果
    results = []
    for promo_id, stats in promo_stats.items():
        info = promo_map.get(promo_id, {
            "title": f"未知活動 ({promo_id})",
            "discount_type": "",
            "status": "",
            "start_at": None,
            "end_at": None,
        })

        orders_count = stats["orders_count"]
        total_revenue = stats["total_revenue"]
        total_discount = stats["total_discount"]
        avg_discount = total_discount / orders_count if orders_count else 0
        discount_rate = total_discount / total_revenue * 100 if total_revenue else 0

        results.append({
            "promotion_id": promo_id,
            "title": info["title"],
            "discount_type": info["discount_type"],
            "status": info["status"],
            "start_at": info["start_at"],
            "end_at": info["end_at"],
            "orders_count": orders_count,
            "total_revenue": round(total_revenue, 2),
            "total_discount": round(total_discount, 2),
            "avg_discount_per_order": round(avg_discount, 2),
            "discount_rate": f"{round(discount_rate, 1)}%",
        })

    results.sort(key=lambda x: -x["total_revenue"])

    return {
        "period": f"{start_date} ~ {end_date}",
        "total_orders_analyzed": len(orders),
        "total_promotions_used": len(results),
        "promotions": results,
    }


# ============================================================
# Tool 10: get_customer_lifecycle — 客戶生命週期遷移分析
# ============================================================
@mcp.tool()
def get_customer_lifecycle(
    period1_start: str = Field(description="第一期起始日期 YYYY-MM-DD"),
    period1_end: str = Field(description="第一期結束日期 YYYY-MM-DD"),
    period2_start: str = Field(description="第二期起始日期 YYYY-MM-DD"),
    period2_end: str = Field(description="第二期結束日期 YYYY-MM-DD"),
    r_days: int = Field(default=30, description="Recency 門檻天數（最近消費 ≤ 此值為高 R）"),
    f_threshold: int = Field(default=2, description="Frequency 門檻（消費 ≥ 此值為高 F）"),
    m_threshold: float = Field(default=5000, description="Monetary 門檻金額（累計 ≥ 此值為高 M）"),
) -> dict:
    """比較兩個時間區間的 RFM 分群遷移，分析客戶生命週期變化。

    【用途】分別計算兩個時段的客戶 RFM 分群，然後比較客戶在兩期之間的分群遷移，
    找出升級（segment 改善）、流失（segment 退步）、新增、消失的客戶，
    產出分群遷移矩陣，協助制定客戶經營策略。
    【呼叫的 Shopline API】
    - GET /v1/orders/search（兩個時段各查詢一次）
    【回傳結構】dict 含 period1、period2、segment_migration、upgrade_count、churn_count、new_count、lost_count。
    """
    SEGMENT_LABELS = {
        "HHH": "Champions（最佳客戶）",
        "HHL": "Loyal（高頻低消）",
        "HLH": "Big Spender（近期高消）",
        "HLL": "New（近期新客）",
        "LHH": "At Risk（流失高價值）",
        "LHL": "Needs Attention（流失高頻）",
        "LLH": "About to Sleep（流失高消）",
        "LLL": "Lost（流失低價值）",
    }

    # 分群排序等級（越高越好）
    SEGMENT_RANK = {
        "LLL": 0, "LLH": 1, "LHL": 2, "LHH": 3,
        "HLL": 4, "HLH": 5, "HHL": 6, "HHH": 7,
    }

    def compute_rfm(start_date, end_date):
        """計算一個時段的客戶 RFM 分群"""
        ref_date = datetime.fromisoformat(f"{end_date}T23:59:59+00:00")
        params = {
            "created_after": f"{start_date}T00:00:00Z",
            "created_before": f"{end_date}T23:59:59Z",
        }
        orders = fetch_all_pages("orders_search", params=params, max_pages=200)
        orders = [o for o in orders if o.get("status") in VALID_ORDER_STATUSES]

        customers = defaultdict(lambda: {"name": "", "orders": [], "total_spent": 0.0})
        for o in orders:
            cid = o.get("customer_id")
            if not cid:
                continue
            customers[cid]["name"] = o.get("customer_name", "")
            customers[cid]["orders"].append(o.get("created_at", ""))
            customers[cid]["total_spent"] += money_to_float(o.get("total"))

        rfm = {}
        for cid, data in customers.items():
            dates = sorted(data["orders"])
            latest = dates[-1] if dates else ""
            if latest:
                latest_dt = datetime.fromisoformat(latest.replace("+00:00", "+00:00"))
                recency = (ref_date - latest_dt).days
            else:
                recency = 999

            frequency = len(dates)
            monetary = data["total_spent"]

            r_high = recency <= r_days
            f_high = frequency >= f_threshold
            m_high = monetary >= m_threshold

            segment = f"{'H' if r_high else 'L'}{'H' if f_high else 'L'}{'H' if m_high else 'L'}"
            rfm[cid] = {
                "name": data["name"],
                "segment": segment,
                "recency": recency,
                "frequency": frequency,
                "monetary": round(monetary, 2),
            }

        return rfm

    # 計算兩期 RFM
    rfm1 = compute_rfm(period1_start, period1_end)
    rfm2 = compute_rfm(period2_start, period2_end)

    all_customers = set(rfm1.keys()) | set(rfm2.keys())

    # 遷移矩陣
    migration = defaultdict(int)  # (from_segment, to_segment) -> count
    upgrade_count = 0
    churn_count = 0
    new_count = 0
    lost_count = 0

    upgrade_customers = []
    churn_customers = []

    for cid in all_customers:
        in_p1 = cid in rfm1
        in_p2 = cid in rfm2

        if in_p1 and in_p2:
            seg1 = rfm1[cid]["segment"]
            seg2 = rfm2[cid]["segment"]
            migration[(seg1, seg2)] += 1
            rank1 = SEGMENT_RANK.get(seg1, 0)
            rank2 = SEGMENT_RANK.get(seg2, 0)
            if rank2 > rank1:
                upgrade_count += 1
                upgrade_customers.append({
                    "customer_id": cid,
                    "name": rfm2[cid]["name"],
                    "from_segment": f"{seg1} ({SEGMENT_LABELS.get(seg1, seg1)})",
                    "to_segment": f"{seg2} ({SEGMENT_LABELS.get(seg2, seg2)})",
                })
            elif rank2 < rank1:
                churn_count += 1
                churn_customers.append({
                    "customer_id": cid,
                    "name": rfm2[cid]["name"],
                    "from_segment": f"{seg1} ({SEGMENT_LABELS.get(seg1, seg1)})",
                    "to_segment": f"{seg2} ({SEGMENT_LABELS.get(seg2, seg2)})",
                })
        elif not in_p1 and in_p2:
            new_count += 1
        elif in_p1 and not in_p2:
            lost_count += 1

    # 整理遷移矩陣
    migration_list = []
    for (seg1, seg2), count in sorted(migration.items(), key=lambda x: -x[1]):
        migration_list.append({
            "from_segment": f"{seg1} ({SEGMENT_LABELS.get(seg1, seg1)})",
            "to_segment": f"{seg2} ({SEGMENT_LABELS.get(seg2, seg2)})",
            "count": count,
        })

    # 各期分群分佈
    def segment_distribution(rfm_data):
        dist = defaultdict(int)
        for data in rfm_data.values():
            dist[data["segment"]] += 1
        return {
            f"{seg} ({SEGMENT_LABELS.get(seg, seg)})": count
            for seg, count in sorted(dist.items(), key=lambda x: -x[1])
        }

    return {
        "period1": f"{period1_start} ~ {period1_end}",
        "period2": f"{period2_start} ~ {period2_end}",
        "thresholds": {
            "recency_days": r_days,
            "frequency": f_threshold,
            "monetary": m_threshold,
        },
        "period1_customers": len(rfm1),
        "period2_customers": len(rfm2),
        "period1_distribution": segment_distribution(rfm1),
        "period2_distribution": segment_distribution(rfm2),
        "upgrade_count": upgrade_count,
        "churn_count": churn_count,
        "new_count": new_count,
        "lost_count": lost_count,
        "segment_migration": migration_list[:30],
        "top_upgrades": upgrade_customers[:10],
        "top_churns": churn_customers[:10],
    }


# ============================================================
# Tool 11: get_slow_movers — 滯銷商品分析
# ============================================================
@mcp.tool()
def get_slow_movers(
    start_date: str = Field(description="分析區間起始 YYYY-MM-DD"),
    end_date: str = Field(description="分析區間結束 YYYY-MM-DD"),
    days_threshold: int = Field(default=30, description="可售天數門檻，超過此值視為滯銷"),
) -> dict:
    """找出庫存高但銷量低的滯銷商品。

    【用途】交叉比對商品庫存與銷售數據，計算每個商品的日均銷量與可售天數（days_of_supply），
    標記 days_of_supply 超過門檻或零銷售的商品為滯銷品，協助清倉決策。
    【呼叫的 Shopline API】
    - GET /v1/products（商品列表含庫存）
    - GET /v1/orders/search（銷售數據）
    【回傳結構】dict 含 period、period_days、total_products、slow_movers（滯銷商品列表）。
    """
    # Step 1: 取得商品庫存
    products = fetch_all_pages("products", max_pages=10)

    # Step 2: 取得銷售數據
    params = {
        "created_after": f"{start_date}T00:00:00Z",
        "created_before": f"{end_date}T23:59:59Z",
    }
    orders = fetch_all_pages("orders_search", params=params, max_pages=200)
    orders = [o for o in orders if o.get("status") in VALID_ORDER_STATUSES]

    # 計算天數
    d1 = datetime.strptime(start_date, "%Y-%m-%d")
    d2 = datetime.strptime(end_date, "%Y-%m-%d")
    period_days = (d2 - d1).days or 1

    # 依商品 ID 彙總銷售數量
    sales_by_product = defaultdict(int)
    for o in orders:
        for item in o.get("subtotal_items", []):
            pid = item.get("item_id", "")
            qty = item.get("quantity", 1)
            sales_by_product[pid] += qty

    # Step 3: 計算滯銷指標
    slow_movers = []
    for p in products:
        pid = p.get("id")
        title = get_translation(p.get("title_translations"))
        sku = p.get("sku") or ""
        brand = p.get("brand") or ""

        variations = p.get("variations", [])
        current_stock = sum(v.get("quantity", 0) or 0 for v in variations)
        if not variations:
            current_stock = p.get("quantity", 0) or 0

        # 跳過沒有庫存的商品
        if current_stock <= 0:
            continue

        units_sold = sales_by_product.get(pid, 0)
        daily_avg_sales = units_sold / period_days if period_days else 0

        if daily_avg_sales > 0:
            days_of_supply = current_stock / daily_avg_sales
        else:
            days_of_supply = float("inf")

        # 判斷是否為滯銷品
        is_slow = (days_of_supply == float("inf")) or (days_of_supply > days_threshold)

        if is_slow:
            slow_movers.append({
                "product_id": pid,
                "title": title,
                "sku": sku,
                "brand": brand,
                "current_stock": current_stock,
                "units_sold": units_sold,
                "daily_avg_sales": round(daily_avg_sales, 2),
                "days_of_supply": round(days_of_supply, 1) if days_of_supply != float("inf") else "無銷售",
                "status": "零銷售" if units_sold == 0 else "滯銷",
            })

    # 排序：零銷售的排前面，然後按庫存量從多到少
    slow_movers.sort(key=lambda x: (
        0 if x["status"] == "零銷售" else 1,
        -x["current_stock"]
    ))

    return {
        "period": f"{start_date} ~ {end_date}",
        "period_days": period_days,
        "days_threshold": days_threshold,
        "total_products_with_stock": len([p for p in products if sum(
            v.get("quantity", 0) or 0 for v in p.get("variations", [])
        ) > 0 or (not p.get("variations") and (p.get("quantity", 0) or 0) > 0)]),
        "slow_movers_count": len(slow_movers),
        "zero_sales_count": len([s for s in slow_movers if s["status"] == "零銷售"]),
        "slow_movers": slow_movers,
    }
