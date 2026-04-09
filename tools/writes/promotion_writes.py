"""
促銷寫入 Tools — 促銷活動、優惠券、快閃價格、聯盟行銷活動的建立、更新、刪除
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from typing import Optional
from pydantic import Field

from app import mcp
from tools.base_tool import api_post, api_put, api_delete


# =====================================================================
# 促銷活動 (Promotions)
# =====================================================================

@mcp.tool()
def create_promotion(
    promotion_data: dict = Field(description="促銷活動資料（參考 Shopline promotion 物件結構）"),
) -> dict:
    """[WRITE] 建立新促銷活動。

    【用途】
    在 Shopline 商店中建立新的促銷活動，例如折扣碼、買一送一、滿額折扣等。

    【呼叫的 Shopline API】
    - POST /v1/promotions

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str, promotion: dict。

    【副作用】
    - 在商店促銷列表中新增一筆促銷活動，活動狀態依 promotion_data 設定而定
    - 若活動設定為立即啟用，消費者即可使用該促銷
    - 促銷規則設定後如需修改，請使用 update_promotion
    """
    result = api_post("promotion_create", json_body=promotion_data)

    promotion = result if "id" in result else result.get("item", result)
    return {
        "success": True,
        "resource_id": promotion.get("id", ""),
        "message": f"促銷活動建立成功（ID: {promotion.get('id', '')}）",
        "promotion": promotion,
    }


@mcp.tool()
def update_promotion(
    promotion_id: str = Field(description="促銷活動 ID"),
    promotion_data: dict = Field(description="要更新的促銷活動欄位（僅傳入需修改的欄位）"),
) -> dict:
    """[WRITE] 更新既有促銷活動。

    【用途】
    修改已建立的促銷活動內容，例如調整折扣金額、有效期限、適用條件等。

    【呼叫的 Shopline API】
    - PUT /v1/promotions/{promotion_id}

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 修改立即生效，已在結帳流程中的消費者可能受影響
    - 不可復原（無版本歷史），但可再次呼叫此工具覆蓋
    """
    if not promotion_data:
        return {
            "success": False,
            "resource_id": promotion_id,
            "message": "未提供任何要更新的欄位",
        }

    api_put("promotion_update", json_body=promotion_data,
            path_params={"promotion_id": promotion_id})
    return {
        "success": True,
        "resource_id": promotion_id,
        "message": f"促銷活動 {promotion_id} 已更新",
    }


@mcp.tool()
def delete_promotion(
    promotion_id: str = Field(description="促銷活動 ID"),
) -> dict:
    """[WRITE] 刪除促銷活動。

    【用途】
    永久刪除指定的促銷活動。通常用於清除過期、測試或錯誤建立的活動。

    【呼叫的 Shopline API】
    - DELETE /v1/promotions/{promotion_id}

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 永久刪除該促銷活動，不可復原
    - 刪除後消費者無法再使用與該活動相關的折扣碼或優惠
    - 已套用該促銷的歷史訂單不受影響
    """
    api_delete("promotion_delete", path_params={"promotion_id": promotion_id})
    return {
        "success": True,
        "resource_id": promotion_id,
        "message": f"促銷活動 {promotion_id} 已刪除",
    }


# =====================================================================
# 優惠券 (Coupons)
# =====================================================================

@mcp.tool()
def send_coupon(
    coupon_data: dict = Field(description="優惠券發送資料，通常包含 coupon_id 與目標客戶識別資訊"),
) -> dict:
    """[WRITE] 發送優惠券給指定客戶。

    【用途】
    主動將優惠券發送給特定客戶，常用於行銷活動、客戶回饋、CRM 觸發場景。

    【呼叫的 Shopline API】
    - POST /v1/coupons/send

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str, result: dict。

    【副作用】
    - 優惠券發送後，目標客戶帳號中將出現對應的優惠券
    - 依優惠券設定，可能有數量限制；若庫存不足，API 會回傳錯誤
    - 部分類型的優惠券一旦發送，無法收回
    """
    result = api_post("coupon_send", json_body=coupon_data)

    item = result if isinstance(result, dict) else {}
    return {
        "success": True,
        "resource_id": item.get("id", ""),
        "message": "優惠券發送成功",
        "result": item,
    }


@mcp.tool()
def redeem_coupon(
    coupon_data: dict = Field(description="優惠券核銷資料，通常包含 coupon_code 與訂單或客戶識別資訊"),
) -> dict:
    """[WRITE] 核銷（使用）優惠券。

    【用途】
    在結帳或特定場景下核銷優惠券，將優惠券標記為已使用狀態。
    適合 POS 場景或 API 整合的結帳流程。

    【呼叫的 Shopline API】
    - POST /v1/coupons/redeem

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str, result: dict。

    【副作用】
    - 優惠券狀態變更為已使用，不可再次使用（一次性優惠券）
    - 核銷紀錄會寫入系統，影響促銷統計報告
    - 操作通常不可逆，請確認核銷對象與條件正確
    """
    result = api_post("coupon_redeem", json_body=coupon_data)

    item = result if isinstance(result, dict) else {}
    return {
        "success": True,
        "resource_id": item.get("id", ""),
        "message": "優惠券核銷成功",
        "result": item,
    }


@mcp.tool()
def claim_coupon(
    coupon_data: dict = Field(description="優惠券領取資料，通常包含 coupon_code 與客戶識別資訊"),
) -> dict:
    """[WRITE] 客戶領取優惠券。

    【用途】
    代表客戶領取（claim）一張優惠券，將優惠券綁定至該客戶帳號。
    適合兌換碼場景或 API 整合的會員領券流程。

    【呼叫的 Shopline API】
    - POST /v1/coupons/claim

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str, result: dict。

    【副作用】
    - 優惠券與指定客戶綁定，消費者帳號中可看到此優惠券
    - 若優惠券已達領取上限或已過期，API 會回傳錯誤
    - 同一張優惠券通常每位客戶只能領取一次（依設定而異）
    """
    result = api_post("coupon_claim", json_body=coupon_data)

    item = result if isinstance(result, dict) else {}
    return {
        "success": True,
        "resource_id": item.get("id", ""),
        "message": "優惠券領取成功",
        "result": item,
    }


# =====================================================================
# 快閃價格活動 (Flash Price Campaigns)
# =====================================================================

@mcp.tool()
def create_flash_price_campaign(
    campaign_data: dict = Field(description="快閃價格活動資料（參考 Shopline flash_price_campaign 物件結構）"),
) -> dict:
    """[WRITE] 建立快閃價格活動。

    【用途】
    建立限時特價活動（Flash Sale），在指定時段內將商品調整為特定價格。
    適合節慶特賣、清倉、限時搶購等場景。

    【呼叫的 Shopline API】
    - POST /v1/flash_price_campaigns

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str, campaign: dict。

    【副作用】
    - 活動建立後，依設定的開始時間自動啟用特價
    - 活動期間，符合條件的商品會顯示特價，影響商店前台的價格呈現
    - 若活動時段與其他促銷重疊，需確認優先規則
    """
    result = api_post("flash_price_campaign_create", json_body=campaign_data)

    campaign = result if "id" in result else result.get("item", result)
    return {
        "success": True,
        "resource_id": campaign.get("id", ""),
        "message": f"快閃價格活動建立成功（ID: {campaign.get('id', '')}）",
        "campaign": campaign,
    }


@mcp.tool()
def update_flash_price_campaign(
    campaign_id: str = Field(description="快閃價格活動 ID"),
    campaign_data: dict = Field(description="要更新的活動欄位（僅傳入需修改的欄位）"),
) -> dict:
    """[WRITE] 更新快閃價格活動。

    【用途】
    修改已建立的快閃價格活動，例如調整特價金額、活動時段或適用商品範圍。

    【呼叫的 Shopline API】
    - PUT /v1/flash_price_campaigns/{campaign_id}

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 修改立即生效；若活動正在進行中，前台價格即時更新
    - 不可復原（無版本歷史），但可再次呼叫此工具覆蓋
    """
    if not campaign_data:
        return {
            "success": False,
            "resource_id": campaign_id,
            "message": "未提供任何要更新的欄位",
        }

    api_put("flash_price_campaign_update", json_body=campaign_data,
            path_params={"campaign_id": campaign_id})
    return {
        "success": True,
        "resource_id": campaign_id,
        "message": f"快閃價格活動 {campaign_id} 已更新",
    }


@mcp.tool()
def delete_flash_price_campaign(
    campaign_id: str = Field(description="快閃價格活動 ID"),
) -> dict:
    """[WRITE] 刪除快閃價格活動。

    【用途】
    永久刪除指定的快閃價格活動。用於清除已結束、取消或錯誤建立的活動。

    【呼叫的 Shopline API】
    - DELETE /v1/flash_price_campaigns/{campaign_id}

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 永久刪除該活動，不可復原
    - 若活動正在進行中，刪除後商品立即恢復原價
    - 歷史訂單中已套用的特價不受影響
    """
    api_delete("flash_price_campaign_delete",
               path_params={"campaign_id": campaign_id})
    return {
        "success": True,
        "resource_id": campaign_id,
        "message": f"快閃價格活動 {campaign_id} 已刪除",
    }


# =====================================================================
# 聯盟行銷活動 (Affiliate Campaigns)
# =====================================================================

@mcp.tool()
def create_affiliate_campaign(
    campaign_data: dict = Field(description="聯盟行銷活動資料（參考 Shopline affiliate_campaign 物件結構）"),
) -> dict:
    """[WRITE] 建立聯盟行銷活動。

    【用途】
    建立聯盟行銷（Affiliate）活動，設定推薦獎勵規則，讓推廣夥伴（聯盟會員）
    透過分享連結或代碼帶來訂單並獲得佣金。

    【呼叫的 Shopline API】
    - POST /v1/affiliate_campaigns

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str, campaign: dict。

    【副作用】
    - 活動建立後，可將活動連結或代碼分發給聯盟夥伴
    - 活動啟用後，透過聯盟連結產生的訂單將自動計算佣金
    - 請確認佣金規則與結算方式設定正確，避免財務損失
    """
    result = api_post("affiliate_campaign_create", json_body=campaign_data)

    campaign = result if "id" in result else result.get("item", result)
    return {
        "success": True,
        "resource_id": campaign.get("id", ""),
        "message": f"聯盟行銷活動建立成功（ID: {campaign.get('id', '')}）",
        "campaign": campaign,
    }


@mcp.tool()
def update_affiliate_campaign(
    campaign_id: str = Field(description="聯盟行銷活動 ID"),
    campaign_data: dict = Field(description="要更新的活動欄位（僅傳入需修改的欄位）"),
) -> dict:
    """[WRITE] 更新聯盟行銷活動。

    【用途】
    修改已建立的聯盟行銷活動，例如調整佣金比例、活動期限或適用條件。

    【呼叫的 Shopline API】
    - PUT /v1/affiliate_campaigns/{campaign_id}

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 修改立即生效；佣金規則調整後，新訂單將套用新規則
    - 已產生的佣金紀錄不受影響（依各活動的歷史快照而定）
    - 不可復原（無版本歷史），但可再次呼叫此工具覆蓋
    """
    if not campaign_data:
        return {
            "success": False,
            "resource_id": campaign_id,
            "message": "未提供任何要更新的欄位",
        }

    api_put("affiliate_campaign_update", json_body=campaign_data,
            path_params={"campaign_id": campaign_id})
    return {
        "success": True,
        "resource_id": campaign_id,
        "message": f"聯盟行銷活動 {campaign_id} 已更新",
    }


@mcp.tool()
def delete_affiliate_campaign(
    campaign_id: str = Field(description="聯盟行銷活動 ID"),
) -> dict:
    """[WRITE] 刪除聯盟行銷活動。

    【用途】
    永久刪除指定的聯盟行銷活動。用於清除已結束、取消或錯誤建立的活動。

    【呼叫的 Shopline API】
    - DELETE /v1/affiliate_campaigns/{campaign_id}

    【回傳結構】
    dict 含 success: bool, resource_id: str, message: str。

    【副作用】
    - 永久刪除該活動，不可復原
    - 刪除後聯盟夥伴的推廣連結或代碼將失效，無法再追蹤新訂單
    - 已累積的佣金紀錄與歷史訂單資料不受影響（依 Shopline 實作而定）
    """
    api_delete("affiliate_campaign_delete",
               path_params={"campaign_id": campaign_id})
    return {
        "success": True,
        "resource_id": campaign_id,
        "message": f"聯盟行銷活動 {campaign_id} 已刪除",
    }
