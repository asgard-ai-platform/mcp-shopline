"""
商品寫入 Tools — 建立、更新、刪除商品；變體、庫存、價格、標籤、圖片、批次操作
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from typing import List

from pydantic import Field

from app import mcp
from tools.base_tool import api_post, api_put, api_delete


@mcp.tool()
def create_product(
    product_data: dict = Field(description="完整商品建立資料，依 Shopline API 規格傳入（含 title、description、price 等欄位）"),
) -> dict:
    """[WRITE] 建立新商品。

    【用途】
    在 Shopline 商店中建立一筆新的商品記錄。product_data 為完整的商品 body，
    應依 Shopline Open API 規格組裝（含名稱、描述、售價、SKU 等）。

    【呼叫的 Shopline API】
    - POST /v1/products

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str, product: dict。

    【副作用】
    - 商品立即在商店後台可見
    - 若 SKU 或 barcode 重複，API 可能回傳錯誤
    - 新商品預設狀態取決於 product_data 內的 status 欄位
    """
    result = api_post("product_create", json_body=product_data)
    product = result if "id" in result else result.get("item", result)
    return {
        "success": True,
        "resource_id": str(product.get("id", "")),
        "message": f"商品建立成功（ID: {product.get('id', '')}）",
        "product": product,
    }


@mcp.tool()
def update_product(
    product_id: str = Field(description="商品內部 ID"),
    product_data: dict = Field(description="要更新的商品欄位（僅需傳入要修改的欄位）"),
) -> dict:
    """[WRITE] 更新商品基本資料。

    【用途】
    修改現有商品的名稱、描述、分類、狀態等欄位。僅傳入要修改的欄位，
    未傳入的欄位不會被覆蓋。

    【呼叫的 Shopline API】
    - PUT /v1/products/{product_id}

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 商品資料變更立即生效，前台同步更新
    - 不可復原（無版本歷史），但可再次呼叫此工具覆蓋
    """
    if not product_data:
        return {"success": False, "resource_id": product_id, "message": "未提供任何要更新的欄位"}

    api_put("product_update", json_body=product_data, path_params={"product_id": product_id})
    return {
        "success": True,
        "resource_id": product_id,
        "message": f"商品 {product_id} 資料已更新",
    }


@mcp.tool()
def delete_product(
    product_id: str = Field(description="商品內部 ID"),
) -> dict:
    """[WRITE] 刪除商品。

    【用途】
    從 Shopline 商店中永久刪除商品記錄。通常用於清除下架商品或測試資料。

    【呼叫的 Shopline API】
    - DELETE /v1/products/{product_id}

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 永久刪除商品，不可復原
    - 商品相關的訂單行項目記錄可能仍保留（取決於 Shopline 實作）
    - 刪除後前台立即下架
    """
    api_delete("product_delete", path_params={"product_id": product_id})
    return {
        "success": True,
        "resource_id": product_id,
        "message": f"商品 {product_id} 已刪除",
    }


@mcp.tool()
def update_product_quantity(
    product_id: str = Field(description="商品內部 ID"),
    quantity: int = Field(description="新庫存數量（絕對值，非增減量）"),
) -> dict:
    """[WRITE] 更新商品庫存數量（無變體商品）。

    【用途】
    直接設定無變體商品的庫存數量。適用於盤點後調整庫存或手動補貨場景。
    若商品有變體，請改用 update_variation_quantity。

    【呼叫的 Shopline API】
    - PUT /v1/products/{product_id}/quantity

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 庫存數量立即更新，影響前台可購買數量
    - 若設為 0 且商品設定不允許超賣，前台將顯示缺貨
    """
    api_put("product_quantity", json_body={"quantity": quantity},
            path_params={"product_id": product_id})
    return {
        "success": True,
        "resource_id": product_id,
        "message": f"商品 {product_id} 庫存已更新為 {quantity}",
    }


@mcp.tool()
def update_product_price(
    product_id: str = Field(description="商品內部 ID"),
    price: float = Field(description="新售價（TWD）"),
) -> dict:
    """[WRITE] 更新商品售價（無變體商品）。

    【用途】
    直接設定無變體商品的售價。適用於調價、促銷結束恢復原價等場景。
    若商品有變體，請改用 update_variation_price。

    【呼叫的 Shopline API】
    - PUT /v1/products/{product_id}/price

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 售價立即更新，前台同步顯示新價格
    - 不影響進行中的訂單（訂單成立時已鎖定價格）
    """
    api_put("product_price", json_body={"price": price},
            path_params={"product_id": product_id})
    return {
        "success": True,
        "resource_id": product_id,
        "message": f"商品 {product_id} 售價已更新為 {price:.2f}",
    }


@mcp.tool()
def create_product_variation(
    product_id: str = Field(description="商品內部 ID"),
    variation_data: dict = Field(description="變體資料（含 SKU、價格、庫存、規格選項等）"),
) -> dict:
    """[WRITE] 為商品新增變體。

    【用途】
    在現有商品下建立新的規格變體（如顏色、尺寸等）。variation_data 應依
    Shopline Open API 規格組裝，含 SKU、價格、庫存等欄位。

    【呼叫的 Shopline API】
    - POST /v1/products/{product_id}/variations

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str, variation: dict。

    【副作用】
    - 變體立即加入商品，前台可供選擇
    - 若 SKU 重複，API 可能回傳錯誤
    """
    result = api_post("product_variations_create", json_body=variation_data,
                      path_params={"product_id": product_id})
    variation = result if "id" in result else result.get("item", result)
    return {
        "success": True,
        "resource_id": str(variation.get("id", "")),
        "message": f"商品 {product_id} 新增變體成功（變體 ID: {variation.get('id', '')}）",
        "variation": variation,
    }


@mcp.tool()
def update_product_variation(
    product_id: str = Field(description="商品內部 ID"),
    variation_id: str = Field(description="變體內部 ID"),
    variation_data: dict = Field(description="要更新的變體欄位（僅需傳入要修改的欄位）"),
) -> dict:
    """[WRITE] 更新商品變體資料。

    【用途】
    修改特定商品變體的 SKU、規格選項、狀態等欄位。僅傳入要修改的欄位，
    未傳入的欄位不會被覆蓋。

    【呼叫的 Shopline API】
    - PUT /v1/products/{product_id}/variations/{variation_id}

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 變體資料變更立即生效，前台同步更新
    - 不可復原（無版本歷史），但可再次呼叫此工具覆蓋
    """
    if not variation_data:
        return {"success": False, "resource_id": variation_id, "message": "未提供任何要更新的欄位"}

    api_put("product_variation_update", json_body=variation_data,
            path_params={"product_id": product_id, "variation_id": variation_id})
    return {
        "success": True,
        "resource_id": variation_id,
        "message": f"商品 {product_id} 的變體 {variation_id} 已更新",
    }


@mcp.tool()
def delete_product_variation(
    product_id: str = Field(description="商品內部 ID"),
    variation_id: str = Field(description="變體內部 ID"),
) -> dict:
    """[WRITE] 刪除商品變體。

    【用途】
    從商品中永久刪除指定的規格變體。適用於停售特定規格或清理錯誤變體。

    【呼叫的 Shopline API】
    - DELETE /v1/products/{product_id}/variations/{variation_id}

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 永久刪除變體，不可復原
    - 若該變體為商品唯一變體，刪除後商品可能無法購買
    - 刪除後前台立即移除該規格選項
    """
    api_delete("product_variation_delete",
               path_params={"product_id": product_id, "variation_id": variation_id})
    return {
        "success": True,
        "resource_id": variation_id,
        "message": f"商品 {product_id} 的變體 {variation_id} 已刪除",
    }


@mcp.tool()
def update_variation_quantity(
    product_id: str = Field(description="商品內部 ID"),
    variation_id: str = Field(description="變體內部 ID"),
    quantity: int = Field(description="新庫存數量（絕對值，非增減量）"),
) -> dict:
    """[WRITE] 更新商品變體庫存數量。

    【用途】
    直接設定特定變體的庫存數量。適用於盤點後調整庫存或手動補貨場景。
    若要批次更新多個 SKU 庫存，可改用 bulk_update_quantities。

    【呼叫的 Shopline API】
    - PUT /v1/products/{product_id}/variations/{variation_id}/quantity

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 庫存數量立即更新，影響前台可購買數量
    - 若設為 0 且商品設定不允許超賣，前台將顯示缺貨
    """
    api_put("product_variation_quantity", json_body={"quantity": quantity},
            path_params={"product_id": product_id, "variation_id": variation_id})
    return {
        "success": True,
        "resource_id": variation_id,
        "message": f"商品 {product_id} 變體 {variation_id} 庫存已更新為 {quantity}",
    }


@mcp.tool()
def update_variation_price(
    product_id: str = Field(description="商品內部 ID"),
    variation_id: str = Field(description="變體內部 ID"),
    price: float = Field(description="新售價（TWD）"),
) -> dict:
    """[WRITE] 更新商品變體售價。

    【用途】
    直接設定特定變體的售價。適用於個別規格調價、限時特價等場景。

    【呼叫的 Shopline API】
    - PUT /v1/products/{product_id}/variations/{variation_id}/price

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 售價立即更新，前台同步顯示新價格
    - 不影響進行中的訂單（訂單成立時已鎖定價格）
    """
    api_put("product_variation_price", json_body={"price": price},
            path_params={"product_id": product_id, "variation_id": variation_id})
    return {
        "success": True,
        "resource_id": variation_id,
        "message": f"商品 {product_id} 變體 {variation_id} 售價已更新為 {price:.2f}",
    }


@mcp.tool()
def update_product_tags(
    product_id: str = Field(description="商品內部 ID"),
    tags: List[str] = Field(description="標籤列表（會取代現有標籤）"),
) -> dict:
    """[WRITE] 設定商品標籤（覆蓋現有標籤）。

    【用途】
    為商品設定標籤，常用於商品分群、促銷標記、SEO 分類等。
    注意：此操作會覆蓋商品現有的所有標籤。

    【呼叫的 Shopline API】
    - POST /v1/products/{product_id}/tags

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 覆蓋商品的所有現有標籤為新的標籤列表
    - 若要新增標籤而非覆蓋，請先用 get_product_list 取得現有標籤再合併後傳入
    """
    api_post("product_tags", json_body={"tags": tags},
             path_params={"product_id": product_id})
    return {
        "success": True,
        "resource_id": product_id,
        "message": f"商品 {product_id} 標籤已更新為 {tags}",
    }


@mcp.tool()
def add_product_images(
    product_id: str = Field(description="商品內部 ID"),
    image_urls: List[str] = Field(description="圖片 URL 列表（公開可存取的圖片連結）"),
) -> dict:
    """[WRITE] 為商品新增圖片。

    【用途】
    上傳圖片 URL 至商品相簿，圖片會被加入到現有圖片之後。
    適用於新增商品展示圖、情境圖等。

    【呼叫的 Shopline API】
    - POST /v1/products/{product_id}/images

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str, images: list。

    【副作用】
    - 圖片加入商品相簿，前台立即可見
    - 圖片 URL 必須為公開可存取的連結，Shopline 將下載並儲存
    - 圖片數量上限取決於 Shopline 商店方案設定
    """
    result = api_post("product_images", json_body={"image_urls": image_urls},
                      path_params={"product_id": product_id})
    images = result.get("items", result.get("images", []))
    return {
        "success": True,
        "resource_id": product_id,
        "message": f"商品 {product_id} 已新增 {len(image_urls)} 張圖片",
        "images": images,
    }


@mcp.tool()
def delete_product_images(
    product_id: str = Field(description="商品內部 ID"),
    image_ids: List[str] = Field(description="要刪除的圖片 ID 列表"),
) -> dict:
    """[WRITE] 刪除商品圖片。

    【用途】
    從商品相簿中刪除指定圖片。適用於移除過時圖片或錯誤上傳的圖片。

    【呼叫的 Shopline API】
    - DELETE /v1/products/{product_id}/images

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 永久刪除指定圖片，不可復原
    - 若被刪除的圖片為商品主圖，商品主圖將自動替換為相簿中下一張圖片
    """
    api_delete("product_images", json_body={"image_ids": image_ids},
               path_params={"product_id": product_id})
    return {
        "success": True,
        "resource_id": product_id,
        "message": f"商品 {product_id} 已刪除 {len(image_ids)} 張圖片（IDs: {image_ids}）",
    }


@mcp.tool()
def bulk_update_quantities(
    updates: List[dict] = Field(
        description="庫存更新列表，每筆為 {sku: str, quantity: int}，以 SKU 識別商品/變體"
    ),
) -> dict:
    """[WRITE] 批次更新多個 SKU 的庫存數量。

    【用途】
    一次更新多個商品或變體的庫存，適用於盤點後大批調整、進貨入庫等場景。
    比逐一呼叫 update_product_quantity / update_variation_quantity 更有效率。

    【呼叫的 Shopline API】
    - PUT /v1/products/bulk-update-quantities

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str, updated_count: int。

    【副作用】
    - 所有 SKU 的庫存數量立即更新，影響前台可購買數量
    - 若某 SKU 不存在，API 可能略過或回傳錯誤（取決於 Shopline 實作）
    - 建議先確認 SKU 正確後再執行批次操作
    """
    api_put("products_bulk_quantities", json_body={"updates": updates})
    return {
        "success": True,
        "resource_id": "bulk",
        "message": f"批次更新 {len(updates)} 筆 SKU 庫存完成",
        "updated_count": len(updates),
    }


@mcp.tool()
def bulk_assign_categories(
    product_ids: List[str] = Field(description="商品 ID 列表"),
    category_ids: List[str] = Field(description="要指派的分類 ID 列表"),
) -> dict:
    """[WRITE] 批次將多個商品指派至指定分類。

    【用途】
    一次將多個商品加入一或多個分類，適用於新季商品上架分類、重新整理分類結構等場景。
    比逐一更新商品分類更有效率。

    【呼叫的 Shopline API】
    - POST /v1/products/bulk-assign-categories

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str, product_count: int, category_count: int。

    【副作用】
    - 商品與分類的關聯立即生效，前台分類頁面同步更新
    - 此操作為新增關聯（非覆蓋），商品原有的分類不會被移除
    - 若商品或分類 ID 不存在，API 可能略過或回傳錯誤
    """
    api_post("products_bulk_categories",
             json_body={"product_ids": product_ids, "category_ids": category_ids})
    return {
        "success": True,
        "resource_id": "bulk",
        "message": f"已將 {len(product_ids)} 件商品批次指派至 {len(category_ids)} 個分類",
        "product_count": len(product_ids),
        "category_count": len(category_ids),
    }
