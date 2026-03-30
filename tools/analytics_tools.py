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
    fetch_all_pages, money_to_float, get_translation
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
