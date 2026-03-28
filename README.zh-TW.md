# MCP Shopline

[![PyPI version](https://img.shields.io/pypi/v/mcp-shopline)](https://pypi.org/project/mcp-shopline/)
[![Python versions](https://img.shields.io/pypi/pyversions/mcp-shopline)](https://pypi.org/project/mcp-shopline/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[English](README.md)

開源的 [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) 伺服器，將 [Shopline Open API](https://open-api.docs.shoplineapp.com/docs/getting-started) 封裝為 19 個 AI 可調用的電商數據分析工具。

專為 [Claude Code](https://claude.ai/code)、Claude Cowork 及任何支援 MCP 協定的 AI 客戶端打造。讓 AI Agent 能夠透過自然語言查詢 Shopline 商店的訂單、商品、庫存、客戶行為與促銷活動。

## 功能特色

- **19 個即用工具** — 涵蓋訂單、商品、庫存、客戶分析、促銷活動
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
uvx --from mcp-shopline shopline-mcp
```

設定 API Token：

```bash
export SHOPLINE_API_TOKEN=your_token_here
```

### 搭配 Claude Code 使用

透過 Claude CLI 加入伺服器：

```bash
claude mcp add --transport stdio shopline -- shopline-mcp
```

或直接帶入環境變數：

```bash
claude mcp add --transport stdio shopline -e SHOPLINE_API_TOKEN=your_token_here -- shopline-mcp
```

若您將專案 clone 至本機，Claude Code 會自動偵測 `.mcp.json`，19 個工具立即可用。

### 搭配 Claude Desktop 使用

在 `claude_desktop_config.json` 中加入以下設定：

```json
{
  "mcpServers": {
    "shopline": {
      "command": "shopline-mcp",
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
      "args": ["--from", "mcp-shopline", "shopline-mcp"],
      "env": {
        "SHOPLINE_API_TOKEN": "your_token_here"
      }
    }
  }
}
```

---

## 工具清單（19 個）

### 訂單類（7 個）

| 工具 | 功能 |
|------|------|
| `query_orders` | 依時間、狀態、通路、門市查詢訂單 |
| `get_sales_summary` | 營業額、客單價、件單價、付款/物流方式分佈 |
| `get_top_products` | 商品銷售排行榜（依銷量或營業額） |
| `get_sales_trend` | 每日/每週/每月銷售趨勢數據 |
| `get_channel_comparison` | 各門市/通路業績比較 |
| `get_order_detail` | 單筆訂單完整明細（含商品、付款、物流） |
| `get_refund_summary` | 退貨退款統計與商品明細 |

### 商品/庫存類（6 個）

| 工具 | 功能 |
|------|------|
| `get_product_list` | 依關鍵字、品牌搜尋商品 |
| `get_product_variants` | SKU 變體明細（尺寸 x 顏色庫存矩陣） |
| `get_inventory_overview` | 全商品庫存總覽（依品牌彙總） |
| `get_low_stock_alerts` | 低庫存/缺貨 SKU 警示 |
| `get_warehouses` | 倉庫/門市據點列表 |
| `get_stock_by_warehouse` | 各倉庫 SKU 庫存分佈矩陣 |

### 數據分析類（6 個）

| 工具 | 功能 |
|------|------|
| `get_rfm_analysis` | RFM 客戶分群分析 |
| `get_repurchase_analysis` | 回購率與回購週期分析 |
| `get_customer_geo_analysis` | 客戶地區分佈（縣市層級） |
| `get_inventory_turnover` | 庫存周轉天數與周轉率 |
| `get_category_sales` | 依商品分類彙總銷售數據 |
| `get_promotion_analysis` | 促銷活動效果分析 |

---

## API 端點覆蓋範圍

基於 [Shopline Open API v1](https://open-api.docs.shoplineapp.com)：

| 端點 | 狀態 | 說明 |
|------|------|------|
| [Orders](https://open-api.docs.shoplineapp.com/docs/order) | 200 | 完整存取 |
| [Products](https://open-api.docs.shoplineapp.com/docs/product) | 200 | 完整存取 |
| [Warehouses](https://open-api.docs.shoplineapp.com/docs/warehouse) | 200 | 完整存取 |
| [Categories](https://open-api.docs.shoplineapp.com/docs/category) | 200 | 完整存取 |
| [Return Orders](https://open-api.docs.shoplineapp.com/docs/return-order) | 200 | 完整存取 |
| [Promotions](https://open-api.docs.shoplineapp.com/docs/promotion) | 200 | 完整存取 |
| [Product Stocks](https://open-api.docs.shoplineapp.com/docs/product-stock) | 200 | 含各倉庫明細 |
| [Customers](https://open-api.docs.shoplineapp.com/docs/customer) | 403 | 需額外權限申請 |
| Channels | 422/403 | 不需要（門市資訊已包含在訂單資料中） |

> **注意：** 端點可用性取決於您的 Shopline API Token 權限。上述狀態反映一般商家設定。若您有更廣泛的權限，可能有更多端點可使用。

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
│   ├── order_tools.py         # 訂單工具（7 個）
│   ├── product_tools.py       # 商品/庫存工具（6 個）
│   ├── analytics_tools.py     # 數據分析工具（6 個）
│   └── tool_registry.py       # 工具統一註冊
├── tests/
│   └── test_all_tools.py      # 端對端測試（19 個工具）
└── scripts/auth/
    ├── test_connection.py     # API 連線驗證
    └── inspect_data_structure.py  # API 回應結構探查
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
python tests/test_all_tools.py
python scripts/auth/test_connection.py
```

### 新增工具

1. 定義 schema dict（Claude API `tool_use` 格式，含 `name`、`description`、`input_schema`）
2. 使用 `base_tool.py` 的 `api_get` / `fetch_all_pages` 實作函數
3. 加入對應模組的工具列表（如 `ORDER_TOOLS`）
4. 自動透過 `tool_registry.py` 和 `mcp_server.py` 註冊，無需額外設定

---

## 開發計畫

- [ ] 新增 Customers API 工具（會員輪廓、人口統計、會員等級）
- [ ] `get_refund_by_store` — 依門市/通路拆分退貨統計
- [ ] `get_stock_transfer_suggestions` — 依銷售速度與庫存水位自動產生調撥建議
- [ ] `get_category_tree` — 商品分類結構檢視
- [ ] `get_promotion_roi` — 交叉比對促銷期間與銷售趨勢，計算提升幅度與 ROI
- [ ] `get_customer_lifecycle` — 比較兩期 RFM 分群變化，追蹤客戶升級/流失
- [ ] `get_slow_movers` — 識別高庫存低銷售商品，輔助清倉決策
- [ ] 支援多商店（多 Token）
- [ ] 新增 Webhook 即時訂單通知

## 貢獻

歡迎提交 Issue 或 Pull Request！

新增工具時，請遵循 `tools/` 目錄下的既有模式，並確保通過端對端測試。

## 授權

MIT
