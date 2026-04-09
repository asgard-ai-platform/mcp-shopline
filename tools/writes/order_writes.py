"""
訂單寫入 Tools — 取消、出貨、拆單、更新、建立訂單
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from typing import Optional, List

from pydantic import Field

from app import mcp
from tools.base_tool import api_post, api_patch, resolve_field


@mcp.tool()
def cancel_order(
    order_id: str = Field(description="訂單 ID"),
    reason: Optional[str] = Field(default=None, description="取消原因（選填）"),
) -> dict:
    """[WRITE] 取消訂單。

    【用途】
    取消指定訂單，適用於客戶要求取消、庫存不足或付款問題等場景。

    【呼叫的 Shopline API】
    - POST /v1/orders/{order_id}/cancel

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 訂單狀態變更為已取消，操作不可逆
    - 若訂單已出貨，可能無法取消（取決於 Shopline 規則）
    - 已付款訂單取消後需另行退款
    """
    reason = resolve_field(reason)
    body = {}
    if reason is not None:
        body["reason"] = reason

    result = api_post("order_cancel", json_body=body,
                      path_params={"order_id": order_id})

    order = result if "id" in result else result.get("item", result)
    return {
        "success": True,
        "resource_id": order.get("id", order_id),
        "message": f"訂單 {order_id} 已取消",
    }


@mcp.tool()
def execute_order_shipment(
    order_id: str = Field(description="訂單 ID"),
) -> dict:
    """[WRITE] 執行訂單出貨。

    【用途】
    將指定訂單標記為已出貨，觸發 Shopline 出貨流程，適用於倉庫確認出貨後的狀態更新。

    【呼叫的 Shopline API】
    - POST /v1/orders/{order_id}/shipment

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 訂單出貨狀態更新為已出貨
    - 可能觸發客戶出貨通知（取決於商店設定）
    - 訂單需處於可出貨狀態，否則 API 會回傳錯誤
    """
    result = api_post("order_shipment", json_body={},
                      path_params={"order_id": order_id})

    order = result if "id" in result else result.get("item", result)
    return {
        "success": True,
        "resource_id": order.get("id", order_id),
        "message": f"訂單 {order_id} 出貨執行成功",
    }


@mcp.tool()
def bulk_execute_shipment(
    order_ids: List[str] = Field(description="訂單 ID 列表，批次出貨"),
) -> dict:
    """[WRITE] 批次執行多訂單出貨。

    【用途】
    一次性將多筆訂單標記為已出貨，提升倉庫作業效率，適用於每日批量出貨場景。

    【呼叫的 Shopline API】
    - POST /v1/orders/shipment/bulk

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str, order_ids: list。

    【副作用】
    - 所有指定訂單的出貨狀態批次更新為已出貨
    - 部分訂單若無法出貨，API 可能整批失敗或回傳各別結果（取決於 Shopline 實作）
    - 可能觸發多封客戶出貨通知
    """
    body = {"order_ids": order_ids}
    result = api_post("orders_shipment_bulk", json_body=body)

    return {
        "success": True,
        "resource_id": ",".join(order_ids),
        "message": f"批次出貨成功，共 {len(order_ids)} 筆訂單",
        "order_ids": order_ids,
    }


@mcp.tool()
def split_order(
    order_id: str = Field(description="訂單 ID"),
    split_config: dict = Field(description="拆單設定，包含各子單的商品與配送資訊"),
) -> dict:
    """[WRITE] 拆分訂單為多個子出貨單。

    【用途】
    將一筆訂單拆分為多個子單，適用於商品分批到貨或不同倉庫分開出貨的場景。
    split_config 為字典，內容依 Shopline API 規格定義各子單。

    【呼叫的 Shopline API】
    - POST /v1/orders/{order_id}/split

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 原訂單被拆分為多個子訂單，原訂單狀態可能變更
    - 操作通常不可逆，請確認拆單設定正確後再執行
    - 已出貨的訂單無法拆單
    """
    result = api_post("order_split", json_body=split_config,
                      path_params={"order_id": order_id})

    order = result if "id" in result else result.get("item", result)
    return {
        "success": True,
        "resource_id": order.get("id", order_id),
        "message": f"訂單 {order_id} 拆單成功",
    }


@mcp.tool()
def update_order(
    order_id: str = Field(description="訂單 ID"),
    fields: dict = Field(description="要更新的欄位與值，以字典形式傳入"),
) -> dict:
    """[WRITE] 更新訂單欄位。

    【用途】
    修改訂單的可編輯欄位（如備註、配送地址等）。僅傳入要修改的欄位，未傳入欄位不受影響。

    【呼叫的 Shopline API】
    - PATCH /v1/orders/{order_id}

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 訂單資料立即變更，不可復原（可再次呼叫此工具覆蓋）
    - 部分欄位（如金額）可能受限於訂單狀態而無法修改
    """
    if not fields:
        return {
            "success": False,
            "resource_id": order_id,
            "message": "未提供任何要更新的欄位",
        }

    api_patch("order_update", json_body=fields,
              path_params={"order_id": order_id})
    return {
        "success": True,
        "resource_id": order_id,
        "message": f"訂單 {order_id} 已更新",
    }


@mcp.tool()
def update_order_status(
    order_id: str = Field(description="訂單 ID"),
    status: Optional[str] = Field(default=None, description="訂單狀態（如 confirmed / cancelled）"),
    delivery_status: Optional[str] = Field(default=None, description="配送狀態（如 shipped / delivered）"),
    payment_status: Optional[str] = Field(default=None, description="付款狀態（如 paid / unpaid）"),
) -> dict:
    """[WRITE] 更新訂單狀態（支援同時更新多種狀態）。

    【用途】
    分別或同時更新訂單的主狀態、配送狀態、付款狀態。
    僅傳入非 None 的參數，每個非 None 參數會各自呼叫一支 API。

    【呼叫的 Shopline API】
    - PATCH /v1/orders/{order_id}/status（若 status 非 None）
    - PATCH /v1/orders/{order_id}/delivery-status（若 delivery_status 非 None）
    - PATCH /v1/orders/{order_id}/payment-status（若 payment_status 非 None）

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str, updated_fields: list。

    【副作用】
    - 訂單狀態立即變更，影響前台顯示與後台報表
    - 狀態變更可能觸發客戶通知（取決於商店設定）
    - 非法的狀態值或不合法的狀態轉換會導致 API 回傳錯誤
    """
    status = resolve_field(status)
    delivery_status = resolve_field(delivery_status)
    payment_status = resolve_field(payment_status)
    if status is None and delivery_status is None and payment_status is None:
        return {
            "success": False,
            "resource_id": order_id,
            "message": "未提供任何狀態參數，至少需傳入一個狀態欄位",
            "updated_fields": [],
        }

    updated_fields = []

    if status is not None:
        api_patch("order_status", json_body={"status": status},
                  path_params={"order_id": order_id})
        updated_fields.append("status")

    if delivery_status is not None:
        api_patch("order_delivery_status",
                  json_body={"delivery_status": delivery_status},
                  path_params={"order_id": order_id})
        updated_fields.append("delivery_status")

    if payment_status is not None:
        api_patch("order_payment_status",
                  json_body={"payment_status": payment_status},
                  path_params={"order_id": order_id})
        updated_fields.append("payment_status")

    return {
        "success": True,
        "resource_id": order_id,
        "message": f"訂單 {order_id} 狀態已更新：{', '.join(updated_fields)}",
        "updated_fields": updated_fields,
    }


@mcp.tool()
def update_order_tags(
    order_id: str = Field(description="訂單 ID"),
    tags: List[str] = Field(description="標籤列表（會取代現有標籤）"),
) -> dict:
    """[WRITE] 設定訂單標籤（覆蓋現有標籤）。

    【用途】
    為訂單設定標籤，常用於訂單分類、優先處理標記、客服備註分群等場景。
    注意：會覆蓋訂單現有的所有標籤。

    【呼叫的 Shopline API】
    - PATCH /v1/orders/{order_id}/tags

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 覆蓋訂單的所有現有標籤為新的標籤列表
    - 若要新增標籤而非覆蓋，請先用 get_order_detail 取得現有標籤再合併
    """
    api_patch("order_tags_update", json_body={"tags": tags},
              path_params={"order_id": order_id})
    return {
        "success": True,
        "resource_id": order_id,
        "message": f"訂單 {order_id} 標籤已更新為 {tags}",
    }


@mcp.tool()
def create_order(
    order_data: dict = Field(description="完整訂單資料，依 Shopline API 規格傳入所有必要欄位"),
) -> dict:
    """[WRITE] 建立新訂單。

    【用途】
    在 Shopline 商店中手動建立新訂單，適用於電話訂購、客服補單、線下訂單轉入等場景。
    order_data 需包含 Shopline 建立訂單 API 所需的完整欄位。

    【呼叫的 Shopline API】
    - POST /v1/orders

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str, order: dict。

    【副作用】
    - 在商店訂單列表中新增一筆訂單
    - 可能觸發庫存扣減（取決於訂單內容與商店設定）
    - 可能觸發客戶訂單確認通知（取決於商店設定）
    - 建立後訂單立即生效，需確認資料正確再執行
    """
    result = api_post("order_create", json_body=order_data)

    order = result if "id" in result else result.get("item", result)
    return {
        "success": True,
        "resource_id": order.get("id", ""),
        "message": f"訂單建立成功，ID：{order.get('id', '（未知）')}",
        "order": order,
    }
