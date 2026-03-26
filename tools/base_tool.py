"""
Shopline API 基底工具 — 認證、分頁、錯誤處理共用邏輯
"""
import requests
import time
from config.settings import get_headers, get_url, DEFAULT_PER_PAGE


class ShoplineAPIError(Exception):
    def __init__(self, status_code, message, endpoint=""):
        self.status_code = status_code
        self.message = message
        self.endpoint = endpoint
        super().__init__(f"[{status_code}] {endpoint}: {message}")


def api_get(endpoint_key, params=None, path_params=None, retries=3):
    """發送 GET 請求到 Shopline API，回傳 JSON。含自動重試。"""
    path_params = path_params or {}
    url = get_url(endpoint_key, **path_params)
    headers = get_headers()

    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=60)
            if resp.status_code != 200:
                raise ShoplineAPIError(resp.status_code, resp.text[:500], url)
            return resp.json()
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # 1s, 2s, 4s
                continue
            raise


def fetch_all_pages(endpoint_key, params=None, path_params=None, max_pages=None):
    """自動分頁遍歷，回傳所有 items"""
    params = dict(params or {})
    params.setdefault("per_page", DEFAULT_PER_PAGE)
    # orders_search 不支援 sort_by 參數
    if "search" not in endpoint_key:
        params.setdefault("sort_by", "desc")

    all_items = []
    page = 1

    while True:
        if max_pages and page > max_pages:
            break

        params["page"] = page
        data = api_get(endpoint_key, params=params, path_params=path_params)

        items = data.get("items", [])
        all_items.extend(items)

        pagination = data.get("pagination", {})
        total_pages = pagination.get("total_pages", 1)

        if page >= total_pages:
            break

        page += 1
        time.sleep(0.2)  # Rate limit 保護

    return all_items


def fetch_all_pages_by_date_segments(endpoint_key, start_date, end_date, params=None):
    """
    對於超過 10,000 筆的查詢，用日期分段拉取。
    start_date / end_date 格式: "YYYY-MM-DDTHH:MM:SSZ"
    """
    from datetime import datetime, timedelta

    params = dict(params or {})
    all_items = []

    start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
    end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
    segment_days = 30

    current = start
    while current < end:
        seg_end = min(current + timedelta(days=segment_days), end)
        params["created_after"] = current.strftime("%Y-%m-%dT%H:%M:%SZ")
        params["created_before"] = seg_end.strftime("%Y-%m-%dT%H:%M:%SZ")

        items = fetch_all_pages(endpoint_key, params=params)
        all_items.extend(items)

        current = seg_end

    return all_items


def money_to_float(money_obj):
    """將 Shopline 金額物件轉為 float，例如 {"cents": 2720, "dollars": 2720.0} → 2720.0"""
    if not money_obj:
        return 0.0
    return float(money_obj.get("dollars", 0) or 0)


def get_translation(obj, lang="zh-hant", fallback="en"):
    """取得翻譯文字"""
    if not obj:
        return ""
    if isinstance(obj, str):
        return obj
    return obj.get(lang, obj.get(fallback, ""))
