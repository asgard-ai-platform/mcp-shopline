"""
媒體與元欄位寫入 Tools — 上傳媒體檔案、建立商家應用元欄位
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pydantic import Field

from app import mcp
from tools.base_tool import api_post


@mcp.tool()
def upload_media(
    media_data: dict = Field(
        description=(
            "媒體上傳資料。可能需要包含 file_url（遠端 URL）或 base64 編碼的檔案內容，"
            "視 Shopline API 支援的格式而定。"
            "範例：{\"file_url\": \"https://example.com/image.jpg\", \"type\": \"image\"}"
        )
    ),
) -> dict:
    """[WRITE] 上傳媒體檔案至 Shopline。

    【用途】
    上傳圖片或其他媒體檔案至 Shopline 媒體庫，上傳後可取得媒體 ID 供商品圖片等用途使用。
    注意：Shopline API 可能需要 multipart/form-data，本工具目前以 JSON body 傳送，
    若 API 回傳格式錯誤，請改用 multipart 上傳方式。

    【呼叫的 Shopline API】
    - POST /v1/media

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str, media: dict。

    【副作用】
    - 在 Shopline 媒體庫中新增一筆媒體記錄
    - 上傳的檔案將佔用商店的媒體儲存空間
    """
    result = api_post("media_create", json_body=media_data)
    media = result if "id" in result else result.get("item", result)
    return {
        "success": True,
        "resource_id": media.get("id", ""),
        "message": f"媒體上傳成功（ID: {media.get('id', '')}）",
        "media": media,
    }


@mcp.tool()
def create_metafield(
    metafield_data: dict = Field(
        description=(
            "元欄位資料，例如："
            "{\"namespace\": \"my_app\", \"key\": \"custom_key\", \"value\": \"custom_value\", \"value_type\": \"string\"}"
        )
    ),
) -> dict:
    """[WRITE] 建立商家應用元欄位（App Metafield）。

    【用途】
    為商家建立自定義的元欄位，用於儲存應用程式所需的額外商家設定或資料。

    【呼叫的 Shopline API】
    - POST /merchants/current/app-metafields

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str, metafield: dict。

    【副作用】
    - 在商家的應用元欄位中新增一筆記錄
    - 相同 namespace + key 組合若已存在，可能會失敗或覆蓋（取決於 Shopline 實作）
    """
    result = api_post("metafield_create", json_body=metafield_data)
    metafield = result if "id" in result else result.get("item", result)
    return {
        "success": True,
        "resource_id": metafield.get("id", ""),
        "message": f"元欄位建立成功（ID: {metafield.get('id', '')}）",
        "metafield": metafield,
    }
