"""
分類寫入 Tools — 建立、更新、刪除商品分類
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pydantic import Field

from app import mcp
from tools.base_tool import api_post, api_put, api_delete


@mcp.tool()
def create_category(
    category_data: dict = Field(description="分類資料，例如 {\"name\": \"夏季新品\", \"parent_id\": null}"),
) -> dict:
    """[WRITE] 建立新商品分類。

    【用途】
    在 Shopline 商店中建立新的商品分類，可指定父分類以建立層級結構。

    【呼叫的 Shopline API】
    - POST /v1/categories

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str, category: dict。

    【副作用】
    - 在商店分類列表中新增一筆分類記錄
    - 若 parent_id 不存在，API 可能回傳錯誤
    """
    result = api_post("category_create", json_body=category_data)

    category = result if "id" in result else result.get("item", result)
    category_id = category.get("id", "")
    name = category.get("name", category_id)
    return {
        "success": True,
        "resource_id": str(category_id),
        "message": f"分類「{name}」建立成功",
        "category": category,
    }


@mcp.tool()
def update_category(
    category_id: str = Field(description="分類 ID"),
    category_data: dict = Field(description="要更新的分類欄位，例如 {\"name\": \"冬季特賣\"}"),
) -> dict:
    """[WRITE] 更新商品分類資料。

    【用途】
    修改分類名稱、排序、父分類等屬性。僅傳入要修改的欄位，未傳入的欄位不會被覆蓋。

    【呼叫的 Shopline API】
    - PUT /v1/categories/{category_id}

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 分類資料變更立即生效，影響前台分類導覽顯示
    - 不可復原，但可再次呼叫此工具覆蓋
    """
    api_put("category_update", json_body=category_data,
            path_params={"category_id": category_id})
    return {
        "success": True,
        "resource_id": category_id,
        "message": f"分類 {category_id} 資料已更新",
    }


@mcp.tool()
def delete_category(
    category_id: str = Field(description="分類 ID"),
) -> dict:
    """[WRITE] 刪除商品分類。

    【用途】
    從 Shopline 商店中永久刪除指定分類。適合清除已停用或錯誤建立的分類。

    【呼叫的 Shopline API】
    - DELETE /v1/categories/{category_id}

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 永久刪除分類記錄，不可復原
    - 原本屬於此分類的商品將解除分類關聯，商品本身不會被刪除
    - 若有子分類，子分類的父分類關聯可能一併受影響（視 Shopline 實作而定）
    """
    api_delete("category_delete", path_params={"category_id": category_id})
    return {
        "success": True,
        "resource_id": category_id,
        "message": f"分類 {category_id} 已刪除，關聯商品已解除分類",
    }
