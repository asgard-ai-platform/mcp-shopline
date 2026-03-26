"""
訂單相關 Tools — 供 AI Agent 調用
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.base_tool import (
    api_get, fetch_all_pages, fetch_all_pages_by_date_segments,
    money_to_float, get_translation, ShoplineAPIError
)
from collections import Counter, defaultdict
from datetime import datetime

# Shopline 線上訂單狀態為 confirmed，POS 為 completed
# 合併查詢時不帶 status 參數，改用程式端篩選排除 cancelled/pending
VALID_ORDER_STATUSES = {"completed", "confirmed"}


# ============================================================
# Tool 1: query_orders — 依條件查詢訂單
# ============================================================
QUERY_ORDERS_SCHEMA = {
    "name": "query_orders",
    "description": "依時間區間、訂單狀態、通路來源查詢訂單列表。回傳精簡的訂單摘要。",
    "input_schema": {
        "type": "object",
        "properties": {
            "start_date": {"type": "string", "description": "起始日期 YYYY-MM-DD"},
            "end_date": {"type": "string", "description": "結束日期 YYYY-MM-DD"},
            "status": {
                "type": "string",
                "enum": ["pending", "confirmed", "completed", "cancelled"],
                "description": "訂單狀態篩選"
            },
            "channel": {
                "type": "string",
                "enum": ["online", "pos", "all"],
                "description": "通路篩選: online=線上官網, pos=實體門市, all=全部",
                "default": "all"
            },
            "store_name": {"type": "string", "description": "門市名稱篩選（如：松菸誠品、新光A11）"},
            "max_results": {"type": "integer", "description": "最多回傳筆數", "default": 100}
        },
        "required": ["start_date", "end_date"]
    }
}


def query_orders(start_date, end_date, status=None, channel="all", store_name=None, max_results=100):
    """查詢訂單"""
    params = {
        "created_after": f"{start_date}T00:00:00Z",
        "created_before": f"{end_date}T23:59:59Z",
    }
    if status:
        params["status"] = status

    orders = fetch_all_pages("orders_search", params=params, max_pages=20)

    # 通路篩選
    if channel == "online":
        orders = [o for o in orders if o.get("created_from") == "shop"]
    elif channel == "pos":
        orders = [o for o in orders if o.get("created_from") == "pos"]

    # 門市篩選
    if store_name:
        def match_store(order):
            ch = order.get("channel") or {}
            name = ch.get("created_by_channel_name") or {}
            return store_name in get_translation(name)
        orders = [o for o in orders if match_store(o)]

    # 精簡輸出
    results = []
    for o in orders[:max_results]:
        ch = o.get("channel") or {}
        ch_name = get_translation(ch.get("created_by_channel_name")) if ch else ""
        payment = o.get("order_payment") or {}
        delivery = o.get("order_delivery") or {}

        results.append({
            "order_number": o.get("order_number"),
            "status": o.get("status"),
            "channel": "POS" if o.get("created_from") == "pos" else "線上",
            "store_name": ch_name or None,
            "total": money_to_float(o.get("total")),
            "subtotal": money_to_float(o.get("subtotal")),
            "discount": money_to_float(o.get("order_discount")),
            "payment_type": get_translation(payment.get("name_translations")),
            "payment_status": payment.get("status"),
            "delivery_type": get_translation(delivery.get("name_translations")),
            "delivery_status": delivery.get("delivery_status"),
            "customer_name": o.get("customer_name"),
            "items_count": len(o.get("subtotal_items", [])),
            "created_at": o.get("created_at"),
        })

    return {
        "total_found": len(orders),
        "returned": len(results),
        "orders": results
    }


# ============================================================
# Tool 2: get_sales_summary — 銷售摘要
# ============================================================
GET_SALES_SUMMARY_SCHEMA = {
    "name": "get_sales_summary",
    "description": "取得指定時間區間的銷售摘要：營業額、訂單數、客單價、件單價、折扣總額等核心指標。支援依通路/門市篩選。",
    "input_schema": {
        "type": "object",
        "properties": {
            "start_date": {"type": "string", "description": "起始日期 YYYY-MM-DD"},
            "end_date": {"type": "string", "description": "結束日期 YYYY-MM-DD"},
            "status": {"type": "string", "description": "訂單狀態", "default": "completed"},
            "channel": {"type": "string", "enum": ["online", "pos", "all"], "default": "all"},
            "store_name": {"type": "string", "description": "門市名稱篩選"},
        },
        "required": ["start_date", "end_date"]
    }
}


def get_sales_summary(start_date, end_date, status="completed", channel="all", store_name=None):
    """計算銷售摘要"""
    params = {
        "created_after": f"{start_date}T00:00:00Z",
        "created_before": f"{end_date}T23:59:59Z",
    }

    orders = fetch_all_pages("orders_search", params=params, max_pages=200)

    # 狀態篩選：預設排除 cancelled/pending，只保留有效訂單
    if status == "completed":
        orders = [o for o in orders if o.get("status") in VALID_ORDER_STATUSES]
    elif status:
        orders = [o for o in orders if o.get("status") == status]

    # 通路篩選
    if channel == "online":
        orders = [o for o in orders if o.get("created_from") == "shop"]
    elif channel == "pos":
        orders = [o for o in orders if o.get("created_from") == "pos"]

    if store_name:
        def match_store(order):
            ch = order.get("channel") or {}
            name = ch.get("created_by_channel_name") or {}
            return store_name in get_translation(name)
        orders = [o for o in orders if match_store(o)]

    total_revenue = 0.0
    total_subtotal = 0.0
    total_discount = 0.0
    total_items_qty = 0
    order_count = len(orders)

    payment_breakdown = Counter()
    delivery_breakdown = Counter()
    store_breakdown = defaultdict(lambda: {"revenue": 0.0, "orders": 0})

    for o in orders:
        revenue = money_to_float(o.get("total"))
        subtotal = money_to_float(o.get("subtotal"))
        discount = money_to_float(o.get("order_discount"))

        total_revenue += revenue
        total_subtotal += subtotal
        total_discount += discount

        items = o.get("subtotal_items", [])
        for item in items:
            total_items_qty += item.get("quantity", 1)

        payment = o.get("order_payment") or {}
        payment_name = get_translation(payment.get("name_translations"))
        if payment_name:
            payment_breakdown[payment_name] += 1

        delivery = o.get("order_delivery") or {}
        delivery_name = get_translation(delivery.get("name_translations"))
        if delivery_name:
            delivery_breakdown[delivery_name] += 1

        ch = o.get("channel") or {}
        if o.get("created_from") == "pos":
            sname = get_translation(ch.get("created_by_channel_name")) or "未知門市"
        else:
            sname = "線上官網"
        store_breakdown[sname]["revenue"] += revenue
        store_breakdown[sname]["orders"] += 1

    avg_order_value = total_revenue / order_count if order_count else 0
    avg_item_price = total_revenue / total_items_qty if total_items_qty else 0

    return {
        "period": f"{start_date} ~ {end_date}",
        "status_filter": status,
        "channel_filter": channel,
        "order_count": order_count,
        "total_revenue": round(total_revenue, 2),
        "total_subtotal": round(total_subtotal, 2),
        "total_discount": round(total_discount, 2),
        "net_revenue": round(total_revenue, 2),
        "total_items_qty": total_items_qty,
        "avg_order_value": round(avg_order_value, 2),
        "avg_item_price": round(avg_item_price, 2),
        "payment_breakdown": dict(payment_breakdown.most_common()),
        "delivery_breakdown": dict(delivery_breakdown.most_common()),
        "store_breakdown": {k: v for k, v in sorted(store_breakdown.items(), key=lambda x: -x[1]["revenue"])},
    }


# ============================================================
# Tool 3: get_top_products — 熱銷/滯銷商品排行
# ============================================================
GET_TOP_PRODUCTS_SCHEMA = {
    "name": "get_top_products",
    "description": "取得指定時間區間的商品銷售排行榜（依銷量或營業額排序），或滯銷商品清單。",
    "input_schema": {
        "type": "object",
        "properties": {
            "start_date": {"type": "string", "description": "起始日期 YYYY-MM-DD"},
            "end_date": {"type": "string", "description": "結束日期 YYYY-MM-DD"},
            "top_n": {"type": "integer", "description": "顯示前 N 名", "default": 20},
            "sort_by": {"type": "string", "enum": ["quantity", "revenue"], "default": "revenue"},
            "channel": {"type": "string", "enum": ["online", "pos", "all"], "default": "all"},
        },
        "required": ["start_date", "end_date"]
    }
}


def get_top_products(start_date, end_date, top_n=20, sort_by="revenue", channel="all"):
    """取得熱銷商品排行"""
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

    # 依 SKU 彙總
    product_stats = defaultdict(lambda: {
        "title": "", "sku": "", "brand": "", "color": "", "size": "",
        "quantity": 0, "revenue": 0.0
    })

    for o in orders:
        for item in o.get("subtotal_items", []):
            sku = item.get("sku", "")
            title = get_translation(item.get("title_translations"))
            fields = item.get("fields_translations", {})
            zh_fields = fields.get("zh-hant", [])

            obj_data = item.get("object_data") or {}
            brand = obj_data.get("brand", "")

            qty = item.get("quantity", 1)
            rev = money_to_float(item.get("total"))

            key = sku or title
            product_stats[key]["title"] = title
            product_stats[key]["sku"] = sku
            product_stats[key]["brand"] = brand
            product_stats[key]["color"] = zh_fields[0] if len(zh_fields) > 0 else ""
            product_stats[key]["size"] = zh_fields[1] if len(zh_fields) > 1 else ""
            product_stats[key]["quantity"] += qty
            product_stats[key]["revenue"] += rev

    sorted_products = sorted(
        product_stats.values(),
        key=lambda x: x[sort_by],
        reverse=True
    )

    return {
        "period": f"{start_date} ~ {end_date}",
        "sort_by": sort_by,
        "total_skus": len(product_stats),
        "top_products": [
            {**p, "revenue": round(p["revenue"], 2), "rank": i + 1}
            for i, p in enumerate(sorted_products[:top_n])
        ]
    }


# ============================================================
# Tool 4: get_sales_trend — 銷售趨勢
# ============================================================
GET_SALES_TREND_SCHEMA = {
    "name": "get_sales_trend",
    "description": "取得銷售趨勢數據，支援每日/每週/每月粒度，可用於繪製趨勢圖。",
    "input_schema": {
        "type": "object",
        "properties": {
            "start_date": {"type": "string", "description": "起始日期 YYYY-MM-DD"},
            "end_date": {"type": "string", "description": "結束日期 YYYY-MM-DD"},
            "granularity": {
                "type": "string",
                "enum": ["daily", "weekly", "monthly"],
                "default": "daily"
            },
            "channel": {"type": "string", "enum": ["online", "pos", "all"], "default": "all"},
        },
        "required": ["start_date", "end_date"]
    }
}


def get_sales_trend(start_date, end_date, granularity="daily", channel="all"):
    """取得銷售趨勢"""
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

    trend = defaultdict(lambda: {"revenue": 0.0, "orders": 0, "items": 0})

    for o in orders:
        created = o.get("created_at", "")
        if not created:
            continue

        dt = datetime.fromisoformat(created.replace("+00:00", "+00:00"))

        if granularity == "daily":
            key = dt.strftime("%Y-%m-%d")
        elif granularity == "weekly":
            key = dt.strftime("%Y-W%W")
        else:  # monthly
            key = dt.strftime("%Y-%m")

        trend[key]["revenue"] += money_to_float(o.get("total"))
        trend[key]["orders"] += 1
        trend[key]["items"] += sum(
            item.get("quantity", 1) for item in o.get("subtotal_items", [])
        )

    sorted_trend = sorted(trend.items())

    return {
        "period": f"{start_date} ~ {end_date}",
        "granularity": granularity,
        "data_points": len(sorted_trend),
        "trend": [
            {
                "date": k,
                "revenue": round(v["revenue"], 2),
                "orders": v["orders"],
                "items": v["items"],
                "avg_order_value": round(v["revenue"] / v["orders"], 2) if v["orders"] else 0,
            }
            for k, v in sorted_trend
        ]
    }


# ============================================================
# Tool 5: get_channel_comparison — 門市比較
# ============================================================
GET_CHANNEL_COMPARISON_SCHEMA = {
    "name": "get_channel_comparison",
    "description": "比較各門市/通路的同期業績：營業額、訂單數、客單價等。支援線上 vs 門市，或門市之間的比較。",
    "input_schema": {
        "type": "object",
        "properties": {
            "start_date": {"type": "string", "description": "起始日期 YYYY-MM-DD"},
            "end_date": {"type": "string", "description": "結束日期 YYYY-MM-DD"},
        },
        "required": ["start_date", "end_date"]
    }
}


def get_channel_comparison(start_date, end_date):
    """各通路/門市比較"""
    params = {
        "created_after": f"{start_date}T00:00:00Z",
        "created_before": f"{end_date}T23:59:59Z",
    }

    orders = fetch_all_pages("orders_search", params=params, max_pages=200)
    orders = [o for o in orders if o.get("status") in VALID_ORDER_STATUSES]

    channels = defaultdict(lambda: {
        "revenue": 0.0, "orders": 0, "items": 0, "discount": 0.0
    })

    for o in orders:
        revenue = money_to_float(o.get("total"))
        discount = money_to_float(o.get("order_discount"))
        items_qty = sum(item.get("quantity", 1) for item in o.get("subtotal_items", []))

        if o.get("created_from") == "pos":
            ch = o.get("channel") or {}
            name = get_translation(ch.get("created_by_channel_name")) or "未知門市"
        else:
            name = "線上官網"

        channels[name]["revenue"] += revenue
        channels[name]["orders"] += 1
        channels[name]["items"] += items_qty
        channels[name]["discount"] += discount

    total_revenue = sum(c["revenue"] for c in channels.values())

    result = []
    for name, data in sorted(channels.items(), key=lambda x: -x[1]["revenue"]):
        result.append({
            "channel": name,
            "revenue": round(data["revenue"], 2),
            "orders": data["orders"],
            "items": data["items"],
            "discount": round(data["discount"], 2),
            "avg_order_value": round(data["revenue"] / data["orders"], 2) if data["orders"] else 0,
            "revenue_share": f"{round(data['revenue'] / total_revenue * 100, 1)}%" if total_revenue else "0%",
        })

    return {
        "period": f"{start_date} ~ {end_date}",
        "total_revenue": round(total_revenue, 2),
        "channels": result
    }


# ============================================================
# Tool 6: get_order_detail — 訂單明細
# ============================================================
GET_ORDER_DETAIL_SCHEMA = {
    "name": "get_order_detail",
    "description": "取得單筆訂單的完整資訊，包含商品明細、付款、物流、折扣等。",
    "input_schema": {
        "type": "object",
        "properties": {
            "order_id": {"type": "string", "description": "訂單 ID"},
        },
        "required": ["order_id"]
    }
}


def get_order_detail(order_id):
    """取得訂單明細"""
    data = api_get("order_detail", path_params={"order_id": order_id})

    o = data if "order_number" in data else data.get("item", data)

    payment = o.get("order_payment") or {}
    delivery = o.get("order_delivery") or {}
    ch = o.get("channel") or {}

    items = []
    for item in o.get("subtotal_items", []):
        fields = item.get("fields_translations", {}).get("zh-hant", [])
        obj_data = item.get("object_data") or {}
        items.append({
            "title": get_translation(item.get("title_translations")),
            "sku": item.get("sku"),
            "quantity": item.get("quantity", 1),
            "price": money_to_float(item.get("price")),
            "sale_price": money_to_float(item.get("price_sale")),
            "item_total": money_to_float(item.get("total")),
            "cost": money_to_float(item.get("cost")),
            "brand": obj_data.get("brand", ""),
            "color": fields[0] if len(fields) > 0 else "",
            "size": fields[1] if len(fields) > 1 else "",
        })

    promotions = []
    for p in o.get("promotion_items", []):
        promo = p.get("promotion") or {}
        promotions.append({
            "title": get_translation(promo.get("title_translations")),
            "discount_type": promo.get("discount_type"),
            "discounted_amount": money_to_float(p.get("discounted_amount")),
        })

    return {
        "order_number": o.get("order_number"),
        "status": o.get("status"),
        "channel": "POS" if o.get("created_from") == "pos" else "線上",
        "store_name": get_translation(ch.get("created_by_channel_name")) if ch else None,
        "created_at": o.get("created_at"),
        "customer_name": o.get("customer_name"),
        "customer_id": o.get("customer_id"),
        "subtotal": money_to_float(o.get("subtotal")),
        "discount": money_to_float(o.get("order_discount")),
        "total": money_to_float(o.get("total")),
        "payment_type": get_translation(payment.get("name_translations")),
        "payment_status": payment.get("status"),
        "delivery_type": get_translation(delivery.get("name_translations")),
        "delivery_status": delivery.get("delivery_status"),
        "delivery_city": (o.get("delivery_address") or {}).get("city"),
        "items": items,
        "promotions": promotions,
        "utm_data": o.get("utm_data") or {},
    }


# ============================================================
# Tool 7: get_refund_summary — 退貨退款統計
# ============================================================
GET_REFUND_SUMMARY_SCHEMA = {
    "name": "get_refund_summary",
    "description": "取得指定時間區間的退貨退款統計：退款金額、退貨筆數、退貨率、退貨商品明細。支援計算淨營收。",
    "input_schema": {
        "type": "object",
        "properties": {
            "start_date": {"type": "string", "description": "起始日期 YYYY-MM-DD"},
            "end_date": {"type": "string", "description": "結束日期 YYYY-MM-DD"},
        },
        "required": ["start_date", "end_date"]
    }
}


def get_refund_summary(start_date, end_date):
    """退貨退款統計"""
    params = {
        "created_after": f"{start_date}T00:00:00Z",
        "created_before": f"{end_date}T23:59:59Z",
    }
    return_orders = fetch_all_pages("return_orders", params=params, max_pages=50)

    total_refund = 0.0
    completed_count = 0
    pending_count = 0
    item_stats = defaultdict(lambda: {"quantity": 0, "refund_amount": 0.0})
    status_breakdown = Counter()

    for ro in return_orders:
        status = ro.get("status", "")
        status_breakdown[status] += 1
        refund = money_to_float(ro.get("total"))

        if status == "completed":
            completed_count += 1
            total_refund += refund

        for item in ro.get("items", []):
            obj_data = item.get("object_data") or {}
            title = get_translation(obj_data.get("title_translations"))
            sku = obj_data.get("sku") or ""
            brand = obj_data.get("brand") or ""
            qty = item.get("quantity", 1)
            item_total = money_to_float(item.get("total"))
            key = sku or title or "unknown"
            item_stats[key]["title"] = title
            item_stats[key]["sku"] = sku
            item_stats[key]["brand"] = brand
            item_stats[key]["quantity"] += qty
            item_stats[key]["refund_amount"] += item_total

    # 排序退貨商品
    sorted_items = sorted(item_stats.values(), key=lambda x: -x["refund_amount"])

    return {
        "period": f"{start_date} ~ {end_date}",
        "total_return_orders": len(return_orders),
        "completed_returns": completed_count,
        "pending_returns": pending_count,
        "total_refund_amount": round(total_refund, 2),
        "status_breakdown": dict(status_breakdown.most_common()),
        "top_refund_items": sorted_items[:20],
    }


# ============================================================
# 註冊所有 Tool
# ============================================================
ORDER_TOOLS = [
    {"schema": QUERY_ORDERS_SCHEMA, "function": query_orders},
    {"schema": GET_SALES_SUMMARY_SCHEMA, "function": get_sales_summary},
    {"schema": GET_TOP_PRODUCTS_SCHEMA, "function": get_top_products},
    {"schema": GET_SALES_TREND_SCHEMA, "function": get_sales_trend},
    {"schema": GET_CHANNEL_COMPARISON_SCHEMA, "function": get_channel_comparison},
    {"schema": GET_ORDER_DETAIL_SCHEMA, "function": get_order_detail},
    {"schema": GET_REFUND_SUMMARY_SCHEMA, "function": get_refund_summary},
]
