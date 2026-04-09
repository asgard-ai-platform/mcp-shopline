"""
分類 Tools — 商品分類樹狀結構、單一分類詳情
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import Optional
from pydantic import Field

from app import mcp
from tools.base_tool import api_get, fetch_all_pages, money_to_float, get_translation


@mcp.tool()
def get_category_tree() -> dict:
    """取得所有商品分類並組成樹狀結構。

    【用途】
    瀏覽商店的完整分類層級，了解分類架構與父子關係。
    可用於確認分類 ID、名稱，再搭配 get_category_detail 取得個別分類詳情，
    或搭配商品工具按分類篩選商品。

    【呼叫的 Shopline API】
    - GET /v1/categories

    【回傳結構】
    dict 含 total, tree[]（樹狀）, flat[]（扁平列表）。
    每個節點包含 id, name, parent_id, children[]（僅在 tree 中）。
    """
    items = fetch_all_pages("categories")

    flat = []
    for cat in items:
        flat.append({
            "id": cat.get("id"),
            "name": get_translation(cat.get("title_translations") or cat.get("name")),
            "parent_id": cat.get("parent_id"),
            "position": cat.get("position"),
            "created_at": cat.get("created_at"),
            "updated_at": cat.get("updated_at"),
        })

    # 組成樹狀結構
    id_to_node = {c["id"]: dict(c, children=[]) for c in flat}
    tree = []
    for node in id_to_node.values():
        parent_id = node.get("parent_id")
        if parent_id and parent_id in id_to_node:
            id_to_node[parent_id]["children"].append(node)
        else:
            tree.append(node)

    return {
        "total": len(flat),
        "tree": tree,
        "flat": flat,
    }


@mcp.tool()
def get_category_detail(
    category_id: str = Field(description="分類 ID（由 get_category_tree 回傳的 id 欄位）"),
) -> dict:
    """取得單一商品分類的完整詳情。

    【用途】
    查詢特定分類的名稱、描述、父分類等完整資訊。
    適合在已知分類 ID 的情況下取得詳細欄位。

    【呼叫的 Shopline API】
    - GET /v1/categories/{category_id}

    【回傳結構】
    dict 包含 id, name, parent_id, description, position, created_at, updated_at。
    """
    data = api_get("category_detail", path_params={"category_id": category_id})
    cat = data.get("item", data) if isinstance(data, dict) else data

    return {
        "id": cat.get("id"),
        "name": get_translation(cat.get("title_translations") or cat.get("name")),
        "parent_id": cat.get("parent_id"),
        "description": get_translation(cat.get("description_translations") or cat.get("description")),
        "position": cat.get("position"),
        "image_url": cat.get("image_url"),
        "created_at": cat.get("created_at"),
        "updated_at": cat.get("updated_at"),
    }
