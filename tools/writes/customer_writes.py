"""
客戶寫入 Tools — 建立、更新、刪除客戶；標籤、儲值金、點數調整
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from typing import Optional, List
from pydantic import Field

from app import mcp
from tools.base_tool import api_post, api_put, api_delete, resolve_field


@mcp.tool()
def create_customer(
    name: str = Field(description="客戶姓名"),
    email: Optional[str] = Field(default=None, description="Email"),
    phone: Optional[str] = Field(default=None, description="電話"),
    gender: Optional[str] = Field(default=None, description="性別 (male/female/other)"),
    birthday: Optional[str] = Field(default=None, description="生日 YYYY-MM-DD"),
    tags: Optional[List[str]] = Field(default=None, description="標籤列表"),
) -> dict:
    """[WRITE] 建立新客戶。

    【用途】
    在 Shopline 商店中建立新的客戶記錄。適合客服手動建檔或批次匯入場景。

    【呼叫的 Shopline API】
    - POST /v1/customers

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str, customer: dict。

    【副作用】
    - 在商店客戶列表中新增一筆客戶
    - 如果 email 或 phone 已存在，可能會失敗（Shopline 可能不允許重複）
    """
    email, phone, gender, birthday, tags = (
        resolve_field(v) for v in (email, phone, gender, birthday, tags)
    )
    body = {"name": name}
    if email:
        body["email"] = email
    if phone:
        body["phone"] = phone
    if gender:
        body["gender"] = gender
    if birthday:
        body["birthday"] = birthday
    if tags:
        body["tags"] = tags

    result = api_post("customer_create", json_body=body)

    customer = result if "id" in result else result.get("item", result)
    return {
        "success": True,
        "resource_id": customer.get("id", ""),
        "message": f"客戶 {name} 建立成功",
        "customer": customer,
    }


@mcp.tool()
def update_customer(
    customer_id: str = Field(description="客戶內部 ID"),
    name: Optional[str] = Field(default=None, description="新姓名"),
    email: Optional[str] = Field(default=None, description="新 Email"),
    phone: Optional[str] = Field(default=None, description="新電話"),
    gender: Optional[str] = Field(default=None, description="性別 (male/female/other)"),
    birthday: Optional[str] = Field(default=None, description="生日 YYYY-MM-DD"),
) -> dict:
    """[WRITE] 更新客戶基本資料。

    【用途】
    修改客戶姓名、聯絡方式、生日等基本資料。僅傳入要修改的欄位，未傳入的欄位不會被覆蓋。

    【呼叫的 Shopline API】
    - PUT /v1/customers/{customer_id}

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 修改客戶資料，變更立即生效
    - 不可復原（無版本歷史），但可再次呼叫此工具覆蓋
    """
    body = {}
    if name is not None:
        body["name"] = name
    if email is not None:
        body["email"] = email
    if phone is not None:
        body["phone"] = phone
    if gender is not None:
        body["gender"] = gender
    if birthday is not None:
        body["birthday"] = birthday

    if not body:
        return {"success": False, "resource_id": customer_id, "message": "未提供任何要更新的欄位"}

    api_put("customer_update", json_body=body, path_params={"customer_id": customer_id})
    return {
        "success": True,
        "resource_id": customer_id,
        "message": f"客戶 {customer_id} 資料已更新",
    }


@mcp.tool()
def delete_customer(
    customer_id: str = Field(description="客戶內部 ID"),
) -> dict:
    """[WRITE] 刪除客戶。

    【用途】
    從 Shopline 商店中刪除客戶記錄。通常用於清除測試資料或 GDPR 合規需求。

    【呼叫的 Shopline API】
    - DELETE /v1/customers/{customer_id}

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 永久刪除客戶記錄，不可復原
    - 客戶相關的訂單紀錄可能仍保留（取決於 Shopline 實作）
    """
    api_delete("customer_delete", path_params={"customer_id": customer_id})
    return {
        "success": True,
        "resource_id": customer_id,
        "message": f"客戶 {customer_id} 已刪除",
    }


@mcp.tool()
def update_customer_tags(
    customer_id: str = Field(description="客戶內部 ID"),
    tags: List[str] = Field(description="標籤列表（會取代現有標籤）"),
) -> dict:
    """[WRITE] 設定客戶標籤（覆蓋現有標籤）。

    【用途】
    為客戶設定標籤，常用於行銷分群、VIP 標記等。注意：會覆蓋客戶現有的所有標籤。

    【呼叫的 Shopline API】
    - PUT /v1/customers/{customer_id}/tags
    - POST /v1/customers/{customer_id}/tags

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 覆蓋客戶的所有現有標籤為新的標籤列表
    - 若要新增標籤而非覆蓋，請先用 get_customer_profile 取得現有標籤再合併
    """
    api_put("customer_tags", json_body={"tags": tags},
            path_params={"customer_id": customer_id})
    return {
        "success": True,
        "resource_id": customer_id,
        "message": f"客戶 {customer_id} 標籤已更新為 {tags}",
    }


@mcp.tool()
def update_customer_store_credits(
    customer_id: str = Field(description="客戶內部 ID"),
    amount: float = Field(description="調整金額（正數=增加，負數=扣除）"),
    note: Optional[str] = Field(default=None, description="調整備註/原因"),
) -> dict:
    """[WRITE] 調整客戶儲值金餘額。

    【用途】
    增加或扣除客戶儲值金，常用於儲值金充值、退款補償、活動贈送等場景。

    【呼叫的 Shopline API】
    - PUT /v1/customers/{customer_id}/store-credits

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 客戶儲值金餘額立即變動
    - 異動紀錄會寫入客戶的儲值金歷史（可透過 get_customer_profile 查看）
    - 扣除後如餘額不足，API 可能回傳錯誤
    """
    body = {"amount": amount}
    if note:
        body["note"] = note

    api_put("customer_store_credits_update", json_body=body,
            path_params={"customer_id": customer_id})
    return {
        "success": True,
        "resource_id": customer_id,
        "message": f"客戶 {customer_id} 儲值金已調整 {amount:+.2f}",
    }


@mcp.tool()
def adjust_customer_member_points(
    customer_id: str = Field(description="客戶內部 ID"),
    points: int = Field(description="調整點數（正數=增加，負數=扣除）"),
    note: Optional[str] = Field(default=None, description="調整備註/原因"),
) -> dict:
    """[WRITE] 調整客戶會員點數。

    【用途】
    增加或扣除客戶會員點數，常用於手動補點、活動贈點、客訴補償等場景。

    【呼叫的 Shopline API】
    - PUT /v1/customers/{customer_id}/member-points

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 客戶點數餘額立即變動
    - 異動紀錄會寫入客戶的點數歷史（可透過 get_customer_profile 查看）
    - 扣除後如點數不足，API 可能回傳錯誤
    """
    body = {"points": points}
    if note:
        body["note"] = note

    api_put("customer_member_points_update", json_body=body,
            path_params={"customer_id": customer_id})
    return {
        "success": True,
        "resource_id": customer_id,
        "message": f"客戶 {customer_id} 會員點數已調整 {points:+d}",
    }
