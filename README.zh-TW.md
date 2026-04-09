# MCP Shopline

[![PyPI version](https://img.shields.io/pypi/v/mcp-shopline)](https://pypi.org/project/mcp-shopline/)
[![Python versions](https://img.shields.io/pypi/pyversions/mcp-shopline)](https://pypi.org/project/mcp-shopline/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub stars](https://img.shields.io/github/stars/asgard-ai-platform/mcp-shopline)](https://github.com/asgard-ai-platform/mcp-shopline/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/asgard-ai-platform/mcp-shopline)](https://github.com/asgard-ai-platform/mcp-shopline/issues)
[![GitHub last commit](https://img.shields.io/github/last-commit/asgard-ai-platform/mcp-shopline)](https://github.com/asgard-ai-platform/mcp-shopline/commits/main)
[![MCP](https://img.shields.io/badge/MCP-compatible-blue)](https://modelcontextprotocol.io/)

[English](README.md)

開源的 [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) 伺服器，將 [Shopline Open API](https://open-api.docs.shoplineapp.com/docs/getting-started) 封裝為 143 個 AI 可調用的工具（75 個讀取 + 68 個寫入），用於電商數據分析與操作。

專為 [Claude Code](https://claude.ai/code)、Claude Cowork 及任何支援 MCP 協定的 AI 客戶端打造。讓 AI Agent 能夠透過自然語言查詢與管理 Shopline 商店的訂單、商品、庫存、客戶行為、促銷活動等。

## 功能特色

- **143 個即用工具** — 涵蓋訂單、商品、庫存、客戶、促銷、分類、訂閱、客服對話、評價等
- **MCP 伺服器**（stdio JSON-RPC 2.0）— 接入 Claude Code 後即可用自然語言提問
- **無外部依賴** — 僅需 Python 3.9+ 與 `requests`
- **內建分頁、重試與限流** — 工具內部處理所有 API 複雜度
- **為 AI Agent 設計** — 結構化 JSON 輸出，參數友善（日期用 `YYYY-MM-DD`，非 timestamp）

## API 參考文件

本專案基於 [Shopline Open API v1](https://open-api.docs.shoplineapp.com/docs/getting-started) 建構。

- API 文件：https://open-api.docs.shoplineapp.com
- 認證方式：Bearer Token（從 Shopline 商家後台取得）
- Base URL：`https://open.shopline.io/v1/`

您需要有效的 Shopline API Access Token。請參考 [Shopline API 認證指南](https://open-api.docs.shoplineapp.com/docs/authentication) 了解取得方式。

---

## 快速開始

### 安裝

```bash
pip install mcp-shopline
```

或使用 uvx（免安裝）：

```bash
uvx --from mcp-shopline mcp-shopline
```

設定 API Token：

```bash
export SHOPLINE_API_TOKEN=your_token_here
```

### 搭配 Claude Code 使用

透過 Claude CLI 加入伺服器：

```bash
claude mcp add --transport stdio shopline -- mcp-shopline
```

或直接帶入環境變數：

```bash
claude mcp add --transport stdio shopline -e SHOPLINE_API_TOKEN=your_token_here -- mcp-shopline
```

若您將專案 clone 至本機，Claude Code 會自動偵測 `.mcp.json`，143 個工具立即可用。

### 搭配 Claude Desktop 使用

在 `claude_desktop_config.json` 中加入以下設定：

```json
{
  "mcpServers": {
    "shopline": {
      "command": "mcp-shopline",
      "env": {
        "SHOPLINE_API_TOKEN": "your_token_here"
      }
    }
  }
}
```

或使用 uvx：

```json
{
  "mcpServers": {
    "shopline": {
      "command": "uvx",
      "args": ["--from", "mcp-shopline", "mcp-shopline"],
      "env": {
        "SHOPLINE_API_TOKEN": "your_token_here"
      }
    }
  }
}
```

---

## 重要：寫入工具

本伺服器包含可**建立、更新與刪除** Shopline 商店資料的工具。
您的 API Token 權限範圍決定哪些操作可用。

- 請在 Shopline 商家後台確認您的 Token 權限設定
- 建議僅開放您實際需要的權限範圍
- 寫入工具的描述均以 `[WRITE]` 前綴標示
- 執行寫入工具的測試需設定 `SHOPLINE_TEST_WRITES=1`

---

## 工具清單（143 個）

### 讀取工具（75 個）

#### 訂單類（12 個）

| 工具 | 功能 |
|------|------|
| `query_orders` | 依時間、狀態、通路、門市查詢訂單 |
| `get_sales_summary` | 營業額、客單價、件單價、付款/物流方式分佈 |
| `get_top_products` | 商品銷售排行榜（依銷量或營業額） |
| `get_sales_trend` | 每日/每週/每月銷售趨勢數據 |
| `get_channel_comparison` | 各門市/通路業績比較 |
| `get_order_detail` | 單筆訂單完整明細（含商品、付款、物流） |
| `get_refund_summary` | 退貨退款統計與商品明細 |
| `get_archived_orders` | 查詢已封存/關閉的訂單 |
| `get_order_labels` | 取得訂單附加的標籤清單 |
| `get_order_tags` | 取得訂單附加的標記清單 |
| `get_order_action_logs` | 訂單操作/稽核日誌 |
| `get_order_transactions` | 訂單的付款交易紀錄 |

#### 商品/庫存類（9 個）

| 工具 | 功能 |
|------|------|
| `get_product_list` | 依關鍵字、品牌搜尋商品 |
| `get_product_variants` | SKU 變體明細（尺寸 x 顏色庫存矩陣） |
| `get_inventory_overview` | 全商品庫存總覽（依品牌彙總） |
| `get_low_stock_alerts` | 低庫存/缺貨 SKU 警示 |
| `get_warehouses` | 倉庫/門市據點列表 |
| `get_stock_by_warehouse` | 各倉庫 SKU 庫存分佈矩陣 |
| `get_locked_inventory` | 查看待出貨訂單鎖定的庫存 |
| `list_purchase_orders` | 列出採購/補貨單 |
| `get_purchase_order_detail` | 單筆採購單完整明細 |

#### 數據分析類（11 個）

| 工具 | 功能 |
|------|------|
| `get_rfm_analysis` | RFM 客戶分群分析 |
| `get_repurchase_analysis` | 回購率與回購週期分析 |
| `get_customer_geo_analysis` | 客戶地區分佈（縣市層級） |
| `get_inventory_turnover` | 庫存周轉天數與周轉率 |
| `get_category_sales` | 依商品分類彙總銷售數據 |
| `get_promotion_analysis` | 促銷活動效果分析 |
| `get_refund_by_store` | 依門市/通路拆分退貨統計 |
| `get_stock_transfer_suggestions` | 依銷售速度與庫存水位自動產生調撥建議 |
| `get_promotion_roi` | 交叉比對促銷期間與銷售趨勢，計算提升幅度與 ROI |
| `get_customer_lifecycle` | 比較兩期 RFM 分群變化，追蹤客戶升級/流失 |
| `get_slow_movers` | 識別高庫存低銷售商品，輔助清倉決策 |

#### 客戶類（9 個）

| 工具 | 功能 |
|------|------|
| `list_customers` | 搜尋與列出客戶資料 |
| `get_customer_profile` | 單一客戶完整資料 |
| `list_customer_groups` | 列出客戶分群組別 |
| `get_customer_group_members` | 某分群組別的成員清單 |
| `list_store_credits` | 購物金餘額與歷史紀錄 |
| `list_membership_tiers` | 會員等級定義 |
| `get_customer_tier_history` | 客戶等級升降歷史 |
| `list_member_point_rules` | 點數累積與兌換規則 |
| `list_custom_fields` | 客戶資料自訂欄位定義 |

#### 分類與促銷類（14 個）

| 工具 | 功能 |
|------|------|
| `get_category_tree` | 完整商品分類階層樹 |
| `get_category_detail` | 單一分類明細 |
| `list_promotions` | 列出所有促銷活動 |
| `get_promotion_detail` | 單一促銷活動完整明細 |
| `search_promotions` | 依關鍵字或狀態搜尋促銷活動 |
| `list_flash_price_campaigns` | 列出限時特賣活動 |
| `get_flash_price_campaign_detail` | 單一限時特賣活動明細 |
| `list_affiliate_campaigns` | 列出聯盟行銷活動 |
| `get_affiliate_campaign_detail` | 單一聯盟活動明細 |
| `get_affiliate_campaign_usage` | 聯盟活動使用量與成效統計 |
| `list_gifts` | 列出買贈促銷活動 |
| `list_addon_products` | 列出加購商品促銷 |
| `list_product_subscriptions` | 列出商品訂閱方案 |
| `get_product_subscription_detail` | 單一訂閱方案明細 |

#### 訂單延伸類（8 個）

| 工具 | 功能 |
|------|------|
| `list_return_orders` | 列出退貨/退款單 |
| `get_return_order_detail` | 單筆退貨單完整明細 |
| `get_order_delivery` | 訂單物流追蹤資訊 |
| `list_conversations` | 列出客服對話 |
| `get_conversation_messages` | 對話串中的訊息內容 |
| `list_product_reviews` | 列出商品評價 |
| `get_product_review_detail` | 單筆評價完整明細 |

#### 商店設定類（12 個）

| 工具 | 功能 |
|------|------|
| `list_merchants` | 列出商家帳號 |
| `get_merchant_detail` | 單一商家詳細資料 |
| `list_payments` | 列出已設定的付款方式 |
| `list_delivery_options` | 列出已設定的物流選項 |
| `get_delivery_option_detail` | 單一物流選項明細 |
| `get_delivery_time_slots` | 可用配送時段 |
| `list_channels` | 列出銷售通路（線上、POS 等） |
| `get_channel_detail` | 單一通路明細 |
| `get_app_settings` | 應用程式層級設定 |
| `list_taxes` | 列出稅務設定 |
| `get_staff_permissions` | 員工帳號權限設定 |
| `get_token_info` | 目前 API Token 的資訊與權限範圍 |
| `list_agents` | 列出客服人員帳號 |

---

### 寫入工具（68 個）

寫入工具在描述中以 `[WRITE]` 前綴標示，需要對應的 Token 權限，測試時須設定 `SHOPLINE_TEST_WRITES=1`。

| 領域 | 工具數量 |
|------|---------|
| 訂單操作 | 8 個 — 更新狀態、新增備註、指派標籤/標記、取消、出貨 |
| 客戶操作 | 6 個 — 建立/更新客戶、調整購物金、更新分群 |
| 商品操作 | 15 個 — 建立/更新/刪除商品、管理變體、更新庫存 |
| 促銷/優惠券/活動操作 | 12 個 — 建立/更新/刪除促銷、優惠券、限時特賣、聯盟活動 |
| 分類操作 | 3 個 — 建立、更新、刪除分類 |
| 退貨單操作 | 2 個 — 審核/拒絕退貨申請 |
| 客服對話操作 | 2 個 — 回覆對話、更新對話狀態 |
| 評價操作 | 6 個 — 回覆評價、審核/拒絕/隱藏評價 |
| 買贈/加購操作 | 7 個 — 建立/更新/刪除買贈與加購促銷 |
| 採購單操作 | 2 個 — 建立與入庫採購單 |
| 媒體/自訂欄位操作 | 2 個 — 上傳媒體檔案、設定自訂欄位 |
| 物流/商家操作 | 3 個 — 更新物流資訊、管理商家設定 |

---

## API 端點覆蓋範圍

基於 [Shopline Open API v1](https://open-api.docs.shoplineapp.com)：

| 端點 | 狀態 | 說明 |
|------|------|------|
| [Orders](https://open-api.docs.shoplineapp.com/docs/order) | 200 | 完整存取（讀取 + 寫入） |
| [Products](https://open-api.docs.shoplineapp.com/docs/product) | 200 | 完整存取（讀取 + 寫入） |
| [Warehouses](https://open-api.docs.shoplineapp.com/docs/warehouse) | 200 | 完整存取 |
| [Categories](https://open-api.docs.shoplineapp.com/docs/category) | 200 | 完整存取（讀取 + 寫入） |
| [Return Orders](https://open-api.docs.shoplineapp.com/docs/return-order) | 200 | 完整存取（讀取 + 寫入） |
| [Promotions](https://open-api.docs.shoplineapp.com/docs/promotion) | 200 | 完整存取（讀取 + 寫入） |
| [Product Stocks](https://open-api.docs.shoplineapp.com/docs/product-stock) | 200 | 含各倉庫明細 |
| [Customers](https://open-api.docs.shoplineapp.com/docs/customer) | 200 | 完整存取（讀取 + 寫入） |
| Channels | 200 | 完整存取 |
| Conversations | 200 | 客服對話（讀取 + 寫入） |
| Reviews | 200 | 商品評價（讀取 + 寫入） |
| Subscriptions | 200 | 商品訂閱方案 |
| Affiliate Campaigns | 200 | 聯盟行銷（讀取 + 寫入） |
| Flash Price Campaigns | 200 | 限時特賣（讀取 + 寫入） |
| Purchase Orders | 200 | 採購/補貨單（讀取 + 寫入） |
| Gifts & Add-ons | 200 | 買贈/加購促銷（讀取 + 寫入） |
| Store Settings | 200 | 付款方式、物流、稅務、員工權限 |

> **注意：** 端點可用性取決於您的 Shopline API Token 權限。上述狀態反映完整權限存取。建議將 Token 限縮至僅需的權限範圍。

---

## 專案結構

```
mcp-shopline/
├── mcp_server.py              # MCP 伺服器（stdio JSON-RPC 2.0）
├── .mcp.json                  # Claude Code MCP 自動偵測設定
├── .env.example               # 環境變數範本
├── config/
│   └── settings.py            # API 設定（Token 從環境變數讀取）
├── tools/
│   ├── base_tool.py           # 共用 HTTP client（重試、分頁、輔助函式）
│   ├── order_tools.py         # 訂單讀取工具（12 個）
│   ├── product_tools.py       # 商品/庫存讀取工具（9 個）
│   ├── analytics_tools.py     # 數據分析讀取工具（11 個）
│   ├── customer_tools.py      # 客戶讀取工具（9 個）
│   ├── category_tools.py      # 分類與促銷讀取工具（14 個）
│   ├── extended_tools.py      # 訂單延伸讀取工具（8 個）
│   ├── settings_tools.py      # 商店設定讀取工具（12 個）
│   ├── writes/
│   │   ├── order_writes.py    # 訂單寫入工具（8 個）
│   │   ├── customer_writes.py # 客戶寫入工具（6 個）
│   │   ├── product_writes.py  # 商品寫入工具（15 個）
│   │   ├── promotion_writes.py # 促銷/優惠券寫入工具（12 個）
│   │   ├── category_writes.py # 分類寫入工具（3 個）
│   │   ├── return_writes.py   # 退貨單寫入工具（2 個）
│   │   ├── conversation_writes.py # 客服對話寫入工具（2 個）
│   │   ├── review_writes.py   # 評價寫入工具（6 個）
│   │   ├── gift_writes.py     # 買贈/加購寫入工具（7 個）
│   │   ├── purchase_writes.py # 採購單寫入工具（2 個）
│   │   ├── media_writes.py    # 媒體/自訂欄位寫入工具（2 個）
│   │   └── delivery_writes.py # 物流/商家寫入工具（3 個）
│   └── tool_registry.py       # 工具統一註冊
├── tests/
│   └── test_all_tools.py      # 端對端測試（143 個工具）
└── scripts/
    ├── auth/
    │   ├── test_connection.py     # API 連線驗證
    │   └── inspect_data_structure.py  # API 回應結構探查
    └── audit/
        └── scope_check.py     # Token 權限範圍稽核
```

## API 限制

以下為 Shopline Open API 的限制，已由工具內部自動處理：

- **分頁**：`page` + `per_page`（上限 50），每次呼叫間隔 0.2 秒以遵守限流
- **搜尋上限**：最多 10,000 筆；`fetch_all_pages_by_date_segments()` 自動依日期分段拉取
- **訂單狀態**：線上訂單用 `confirmed`、POS 用 `completed`，工具預設兩者皆包含
- **通路識別**：`created_from` = `"shop"`（線上）/ `"pos"`（門市）；門市名稱從 `order.channel.created_by_channel_name` 取得
- **幣別**：所有金額以 TWD（新台幣）表示，透過 `money_to_float()` 轉為 float

---

## 開發

### 從原始碼安裝

```bash
git clone https://github.com/asgard-ai-platform/mcp-shopline.git
cd mcp-shopline
pip install -e .
```

### 執行測試

```bash
# 讀取工具（無副作用）
python tests/test_all_tools.py

# 包含寫入工具（會建立/更新/刪除資料）
SHOPLINE_TEST_WRITES=1 python tests/test_all_tools.py

python scripts/auth/test_connection.py
```

### 新增工具

1. 定義 schema dict（Claude API `tool_use` 格式，含 `name`、`description`、`input_schema`）
2. 使用 `base_tool.py` 的 `api_get` / `fetch_all_pages` 實作函數
3. 加入對應模組的工具列表（如 `ORDER_TOOLS`）
4. 自動透過 `tool_registry.py` 和 `mcp_server.py` 註冊，無需額外設定

---

## 已知測試缺口

以下工具已實作並註冊，但因測試商店資料或 Token 權限限制，**尚未完成完整 E2E 測試**。程式碼可正常編譯、匯入、註冊，只需要實際資料或更廣的 Token 權限才能驗證端對端流程。

### 需要商店資料（透過 Shopline 後台建立）

| 工具 | 需要的資料 |
|------|-----------|
| `get_flash_price_campaign_detail` | 快閃價格活動（後台 > 行銷 > 限時特賣） |
| `get_affiliate_campaign_usage` | 至少一筆使用聯盟行銷碼的訂單 |
| `get_product_subscription_detail` | 啟用訂閱制的商品（後台 > 商品設定） |
| `get_return_order_detail` | 已完成的退貨單（後台 > 訂單 > 退貨） |
| `get_order_delivery` | 已執行出貨的訂單（出貨後物流才有獨立 ID） |
| `get_customer_group_members` | 至少一個客戶群組（後台 > 客戶 > 群組） |
| `get_customer_tier_history` | 有會員等級變動紀錄的客戶（需設定等級規則） |
| `get_delivery_time_slots` | 有設定取貨時段的物流選項 |

### 需要 Token 權限

| 工具 | 需要的權限 |
|------|-----------|
| `list_conversations` / `get_conversation_messages` | 對話 (Conversations) 讀取權限 |
| `list_channels` / `get_channel_detail` | 渠道 (Channels) 讀取權限（常見回傳 403/422；渠道資訊也可從 `order.channel.created_by_channel_name` 取得） |

### 寫入工具

全部 68 個寫入工具已通過匯入/註冊驗證。完整 E2E 寫入測試需設定 `SHOPLINE_TEST_WRITES=1` 並使用專用測試商店，以避免修改正式資料。測試腳本位於 `tests/test_writes/`。

## 開發計畫

- [x] `get_refund_by_store` — 依門市/通路拆分退貨統計
- [x] `get_stock_transfer_suggestions` — 依銷售速度與庫存水位自動產生調撥建議
- [x] `get_category_tree` — 商品分類結構檢視
- [x] `get_promotion_roi` — 交叉比對促銷期間與銷售趨勢，計算提升幅度與 ROI
- [x] `get_customer_lifecycle` — 比較兩期 RFM 分群變化，追蹤客戶升級/流失
- [x] `get_slow_movers` — 識別高庫存低銷售商品，輔助清倉決策
- [x] 新增 Customers API 工具（會員輪廓、人口統計、會員等級）
- [ ] 支援多商店（多 Token）
- [ ] 新增 Webhook 即時訂單通知

---

## 使用範例

### 「這個月的銷售狀況如何？」

> **你：** 這個月的銷售摘要是什麼？

**AI 呼叫：**
```
get_sales_summary(
  start_date = "2026-04-01",
  end_date = "2026-04-09",
  channel = "all"
)
```

**結果：** 本月營業額 NT$1,234,567，共 456 筆訂單，客單價 NT$2,707，線上佔 62%、門市佔 38%。

---

### 「哪些商品賣最好？」

> **你：** 上個月最暢銷的前 5 名商品是什麼？

**AI 呼叫：**
```
get_top_products(
  start_date = "2026-03-01",
  end_date = "2026-03-31",
  top_n = 5,
  sort_by = "revenue"
)
```

**結果：** 第一名「經典帆布休閒鞋 Classic Canvas」營收 NT$892,000（268 雙），第二名「輕量機能防風外套」營收 NT$654,000...

---

### 「查詢客戶資訊」

> **你：** 幫我查一下客戶「陳大明」的完整資訊

**AI 呼叫：**
```
list_customers(search_keyword = "陳大明")
→ get_customer_profile(customer_id = "5f3a8b2c...")
```

**結果：** 陳大明，VIP 會員，累計消費 NT$56,330，近 30 天消費 5 次，會員點數餘額 2,800 點，儲值金餘額 NT$500。

---

### 「哪些商品快缺貨了？」

> **你：** 哪些商品快缺貨了？

**AI 呼叫：**
```
get_low_stock_alerts(threshold = 5)
```

**結果：** 共 3,098 個 SKU 低於門檻，其中 2,847 個已完全缺貨。最嚴重的是「經典帆布休閒鞋 Classic Canvas」深藍色 M 號（庫存 0）。

---

### 「比較線上和門市業績」

> **你：** 比較一下線上和門市這個月的業績

**AI 呼叫：**
```
get_channel_comparison(
  start_date = "2026-04-01",
  end_date = "2026-04-09"
)
```

**結果：** 線上官網營收 NT$780,000（佔 63%），信義旗艦店 NT$220,000（佔 18%），中山概念店 NT$120,000（佔 10%）...

---

### 「客戶分群分析」

> **你：** 分析一下客戶 RFM 分群

**AI 呼叫：**
```
get_rfm_analysis(
  start_date = "2026-01-01",
  end_date = "2026-04-09"
)
```

**結果：** 共 1,618 位客戶。最佳客戶 70 人（HHH），近期新客 433 人（HLL），流失高消費客戶 188 人（LLH）需要挽回。

---

### 「建立新客戶」（寫入工具）

> **你：** 幫我建立一個新客戶，姓名王小明，email wang@test.com

**AI 呼叫：**
```
create_customer(
  name = "王小明",
  email = "wang@test.com"
)
```

**結果：** `[WRITE]` 客戶王小明建立成功，ID: 69d77d57...

---

## 貢獻

歡迎提交 Issue 或 Pull Request！

新增工具時，請遵循 `tools/` 目錄下的既有模式，並確保通過端對端測試。

## 授權

MIT
