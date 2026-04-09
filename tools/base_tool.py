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


def _api_request(method, endpoint_key, json_body=None, params=None,
                 path_params=None, retries=3, retry_on_client_error=True):
    """
    內部共用 HTTP 請求函數。不直接由 tool 呼叫。

    retry_on_client_error:
      - True (GET): 任何非 200 都重試（保持既有行為）
      - False (POST/PUT/PATCH/DELETE): 4xx 直接拋錯不重試，僅 5xx/網路層重試
    """
    path_params = path_params or {}
    url = get_url(endpoint_key, **path_params)
    headers = get_headers()

    for attempt in range(retries):
        try:
            resp = requests.request(
                method, url, headers=headers, params=params,
                json=json_body, timeout=60
            )
            if resp.status_code in (200, 201):
                return resp.json()
            if resp.status_code == 204:
                return {}  # No Content（常見於 DELETE 回應）

            is_client_error = 400 <= resp.status_code < 500
            is_server_error = resp.status_code >= 500

            if is_client_error and not retry_on_client_error:
                raise ShoplineAPIError(resp.status_code, resp.text[:500], url)

            if is_server_error or (is_client_error and retry_on_client_error):
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise ShoplineAPIError(resp.status_code, resp.text[:500], url)

            # 其他非預期狀態碼
            raise ShoplineAPIError(resp.status_code, resp.text[:500], url)

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise


def api_get(endpoint_key, params=None, path_params=None, retries=3):
    """發送 GET 請求到 Shopline API，回傳 JSON。含自動重試。"""
    return _api_request("GET", endpoint_key, params=params,
                        path_params=path_params, retries=retries,
                        retry_on_client_error=True)


def api_post(endpoint_key, json_body=None, params=None, path_params=None, retries=3):
    """發送 POST 請求到 Shopline API。4xx 不重試。"""
    return _api_request("POST", endpoint_key, json_body=json_body,
                        params=params, path_params=path_params, retries=retries,
                        retry_on_client_error=False)


def api_put(endpoint_key, json_body=None, params=None, path_params=None, retries=3):
    """發送 PUT 請求到 Shopline API。4xx 不重試。"""
    return _api_request("PUT", endpoint_key, json_body=json_body,
                        params=params, path_params=path_params, retries=retries,
                        retry_on_client_error=False)


def api_patch(endpoint_key, json_body=None, params=None, path_params=None, retries=3):
    """發送 PATCH 請求到 Shopline API。4xx 不重試。"""
    return _api_request("PATCH", endpoint_key, json_body=json_body,
                        params=params, path_params=path_params, retries=retries,
                        retry_on_client_error=False)


def api_delete(endpoint_key, params=None, path_params=None, retries=3):
    """發送 DELETE 請求到 Shopline API。4xx 不重試。"""
    return _api_request("DELETE", endpoint_key, params=params,
                        path_params=path_params, retries=retries,
                        retry_on_client_error=False)


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
