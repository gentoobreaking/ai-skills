# TWSE Monitor 使用說明（v2）

## 概覽

TWSE Monitor v2 透過兩種資料來源監控豪關注的個股與市場動態，主動推播至 Telegram（含 iPhone / Apple Watch）：

| 資料來源 | 用途 | 即時性 |
|----------|------|--------|
| [TWSE OpenAPI](https://openapi.twse.com.tw/v1) | 收盤後完整資料 | ❌ 收盤後更新 |
| TWSE 即時報價 API（`mis.twse.com.tw`） | 盤中即時價格 | ✅ 盤中即時 |

**無需 API Key，完全免費。零外部依賴（純 Python 標準庫）。**

---

## 基本用法

### 單一模組執行
```bash
python3 /Users/claw/scripts/twse_monitor_v2.py --check-messages
```

### 多模組同時執行
```bash
# 盤後：重大訊息 + 大盤統計
python3 /Users/claw/scripts/twse_monitor_v2.py --check-messages --check-market

# 盤中：即時報價 + 即時閾值監控
python3 /Users/claw/scripts/twse_monitor_v2.py --check-realtime --check-threshold

# 收盤後：BFP 四大買賣點
python3 /Users/claw/scripts/twse_monitor_v2.py --check-bfp
```

### 每日完整總檢查（收盤後）
```bash
python3 /Users/claw/scripts/twse_monitor_v2.py --daily
```
> 一次跑：重大訊息 + 除權除息 + 殖利率 + 注意/處置股票 + 董監事 + 月營收/EPS + 公司治理 + 大盤統計
> （`--check-price`、`--check-threshold`、`--check-realtime`、`--check-bfp` 不含在 `--daily` 中，需單獨掛 cron）

### Debug 模式
```bash
python3 /Users/claw/scripts/twse_monitor_v2.py --debug --check-realtime
```
開啟後所有 API 請求、判斷過程、計算結果寫入 `/tmp/twse_monitor.log`。

### 查閱完整說明
```bash
python3 /Users/claw/scripts/twse_monitor_v2.py --help
```

---

## 可用模組

| 參數 | 說明 | 頻率建議 | 觸發條件 | 資料來源 |
|------|------|----------|----------|----------|
| `--check-messages` | 個股重大訊息 | 每日 1-2 次 | 有新訊息才推 | TWSE OpenAPI |
| `--check-dividend` | 除權除息預告 | 每日 | 有新預告才推 | TWSE OpenAPI |
| `--check-valuation` | 殖利率 / 本益比 / 股價淨值比 | 每日 | 有變動才推 | TWSE OpenAPI |
| `--check-price` | 個股日成交行情 | 每日收盤後 | 每日首次推，之後跳過 | TWSE OpenAPI |
| `--check-threshold` | 股價閾值監控（收盤） | 每日收盤後 | 漲跌停/價格/百分比觸發 | TWSE OpenAPI |
| `--check-realtime` | **盤中即時報價 + 閾值** | 每 10-15 分鐘（盤中） | 同 threshold | TWSE 即時 API |
| `--check-bfp` | **四大買賣點（BFP）** | 每日收盤後 | 有買/賣訊號 | TWSE OpenAPI |
| `--check-alert` | 注意/處置/變更交易/暫停交易 | 每小時 | 關注股入列才推 | TWSE OpenAPI |
| `--check-insider` | 董監事持股轉讓 + 持股明細 | 每日 | 有新申報/變動才推 | TWSE OpenAPI |
| `--check-revenue` | 月營收 + EPS + 財測差異 | 每週/月營收高峰期 | 有新資料才推 | TWSE OpenAPI |
| `--check-governance` | 裁罰/違規/經營權異動/ESG | 每日 | 有新事件才推 | TWSE OpenAPI |
| `--check-market` | 大盤指數 + 台灣50 + 加權走勢 | 每日收盤後 | **每次都推** | TWSE OpenAPI |

> `--check-market` 是唯一每次執行都推播的模組，其餘皆「有料才推」。

---

## 各模組使用範例

### `--check-realtime` 盤中即時報價（v2 新增）
```bash
python3 /Users/claw/scripts/twse_monitor_v2.py --check-realtime
```
輸出範例：
```
📡 台積電(2330) 盤中即時
   開: 2250.00  高: 2285.00  低: 2240.00  現: 2250.00
   成交量: 31,813  昨收: 2250.00
```
> 盤中每 10-15 分鐘跑一次，即時 OHLCV 資料（開/高/低/即時價/量）。
> 即時閾值與 `--check-threshold` 共用 `~/.twse_monitor_config.json` 的閾值設定。

### `--check-bfp` 四大買賣點（v2 新增）
```bash
python3 /Users/claw/scripts/twse_monitor_v2.py --check-bfp
```
輸出範例（觸發時）：
```
📊 四大買賣點 — 台積電(2330)

🟢 買點訊號
   量大收紅、三日均價大於六日均價

   MA3: 2245.00  MA6: 2238.50  乖離: +6.50
   極轉點條件: ✅ 前期正乖離 → 乖離率已回落，區域性買點
```

**訊號解讀：**
| 訊號 | 意義 |
|------|------|
| 🟢 買點 | 四項滿足越多，多頭訊號越強 |
| 🔴 賣點 | 四項滿足越多，空頭訊號越強 |
| 極轉點閘門 | 需 3/6 乖離率極值出現在近 3 天內才會輸出訊號 |

**觸發門檻（極轉點）**：
- **買點**：3日均線在6日均線之上（正乖離）→ 正乖離擴張後開始收斂 → 才輸出買點
- **賣點**：3日均線在6日均線之下（負乖離）→ 負乖離擴張後開始收斂 → 才輸出賣點

**注意**：需累積至少 6 天歷史行情（`--check-price` 每日執行）後，BFP 才會正常運作。

### `--check-messages` 重大訊息
```bash
python3 /Users/claw/scripts/twse_monitor_v2.py --check-messages
```
輸出範例：
```
📢 台積電(2330)
   2026/05/05 · 本公司代子公司 TSMC Global Ltd. 公告取得固定收益證券
```

### `--check-dividend` 除權除息預告
```bash
python3 /Users/claw/scripts/twse_monitor_v2.py --check-dividend
```
輸出範例：
```
💰 台積電(2330)
   除權息日: 115/06/15 · 現金股利: 5.0 · 股票股利: -
```

### `--check-valuation` 殖利率/本益比
```bash
python3 /Users/claw/scripts/twse_monitor_v2.py --check-valuation
```
輸出範例：
```
📊 台積電(2330)
   本益比: 33.97 · 殖利率: 0.98% · 淨值比: 10.77
   (已變動)
```

### `--check-price` 個股日成交
```bash
python3 /Users/claw/scripts/twse_monitor_v2.py --check-price
```
輸出範例：
```
📈 台積電(2330)
   收盤: 2250.00 (-25.00) · 成交量: 41,519,169
```

### `--check-threshold` 股價閾值監控
```bash
python3 /Users/claw/scripts/twse_monitor_v2.py --check-threshold
```
輸出範例（觸發時）：
```
🚨 【股價警報】
🔴 跌停！台積電(2330)
   收盤: 2047.50  (-10.0%)
🟡 台積電(2330) 跌破相對低點
   收盤: 2047.50 ≤ 閾值 2240.00
🔵 台積電(2330) 單日大跌
   -10.0%  閾值: ≥5%
```
> `--check-realtime` 與 `--check-threshold` 共用同一閾值邏輯，只是資料來源不同（即時 vs 收盤）。

### `--check-alert` 注意/處置/變更交易/暫停交易
```bash
python3 /Users/claw/scripts/twse_monitor_v2.py --check-alert
```
4 種警示分級：
| emoji | 類型 | 端點 |
|-------|------|------|
| ⚠️ | 注意股票 | `/announcement/notice` |
| 🔴 | 處置股票 | `/announcement/punish` |
| 🟠 | 變更交易 | `/exchangeReport/TWT85U` |
| ⛔ | 暫停交易 | `/exchangeReport/TWTAWU` |

### `--check-insider` 董監事持股
```bash
python3 /Users/claw/scripts/twse_monitor_v2.py --check-insider
```
輸出範例：
```
📋 台積電(2330) 董事長本人 魏哲家
   選任時: 6,392,834 → 目前: 7,452,349 · 設質: 1600000 (21.46%)
```
涵蓋兩個端點：
- 持股轉讓申報（`t187ap12_L`）：預定轉讓的董監事
- 董監事持股餘額（`t187ap11_L`）：全體董監事持股與設質

### `--check-revenue` 月營收/EPS
```bash
python3 /Users/claw/scripts/twse_monitor_v2.py --check-revenue
```
輸出範例：
```
📊 台積電(2330) 半導體業 · 2026/03
   當月營收: 415,191,699
   月增: 30.70%  年增: 45.19%
   累計: 1,134,103,440  年增: 35.13%
```

### `--check-governance` 公司治理/ESG
```bash
python3 /Users/claw/scripts/twse_monitor_v2.py --check-governance
```
6 個端點分三級：

| 等級 | 類型 | emoji | 端點 |
|------|------|-------|------|
| 🔴 緊急 | 裁罰案件 | 🔴 | `t187ap22_L` |
| 🔴 緊急 | 經營權異動+變更交易 | 🔴 | `t187ap27_L` |
| 🟡 警告 | 違反資訊申報 | 🟡 | `t187ap23_L` |
| 🟠 警告 | 經營權異動 | 🟠 | `t187ap24_L` |
| 🔵 參考 | ESG 資訊安全 | 🔵 | `t187ap46_L_16` |
| 🔵 參考 | ESG 職業安全衛生 | 🔵 | `t187ap46_L_21` |

### `--check-market` 大盤統計
```bash
python3 /Users/claw/scripts/twse_monitor_v2.py --check-market
```
輸出範例：
```
【大盤收盤】

🔺 寶島股價指數
   收盤: 45683.96 +145.84 (0.32%)

📊 臺灣50指數
   2026/05/05 · 價格: 37805.31 · 報酬: 86563.25

📈 加權指數走勢
   2026/05/05 · 開: 40708.40 · 高: ... · 低: ... · 收: 40769.29
```

---

## 管理指令

### 設定持有成本
```bash
python3 /Users/claw/scripts/twse_monitor_v2.py --cost 2330 2150
python3 /Users/claw/scripts/twse_monitor_v2.py --cost 0050 88.5
```
輸出範例：
```
✅ 持有成本已更新
   股票：2330 台積電
   成本：2,150.00
   現價：2,250.00（close_today）
   未實現損益：📈 +100.00（+4.65%）
```

### 查詢 DB
```bash
python3 /Users/claw/scripts/twse_monitor_v2.py --show-db                # 全部表
python3 /Users/claw/scripts/twse_monitor_v2.py --show-db --table stocks  # 只看 stocks
```

### 查詢設定檔
```bash
python3 /Users/claw/scripts/twse_monitor_v2.py --show-config
```

---

## 資料庫

**位置**：`~/.twse_monitor.db`（SQLite）

### 資料表：stocks

| 欄位 | 說明 | 範例 |
|------|------|------|
| `code` | 股票代碼（主鍵） | `2330` |
| `name` | 股票名稱 | `台積電` |
| `cost` | **持有成本**（豪自行填入） | `2150.0` |
| `close_today` | 今日收盤價（每日更新） | `2250.0` |
| `close_prev` | 昨日收盤價（每日更新） | `2275.0` |
| `updated_ts` | 最後更新時間 | `2026-05-06T14:16:56` |

> `cost` 欄位由豪自行維護，使用 `--cost CODE VALUE` 設定。

### 資料表：seen_items

記錄已通知過的項目，防止重複推播。

| 欄位 | 說明 | 範例 |
|------|------|------|
| `category` | 訊息類別 | `major_news`、`insider_holding`、`revenue`、`gov_penalty`、`realtime_threshold`、`bfp_buy`、`bfp_sell` 等 |
| `item_key` | 訊息唯一識別鍵 | `revenue_2330_11503`、`realtime_2330_20260506` |
| `message` | 訊息內容摘要 | `2250.00|+1.22%` |
| `ts` | 寫入時間 | `2026-05-06T14:16:40` |

### 手動查詢範例

```bash
sqlite3 ~/.twse_monitor.db "SELECT * FROM stocks;"
sqlite3 ~/.twse_monitor.db "SELECT category, item_key, ts FROM seen_items ORDER BY ts DESC LIMIT 10;"
```

---

## 設定檔

**位置**：`~/.twse_monitor_config.json`

```json
{
  "watchlist": ["0050", "2330", "00981A"],
  "realtime_enabled": true,
  "bfp_enabled": true,
  "realtime_interval": 600,
  "thresholds": {
    "0050": {
      "max_price":    "+10",
      "min_price":    "-10",
      "max_pct_up":    5,
      "max_pct_down":  5,
      "circuit_up":    true,
      "circuit_down":  true,
      "circuit_pct":   10
    },
    "2330": {
      "max_price":    "+10",
      "min_price":    "-10",
      "max_pct_up":    5,
      "max_pct_down":  5,
      "circuit_up":    true,
      "circuit_down":  true,
      "circuit_pct":   10
    },
    "00981A": {
      "max_price":    "+10",
      "min_price":    "-10",
      "max_pct_up":    5,
      "max_pct_down":  5,
      "circuit_up":    true,
      "circuit_down":  true,
      "circuit_pct":   10
    }
  },
  "telegram_bot_token": "...",
  "telegram_chat_id": "..."
}
```

### v2 新增欄位

| 欄位 | 說明 | 預設值 |
|------|------|--------|
| `realtime_enabled` | 啟用盤中即時監控 | `true` |
| `bfp_enabled` | 啟用四大買賣點 | `true` |
| `realtime_interval` | 即時輪詢間隔（秒），僅 `--check-realtime` 使用 | `600`（10 分鐘） |

---

## 閾值設定完整說明（以 2330 為例）

| 欄位 | 預設值 | 說明 |
|------|--------|------|
| `max_price` | `close + 10`（未填時） | 漲破此價位 → 🟡 警告 |
| `min_price` | `close - 10`（未填時） | 跌破此價位 → 🟡 警告 |
| `max_pct_up` | `5` | 單日漲幅 > 此值 → 🔵 參考 |
| `max_pct_down` | `5` | 單日跌幅 > 此值 → 🔵 參考 |
| `circuit_up` | `true` | 漲停通知（±10%）|
| `circuit_down` | `true` | 跌停通知 |
| `circuit_pct` | `10` | 漲跌停幅度（%）|

### 支援的閾值格式

| 設定值 | 意義 | 範例情境（2330 close=2250） |
|--------|------|------|
| `2400` | 絕對價格 | 漲破 2400 才通知 |
| `"+10"` | close + 10 | close ≥ 2260 通知 |
| `"-10"` | close - 10 | close ≤ 2240 通知 |
| `"+5%"` | close × 1.05 | close ≥ 2362.5 通知 |
| `"-5%"` | close × 0.95 | close ≤ 2137.5 通知 |
| `"90%"` | close × 0.90 | close ≤ 2025 通知 |

---

## 四大買賣點（Best Four Point）

本功能參考 [mlouielu/twstock](https://github.com/mlouielu/twstock)（MIT License）邏輯實作，去耦合、零外部依賴。

### 買點訊號（需同時滿足極轉點閘門）

| # | 名稱 | 觸發條件 | 意義 |
|---|------|----------|------|
| 1 | 量大收紅 | 成交量 > 昨日成交量 **且** 收盤 > 開盤 | 多頭力道強勁 |
| 2 | 量縮價不跌 | 成交量 < 昨日成交量 **且** 收盤 ≥ 昨收 | 拋壓不重，空方無力 |
| 3 | MA3 上揚 | 三日均線連續上漲 | 短期動能向上 |
| 4 | MA3 > MA6 | MA3[-1] > MA6[-1] | 均線多頭排列 |

### 賣點訊號（需同時滿足極轉點閘門）

| # | 名稱 | 觸發條件 | 意義 |
|---|------|----------|------|
| 1 | 量大收黑 | 成交量 > 昨日成交量 **且** 收盤 < 開盤 | 空頭力道強勁 |
| 2 | 量縮價跌 | 成交量 < 昨日成交量 **且** 收盤 < 昨收 | 承接薄弱，跌勢未止 |
| 3 | MA3 下滑 | 三日均線連續下跌 | 短期動能轉弱 |
| 4 | MA3 < MA6 | MA3[-1] < MA6[-1] | 均線空頭排列 |

### 極轉點閘門（必要前置條件）

```
【買點閘門】：前期正乖離（MA3 > MA6）→ 正乖離擴張後開始收斂 → 才輸出買點
【賣點閘門】：前期負乖離（MA3 < MA6）→ 負乖離擴張後開始收斂 → 才輸出賣點
```

> 若乖離率尚未形成明確極點，即使四個條件全滿也不輸出訊號。

### 實務注意事項

| 情境 | 建議 |
|------|------|
| 盤整/震盪市場 | 乖離率極轉點訊號可能來回觸發，請搭配其他分析 |
| 新追蹤的股票 | 需累積至少 6 天行情（`--check-price` 每日執行）後 BFP 才正常運作 |
| 純參考用途 | BFP 不含停損/停利機制，請勿作為唯一進場依據 |

---

## 通知分級

| 等級 | 觸發條件 | iPhone / Apple Watch |
|------|----------|----------------------|
| 🔴 緊急 | 漲停 / 跌停 / 裁罰 / 經營權+變更交易 | 響鈴 + 抬手 |
| 🟡 警告 | 突破價格閾值 / 違反申報 / 經營權異動 | 響鈴 |
| 🟠 警告 | 變更交易 | 響鈴 |
| 🔵 參考 | 百分比警告 / ESG 揭露 / BFP 訊號 | 一般推播 |
| ⚠️ | 注意股票 | 一般推播 |

---

## 快速參考

```bash
# ── 盤中即時（每 10-15 分鐘）─────────────────────────
python3 /Users/claw/scripts/twse_monitor_v2.py --check-realtime
python3 /Users/claw/scripts/twse_monitor_v2.py --check-realtime --debug

# ── 收盤後（每日 14:00）──────────────────────────────
python3 /Users/claw/scripts/twse_monitor_v2.py --check-price --check-threshold --check-bfp

# ── 盤後總檢查（每日 17:30）──────────────────────────
python3 /Users/claw/scripts/twse_monitor_v2.py --daily

# ── 每小時（盤中 9-16 點）───────────────────────────
python3 /Users/claw/scripts/twse_monitor_v2.py --check-alert                     # 注意/處置股票

# ── 每營業日 09:00 ──────────────────────────────────
python3 /Users/claw/scripts/twse_monitor_v2.py --check-insider                   # 董監事

# ── 每週一 09:00 ────────────────────────────────────
python3 /Users/claw/scripts/twse_monitor_v2.py --check-governance                # 公司治理

# ── 管理 ─────────────────────────────────────────────
python3 /Users/claw/scripts/twse_monitor_v2.py --cost 2330 2150                # 持有成本
python3 /Users/claw/scripts/twse_monitor_v2.py --show-db                         # 查 DB
python3 /Users/claw/scripts/twse_monitor_v2.py --show-config                     # 查設定

# ── 除錯 ─────────────────────────────────────────────
python3 /Users/claw/scripts/twse_monitor_v2.py --debug --check-realtime          # Debug
python3 /Users/claw/scripts/twse_monitor_v2.py --help                           # 說明
```

---

## 常見問題

**Q: `--check-price` 執行兩次會重複通知嗎？**
A: 不會。每日首次執行寫入 SQLite 後，之後執行會自動略過。

**Q: 哪些 API 可用於 ETF（如 0050）？**
A: `STOCK_DAY_ALL`、`BWIBBU_ALL`、`TWT48U_ALL` 均支援 ETF。即時 API 也支援。月營收（`t187ap05_L`）僅限上市公司。

**Q: `stocks.cost`（持有成本）怎麼填？**
A: `python3 twse_monitor_v2.py --cost 2330 2150`

**Q: Debug log 在哪裡？**
A: `/tmp/twse_monitor.log`，每次加 `--debug` 執行時覆蓋。

**Q: iPhone 收到但 Apple Watch 沒響？**
A: 檢查 Telegram App 設定 → 通知 → Apple Watch 同步是否開啟。

**Q: `--daily` 包含哪些模組？**
A: 重大訊息 + 除權除息 + 殖利率 + 注意股票 + 董監事 + 月營收 + 公司治理 + 大盤。不含 `--check-price`、`--check-threshold`、`--check-realtime`、`--check-bfp`（需單獨掛 cron）。

**Q: BFP 何時開始運作？**
A: 需累積至少 6 天歷史行情。每日執行 `--check-price`，6 天後 `--check-bfp` 會自動計算。

**Q: v1 與 v2 有何差異？**
A: v2 新增 `--check-realtime`（盤中即時）和 `--check-bfp`（四大買賣點），其餘模組相同。設定檔格式相容。
