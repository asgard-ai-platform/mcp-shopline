"""
配送方式 Tools — 商店配送選項與時段查詢
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import mcp
from tools.base_tool import api_get, get_translation


@mcp.tool()
def list_delivery_options() -> dict:
    """取得商店啟用的配送方式清單。

    【用途】
    查看商店目前設定的所有配送方式，例如宅配、超商取貨、
    門市自取等。適合確認可用配送渠道或分析訂單配送偏好。

    【呼叫的 Shopline API】
    - GET /v1/delivery_options

    【回傳結構】
    dict 含 total, delivery_options[]。
    每個 delivery_option 包含 id, name, delivery_type,
    enabled, position, price, created_at 等。
    """
    data = api_get("delivery_options")
    items = data.get("items", []) if isinstance(data, dict) else []

    results = []
    for d in items:
        results.append({
            "id": d.get("id"),
            "name": get_translation(d.get("name_translations")) or d.get("name"),
            "delivery_type": d.get("delivery_type"),
            "enabled": d.get("enabled"),
            "position": d.get("position"),
            "price": d.get("price"),
            "created_at": d.get("created_at"),
        })

    return {
        "total": len(results),
        "delivery_options": results,
    }


@mcp.tool()
def get_delivery_option_detail(delivery_option_id: str) -> dict:
    """取得指定配送方式的詳細資訊。

    【用途】
    查詢單一配送方式的完整設定，包含費率規則、地區限制、
    重量限制等。適合確認特定配送方式的詳細條件。

    【呼叫的 Shopline API】
    - GET /v1/delivery_options/{delivery_option_id}

    【回傳結構】
    dict 含配送方式詳細欄位：id, name, delivery_type,
    enabled, price, weight_limit, regions, created_at 等。
    """
    data = api_get(
        "delivery_option_detail",
        path_params={"delivery_option_id": delivery_option_id},
    )
    d = data.get("delivery_option", data) if isinstance(data, dict) else {}

    return {
        "id": d.get("id"),
        "name": get_translation(d.get("name_translations")) or d.get("name"),
        "delivery_type": d.get("delivery_type"),
        "enabled": d.get("enabled"),
        "position": d.get("position"),
        "price": d.get("price"),
        "weight_limit": d.get("weight_limit"),
        "regions": d.get("regions", []),
        "created_at": d.get("created_at"),
        "updated_at": d.get("updated_at"),
    }


@mcp.tool()
def get_delivery_time_slots(delivery_option_id: str) -> dict:
    """取得指定配送方式的可用時段清單。

    【用途】
    查詢特定配送方式的預約時段設定，例如到府配送的時間選項。
    適合確認預約配送時段或分析客戶配送時段偏好。

    【呼叫的 Shopline API】
    - GET /v1/delivery_options/{delivery_option_id}/time_slots

    【回傳結構】
    dict 含 delivery_option_id, total, time_slots[]。
    每個 time_slot 包含 id, day, start_time, end_time, enabled 等。
    """
    data = api_get(
        "delivery_option_time_slots",
        path_params={"delivery_option_id": delivery_option_id},
    )
    items = data.get("items", []) if isinstance(data, dict) else []

    results = []
    for ts in items:
        results.append({
            "id": ts.get("id"),
            "day": ts.get("day"),
            "start_time": ts.get("start_time"),
            "end_time": ts.get("end_time"),
            "enabled": ts.get("enabled"),
            "capacity": ts.get("capacity"),
        })

    return {
        "delivery_option_id": delivery_option_id,
        "total": len(results),
        "time_slots": results,
    }
