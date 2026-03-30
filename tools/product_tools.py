"""
商品與庫存相關 Tools — 供 AI Agent 調用
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import Optional
from pydantic import Field

from app import mcp
from tools.base_tool import (
    api_get, fetch_all_pages, money_to_float, get_translation
)
from collections import defaultdict


# ============================================================
# Tool 1: get_product_list — 商品列表
# ============================================================
@mcp.tool()
def get_product_list(
    keyword: Optional[str] = Field(default=None, description="商品名稱關鍵字搜尋"),
    brand: Optional[str] = Field(default=None, description="品牌篩選"),
    max_results: int = Field(default=50, description="最多回傳筆數"),
) -> dict:
    """取得商品列表，含 SKU 變體、價格、品牌、庫存數量等資訊。"""
    products = fetch_all_pages("products", max_pages=10)

    if keyword:
        keyword_lower = keyword.lower()
        products = [
            p for p in products
            if keyword_lower in get_translation(p.get("title_translations")).lower()
            or keyword_lower in (p.get("sku") or "").lower()
        ]

    if brand:
        brand_lower = brand.lower()
        products = [
            p for p in products
            if brand_lower in (p.get("brand") or "").lower()
        ]

    results = []
    for p in products[:max_results]:
        variations = p.get("variations", [])
        total_qty = sum(v.get("quantity", 0) or 0 for v in variations)
        if not variations:
            total_qty = p.get("quantity", 0) or 0

        supplier = p.get("supplier") or {}
        supplier_name = supplier.get("name", "") if isinstance(supplier, dict) else ""

        results.append({
            "id": p.get("id"),
            "title": get_translation(p.get("title_translations")),
            "sku": p.get("sku"),
            "brand": p.get("brand"),
            "supplier": supplier_name,
            "price": money_to_float(p.get("price")),
            "price_sale": money_to_float(p.get("price_sale")),
            "cost": money_to_float(p.get("cost")),
            "quantity": total_qty,
            "category_ids": p.get("category_ids", []),
            "status": p.get("status"),
            "variants_count": len(variations),
            "tags": p.get("tags", []),
        })

    return {
        "total_found": len(products),
        "returned": len(results),
        "products": results
    }


# ============================================================
# Tool 2: get_product_variants — 商品 SKU 變體明細
# ============================================================
@mcp.tool()
def get_product_variants(
    product_id: str = Field(description="商品 ID"),
) -> dict:
    """取得特定商品的所有 SKU 變體明細，含尺寸×顏色的庫存矩陣。"""
    # 從列表中找到該商品（或直接用 ID 查詢）
    products = fetch_all_pages("products", max_pages=10)
    product = None
    for p in products:
        if p.get("id") == product_id:
            product = p
            break

    if not product:
        return {"error": f"Product {product_id} not found"}

    title = get_translation(product.get("title_translations"))
    field_titles = product.get("field_titles", [])
    dim_names = [get_translation(ft.get("name_translations")) for ft in field_titles]

    variants = []
    for v in product.get("variations", []):
        fields = v.get("fields_translations", {}).get("zh-hant", [])
        feed = v.get("feed_variations", {})

        variants.append({
            "id": v.get("id"),
            "sku": v.get("sku"),
            "color": get_translation(feed.get("color")) if "color" in feed else (fields[0] if len(fields) > 0 else ""),
            "size": get_translation(feed.get("size")) if "size" in feed else (fields[1] if len(fields) > 1 else ""),
            "price": money_to_float(v.get("price")),
            "price_sale": money_to_float(v.get("price_sale")),
            "cost": money_to_float(v.get("cost")),
            "quantity": v.get("quantity", 0) or 0,
            "total_orderable_quantity": v.get("total_orderable_quantity", 0),
        })

    return {
        "product_id": product_id,
        "title": title,
        "brand": product.get("brand"),
        "dimensions": dim_names,
        "variants_count": len(variants),
        "total_quantity": sum(v["quantity"] for v in variants),
        "variants": variants,
    }


# ============================================================
# Tool 3: get_inventory_overview — 庫存總覽
# ============================================================
@mcp.tool()
def get_inventory_overview(
    brand: Optional[str] = Field(default=None, description="品牌篩選"),
) -> dict:
    """取得全商品庫存總覽：總庫存數量、庫存品項數、缺貨品項數等。從商品 variations 的 quantity 欄位計算。"""
    products = fetch_all_pages("products", max_pages=10)

    if brand:
        brand_lower = brand.lower()
        products = [p for p in products if brand_lower in (p.get("brand") or "").lower()]

    total_quantity = 0
    total_cost_value = 0.0
    total_skus = 0
    out_of_stock_skus = 0
    low_stock_skus = 0  # quantity <= 3

    brand_stats = defaultdict(lambda: {"quantity": 0, "skus": 0, "oos": 0})
    product_summary = []

    for p in products:
        title = get_translation(p.get("title_translations"))
        p_brand = p.get("brand") or "未設定"
        variations = p.get("variations", [])

        p_total_qty = 0
        p_sku_count = 0
        p_oos_count = 0

        for v in variations:
            qty = v.get("quantity", 0) or 0
            cost = money_to_float(v.get("cost"))

            total_skus += 1
            p_sku_count += 1
            p_total_qty += qty
            total_quantity += qty
            total_cost_value += cost * qty

            if qty == 0:
                out_of_stock_skus += 1
                p_oos_count += 1
            elif qty <= 3:
                low_stock_skus += 1

            brand_stats[p_brand]["quantity"] += qty
            brand_stats[p_brand]["skus"] += 1
            if qty == 0:
                brand_stats[p_brand]["oos"] += 1

        if not variations:
            qty = p.get("quantity", 0) or 0
            total_skus += 1
            p_sku_count = 1
            p_total_qty = qty
            total_quantity += qty
            if qty == 0:
                out_of_stock_skus += 1
                p_oos_count = 1

        product_summary.append({
            "title": title,
            "brand": p_brand,
            "total_quantity": p_total_qty,
            "sku_count": p_sku_count,
            "out_of_stock_skus": p_oos_count,
        })

    return {
        "total_products": len(products),
        "total_skus": total_skus,
        "total_quantity": total_quantity,
        "total_cost_value": round(total_cost_value, 2),
        "out_of_stock_skus": out_of_stock_skus,
        "low_stock_skus": low_stock_skus,
        "brand_breakdown": {
            k: v for k, v in sorted(brand_stats.items(), key=lambda x: -x[1]["quantity"])
        },
        "products": sorted(product_summary, key=lambda x: x["total_quantity"]),
    }


# ============================================================
# Tool 4: get_low_stock_alerts — 低庫存警示
# ============================================================
@mcp.tool()
def get_low_stock_alerts(
    threshold: int = Field(default=5, description="庫存低於此值即警示"),
) -> dict:
    """取得低庫存或缺貨的 SKU 清單，可自訂庫存門檻值。"""
    products = fetch_all_pages("products", max_pages=10)

    alerts = []
    for p in products:
        title = get_translation(p.get("title_translations"))
        for v in p.get("variations", []):
            qty = v.get("quantity", 0) or 0
            if qty <= threshold:
                fields = v.get("fields_translations", {}).get("zh-hant", [])
                alerts.append({
                    "product_title": title,
                    "sku": v.get("sku"),
                    "color": fields[0] if len(fields) > 0 else "",
                    "size": fields[1] if len(fields) > 1 else "",
                    "quantity": qty,
                    "status": "缺貨" if qty == 0 else "低庫存",
                    "brand": p.get("brand"),
                })

    alerts.sort(key=lambda x: x["quantity"])

    return {
        "threshold": threshold,
        "total_alerts": len(alerts),
        "out_of_stock": len([a for a in alerts if a["quantity"] == 0]),
        "low_stock": len([a for a in alerts if a["quantity"] > 0]),
        "alerts": alerts,
    }


# ============================================================
# Tool 5: get_warehouses — 倉庫列表
# ============================================================
@mcp.tool()
def get_warehouses() -> dict:
    """取得所有倉庫/門市據點列表。"""
    data = api_get("warehouses", params={"per_page": 50})
    warehouses = data.get("items", [])

    return {
        "total": len(warehouses),
        "warehouses": [
            {
                "id": w.get("id"),
                "name": w.get("name"),
                "status": w.get("status"),
            }
            for w in warehouses
        ]
    }


# ============================================================
# Tool 6: get_stock_by_warehouse — 各倉庫 SKU 庫存
# ============================================================
@mcp.tool()
def get_stock_by_warehouse(
    product_id: Optional[str] = Field(default=None, description="商品 ID（不填則查詢全部商品，但較慢）"),
    warehouse_id: Optional[str] = Field(default=None, description="倉庫 ID 篩選（僅看特定倉庫）"),
) -> dict:
    """取得商品在各倉庫/門市的庫存分佈矩陣。可查詢單一商品或全部商品的各倉庫庫存。"""
    # 取得倉庫名稱對照
    wh_data = api_get("warehouses", params={"per_page": 50})
    wh_map = {w["id"]: w.get("name", w["id"]) for w in wh_data.get("items", [])}

    if product_id:
        # 單一商品
        data = api_get("product_stocks", path_params={"product_id": product_id})
        products_stocks = [data]
    else:
        # 全部商品（分頁取得商品列表，逐一查庫存）
        products = fetch_all_pages("products", max_pages=10)
        products_stocks = []
        import time as _time
        for p in products[:50]:  # 限制前 50 個以避免過慢
            try:
                stock = api_get("product_stocks", path_params={"product_id": p["id"]})
                products_stocks.append(stock)
                _time.sleep(0.2)
            except Exception:
                continue

    # 彙總
    warehouse_totals = defaultdict(lambda: {"total_quantity": 0, "sku_count": 0, "oos_skus": 0})
    product_details = []

    for ps in products_stocks:
        title = get_translation(ps.get("title_translations"))
        pid = ps.get("id", "")

        for v in ps.get("variations", []):
            fields = v.get("fields_translations", {}).get("zh-hant", [])
            sku = v.get("sku", "")
            color = fields[0] if len(fields) > 0 else ""
            size = fields[1] if len(fields) > 1 else ""

            stocks = v.get("stocks", [])
            variant_detail = {
                "product_title": title,
                "product_id": pid,
                "sku": sku,
                "color": color,
                "size": size,
                "warehouses": {},
            }

            for s in stocks:
                wid = s.get("warehouse_id", "")
                qty = s.get("quantity", 0)
                wname = wh_map.get(wid, wid)

                if warehouse_id and wid != warehouse_id:
                    continue

                variant_detail["warehouses"][wname] = qty
                warehouse_totals[wname]["total_quantity"] += qty
                warehouse_totals[wname]["sku_count"] += 1
                if qty == 0:
                    warehouse_totals[wname]["oos_skus"] += 1

            if variant_detail["warehouses"]:
                product_details.append(variant_detail)

    # 排序倉庫
    sorted_warehouses = sorted(warehouse_totals.items(), key=lambda x: -x[1]["total_quantity"])

    return {
        "products_queried": len(products_stocks),
        "total_variants": len(product_details),
        "warehouse_summary": {k: v for k, v in sorted_warehouses},
        "details": product_details[:100],  # 限制回傳筆數
    }
