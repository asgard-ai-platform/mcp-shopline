"""
贈品與加購商品寫入 Tools — 建立、更新贈品與加購商品；調整庫存數量
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pydantic import Field

from app import mcp
from tools.base_tool import api_post, api_put, api_patch


@mcp.tool()
def create_gift(
    gift_data: dict = Field(description="贈品資料，例如 {name, sku, quantity, ...}"),
) -> dict:
    """[WRITE] 建立新贈品。

    【用途】
    在 Shopline 商店中建立一個新的贈品記錄，可搭配促銷活動使用。

    【呼叫的 Shopline API】
    - POST /v1/gifts

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str, gift: dict。

    【副作用】
    - 在商店贈品列表中新增一筆記錄
    - 贈品建立後可透過促銷規則設定觸發條件
    """
    result = api_post("gift_create", json_body=gift_data)
    gift = result if "id" in result else result.get("item", result)
    return {
        "success": True,
        "resource_id": gift.get("id", ""),
        "message": f"贈品建立成功（ID: {gift.get('id', '')}）",
        "gift": gift,
    }


@mcp.tool()
def update_gift(
    gift_id: str = Field(description="贈品 ID"),
    gift_data: dict = Field(description="要更新的贈品欄位，例如 {name, quantity, ...}"),
) -> dict:
    """[WRITE] 更新贈品資料。

    【用途】
    修改指定贈品的名稱、數量、圖片等欄位。僅傳入要修改的欄位。

    【呼叫的 Shopline API】
    - PATCH /v1/gifts/{gift_id}

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 修改指定贈品的資料，變更立即生效
    - 不可復原，但可再次呼叫此工具覆蓋
    """
    if not gift_data:
        return {"success": False, "resource_id": gift_id, "message": "未提供任何要更新的欄位"}

    api_patch("gift_update", json_body=gift_data, path_params={"gift_id": gift_id})
    return {
        "success": True,
        "resource_id": gift_id,
        "message": f"贈品 {gift_id} 已更新",
    }


@mcp.tool()
def update_gift_quantity_by_sku(
    sku: str = Field(description="贈品 SKU 編號"),
    quantity: int = Field(description="新的庫存數量（絕對值，非差異）"),
) -> dict:
    """[WRITE] 依 SKU 更新贈品庫存數量。

    【用途】
    直接以 SKU 為索引更新贈品庫存數量，適合批次庫存同步場景。

    【呼叫的 Shopline API】
    - PATCH /v1/gifts/quantity-by-sku

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 指定 SKU 的贈品庫存數量將被覆蓋為新值
    - 庫存變動立即生效，影響贈品可用性
    """
    api_patch("gift_quantity_by_sku", json_body={"sku": sku, "quantity": quantity})
    return {
        "success": True,
        "resource_id": sku,
        "message": f"贈品 SKU {sku} 庫存已更新為 {quantity}",
    }


@mcp.tool()
def create_addon_product(
    addon_data: dict = Field(description="加購商品資料，例如 {name, sku, price, quantity, ...}"),
) -> dict:
    """[WRITE] 建立新加購商品。

    【用途】
    在 Shopline 商店中建立一個新的加購商品（Addon Product），可於結帳時讓顧客選購。

    【呼叫的 Shopline API】
    - POST /v1/addon_products

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str, addon_product: dict。

    【副作用】
    - 在商店加購商品列表中新增一筆記錄
    - 建立後需於促銷或商品設定中啟用才會顯示給顧客
    """
    result = api_post("addon_product_create", json_body=addon_data)
    addon = result if "id" in result else result.get("item", result)
    return {
        "success": True,
        "resource_id": addon.get("id", ""),
        "message": f"加購商品建立成功（ID: {addon.get('id', '')}）",
        "addon_product": addon,
    }


@mcp.tool()
def update_addon_product(
    addon_product_id: str = Field(description="加購商品 ID"),
    addon_data: dict = Field(description="要更新的加購商品欄位，例如 {name, price, ...}"),
) -> dict:
    """[WRITE] 更新加購商品資料。

    【用途】
    修改指定加購商品的名稱、價格、圖片等欄位。僅傳入要修改的欄位。

    【呼叫的 Shopline API】
    - PUT /v1/addon_products/{addon_product_id}

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 修改指定加購商品的資料，變更立即生效
    - 不可復原，但可再次呼叫此工具覆蓋
    """
    if not addon_data:
        return {"success": False, "resource_id": addon_product_id, "message": "未提供任何要更新的欄位"}

    api_put("addon_product_update", json_body=addon_data,
            path_params={"addon_product_id": addon_product_id})
    return {
        "success": True,
        "resource_id": addon_product_id,
        "message": f"加購商品 {addon_product_id} 已更新",
    }


@mcp.tool()
def update_addon_product_quantity(
    addon_product_id: str = Field(description="加購商品 ID"),
    quantity: int = Field(description="新的庫存數量（絕對值，非差異）"),
) -> dict:
    """[WRITE] 更新加購商品庫存數量。

    【用途】
    直接以 ID 更新指定加購商品的庫存數量。

    【呼叫的 Shopline API】
    - PUT /v1/addon_products/{addon_product_id}/quantity

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 指定加購商品的庫存數量將被覆蓋為新值
    - 庫存變動立即生效
    """
    api_put("addon_product_quantity", json_body={"quantity": quantity},
            path_params={"addon_product_id": addon_product_id})
    return {
        "success": True,
        "resource_id": addon_product_id,
        "message": f"加購商品 {addon_product_id} 庫存已更新為 {quantity}",
    }


@mcp.tool()
def update_addon_product_quantity_by_sku(
    sku: str = Field(description="加購商品 SKU 編號"),
    quantity: int = Field(description="新的庫存數量（絕對值，非差異）"),
) -> dict:
    """[WRITE] 依 SKU 更新加購商品庫存數量。

    【用途】
    直接以 SKU 為索引更新加購商品庫存數量，適合批次庫存同步場景。

    【呼叫的 Shopline API】
    - PUT /v1/addon_products/sku/quantity

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 指定 SKU 的加購商品庫存數量將被覆蓋為新值
    - 庫存變動立即生效
    """
    api_put("addon_product_sku_quantity", json_body={"sku": sku, "quantity": quantity})
    return {
        "success": True,
        "resource_id": sku,
        "message": f"加購商品 SKU {sku} 庫存已更新為 {quantity}",
    }
