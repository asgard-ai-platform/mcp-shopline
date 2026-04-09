"""
商品評價寫入 Tools — 建立、更新、刪除商品評論（含批次操作）
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from typing import List
from pydantic import Field

from app import mcp
from tools.base_tool import api_post, api_patch, api_delete


@mcp.tool()
def create_product_review(
    review_data: dict = Field(
        description=(
            "評論資料，例如 {\"product_id\": \"P001\", \"rating\": 5, "
            "\"content\": \"品質很好！\", \"reviewer_name\": \"王小明\"}"
        )
    ),
) -> dict:
    """[WRITE] 建立單筆商品評論。

    【用途】
    為指定商品建立一筆顧客評論，適用於客服代為補登評論或匯入歷史評論資料。

    【呼叫的 Shopline API】
    - POST /v1/product_review_comments

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str, review: dict。

    【副作用】
    - 在商品評論列表中新增一筆評論，依商店設定可能立即公開或待審核
    - 影響商品的平均評分顯示
    """
    result = api_post("product_review_comment_create", json_body=review_data)

    review = result if "id" in result else result.get("item", result)
    comment_id = review.get("id", "")
    return {
        "success": True,
        "resource_id": str(comment_id),
        "message": f"商品評論 {comment_id} 建立成功",
        "review": review,
    }


@mcp.tool()
def bulk_create_product_reviews(
    reviews: List[dict] = Field(
        description=(
            "評論資料列表，每筆格式同 create_product_review，"
            "例如 [{\"product_id\": \"P001\", \"rating\": 5, \"content\": \"讚！\"}]"
        )
    ),
) -> dict:
    """[WRITE] 批次建立多筆商品評論。

    【用途】
    一次性批次建立多筆商品評論，適用於大量匯入歷史評論或促銷活動後的評論補登。

    【呼叫的 Shopline API】
    - POST /v1/product_review_comments/bulk

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str, result: dict。

    【副作用】
    - 批次在商品評論列表中新增多筆評論
    - 依商店設定，評論可能立即公開或待審核
    - 影響相關商品的平均評分顯示
    - 部分評論若格式錯誤，整批可能失敗或僅失敗該筆（視 API 實作而定）
    """
    result = api_post("product_review_comments_bulk_create", json_body={"comments": reviews})

    count = len(reviews)
    return {
        "success": True,
        "resource_id": "",
        "message": f"批次建立 {count} 筆商品評論成功",
        "result": result,
    }


@mcp.tool()
def update_product_review(
    comment_id: str = Field(description="評論 ID"),
    review_data: dict = Field(
        description="要更新的評論欄位，例如 {\"status\": \"published\", \"content\": \"修改後的評論\"}"
    ),
) -> dict:
    """[WRITE] 更新單筆商品評論。

    【用途】
    修改評論內容、審核狀態、評分等資料，適用於客服審核或編輯不當評論。

    【呼叫的 Shopline API】
    - PATCH /v1/product_review_comments/{comment_id}

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 評論資料變更立即生效
    - 若變更評分，商品平均評分將同步更新
    - 不可復原，但可再次呼叫此工具覆蓋
    """
    api_patch("product_review_comment_update", json_body=review_data,
              path_params={"comment_id": comment_id})
    return {
        "success": True,
        "resource_id": comment_id,
        "message": f"評論 {comment_id} 資料已更新",
    }


@mcp.tool()
def bulk_update_product_reviews(
    updates: List[dict] = Field(
        description=(
            "批次更新資料列表，每筆須含 id 欄位，"
            "例如 [{\"id\": \"C001\", \"status\": \"published\"}, {\"id\": \"C002\", \"status\": \"hidden\"}]"
        )
    ),
) -> dict:
    """[WRITE] 批次更新多筆商品評論。

    【用途】
    一次性批次審核或修改多筆評論狀態，適用於管理員批次公開或隱藏評論。

    【呼叫的 Shopline API】
    - PATCH /v1/product_review_comments

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str, result: dict。

    【副作用】
    - 批次更新多筆評論，變更立即生效
    - 若有評論狀態變更，相關商品的平均評分可能同步更新
    - 部分評論若 id 不存在，整批可能失敗或僅失敗該筆（視 API 實作而定）
    """
    result = api_patch("product_review_comments_bulk_update", json_body={"comments": updates})

    count = len(updates)
    return {
        "success": True,
        "resource_id": "",
        "message": f"批次更新 {count} 筆商品評論成功",
        "result": result,
    }


@mcp.tool()
def delete_product_review(
    comment_id: str = Field(description="評論 ID"),
) -> dict:
    """[WRITE] 刪除單筆商品評論。

    【用途】
    從 Shopline 商店中永久刪除指定評論，適用於移除違規、惡意或測試用評論。

    【呼叫的 Shopline API】
    - DELETE /v1/product_review_comments/{comment_id}

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 永久刪除評論記錄，不可復原
    - 商品的評論總數與平均評分將同步更新
    """
    api_delete("product_review_comment_delete",
               path_params={"comment_id": comment_id})
    return {
        "success": True,
        "resource_id": comment_id,
        "message": f"評論 {comment_id} 已刪除",
    }


@mcp.tool()
def bulk_delete_product_reviews(
    comment_ids: List[str] = Field(
        description="要刪除的評論 ID 列表，例如 [\"C001\", \"C002\", \"C003\"]"
    ),
) -> dict:
    """[WRITE] 批次刪除多筆商品評論。

    【用途】
    一次性永久刪除多筆評論，適用於批次清除測試資料或大量違規評論。

    【呼叫的 Shopline API】
    - DELETE /v1/product_review_comments

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str, deleted_count: int。

    【副作用】
    - 永久刪除多筆評論記錄，不可復原
    - 相關商品的評論總數與平均評分將同步更新
    - 部分 id 若不存在，整批可能失敗或僅失敗該筆（視 API 實作而定）
    """
    api_delete("product_review_comments_bulk_delete",
               params={"ids": comment_ids})
    count = len(comment_ids)
    return {
        "success": True,
        "resource_id": "",
        "message": f"已批次刪除 {count} 筆商品評論",
        "deleted_count": count,
    }
