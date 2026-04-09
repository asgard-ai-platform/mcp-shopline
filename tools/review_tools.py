"""
商品評價相關 Tools — 評價列表、評價明細
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import Optional
from pydantic import Field

from app import mcp
from tools.base_tool import api_get, fetch_all_pages, money_to_float, get_translation


@mcp.tool()
def list_product_reviews(
    max_results: int = Field(default=50, description="最多回傳筆數"),
) -> dict:
    """取得商品評價列表。

    【用途】
    瀏覽所有商品評價的摘要清單，了解顧客對商品的整體評分與回饋。可用於監控
    評價品質、找出評分偏低的商品，或追蹤近期新增的評論。若需查看單一評價的
    完整內容（含圖片、店家回覆等），請改用 get_product_review_detail。

    【呼叫的 Shopline API】
    - GET /v1/product_review_comments

    【回傳結構】
    dict 含 total_found, returned, reviews[]。
    每個 review 包含 id, product_id, product_name（多語系翻譯優先取中文）,
    rating（評分，通常 1-5）, content（評價內容摘要）, created_at。
    """
    max_pages = max(1, max_results // 50)
    items = fetch_all_pages("product_review_comments", max_pages=max_pages)

    results = []
    for review in items[:max_results]:
        results.append({
            "id": review.get("id"),
            "product_id": review.get("product_id"),
            "product_name": (
                get_translation(review.get("product_title_translations"))
                or review.get("product_title")
            ),
            "rating": review.get("rating"),
            "content": review.get("content") or review.get("body"),
            "created_at": review.get("created_at"),
        })

    return {
        "total_found": len(items),
        "returned": len(results),
        "reviews": results,
    }


@mcp.tool()
def get_product_review_detail(
    comment_id: str = Field(description="評價 ID（由 list_product_reviews 回傳的 id 欄位）"),
) -> dict:
    """取得單一商品評價的完整內容，包含圖片與店家回覆。

    【用途】
    查閱特定評價的詳細資料：完整評論文字、評分、附圖、顧客資訊及店家回覆。
    適用於客服處理評價問題、追蹤店家回應進度，或人工審核評價內容。

    【呼叫的 Shopline API】
    - GET /v1/product_review_comments/{comment_id}

    【回傳結構】
    dict 包含：
    - id：評價 ID
    - product_id / product_name：商品資訊
    - rating：評分（通常 1–5）
    - content：完整評論文字
    - images[]：附圖 URL 列表
    - reviewer_name：評價者姓名
    - status：評價審核狀態（如 published, pending）
    - reply：店家回覆內容（若有）
    - created_at, updated_at
    """
    path_params = {"comment_id": comment_id}
    data = api_get("product_review_comment_detail", path_params=path_params)

    review = data if "id" in data else data.get("item", data)

    raw_images = review.get("images", [])
    images = []
    for img in raw_images:
        if isinstance(img, dict):
            images.append(img.get("url") or img.get("src"))
        elif isinstance(img, str):
            images.append(img)

    reply = review.get("reply") or review.get("merchant_reply")

    return {
        "id": review.get("id"),
        "product_id": review.get("product_id"),
        "product_name": (
            get_translation(review.get("product_title_translations"))
            or review.get("product_title")
        ),
        "rating": review.get("rating"),
        "content": review.get("content") or review.get("body"),
        "images": images,
        "reviewer_name": review.get("reviewer_name") or review.get("author"),
        "status": review.get("status"),
        "reply": reply,
        "created_at": review.get("created_at"),
        "updated_at": review.get("updated_at"),
    }
