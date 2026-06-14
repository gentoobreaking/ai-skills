---
name: clw-twse-monitor
description: "台股即時監控與推播通知（v2）。當用戶提及台股監控、股價通知、漲停跌停、董監事持股、月營收、注意股票、處置股票、ESG、大盤指數、除權除息、殖利率、持股成本、未實現損益、四大買賣點、盤中即時報價、TWSE、證交所相關需求時使用此技能。覆蓋十二大場景：(1) 重大訊息——個股每日重大訊息掃描 (2) 除權除息——除權除息預告通知 (3) 評價追蹤——殖利率/本益比/淨值比變動 (4) 收盤行情——個股日成交價量 (5) 閾值警報——漲停/跌停/價格/百分比觸發 (6) 盤中即時——TWSE即時報價API+閾值監控 (7) 四大買賣點——BFP量價技術面訊號 (8) 警示掃描——注意/處置/變更交易/暫停交易 (9) 董監事——持股轉讓申報+持股餘額明細 (10) 月營收——營收公告/EPS/財測差異 (11) 公司治理——裁罰/違規/經營權異動/ESG (12) 大盤統計——加權指數+台灣50+歷史走勢。管理功能：--cost設定持有成本、--show-db查詢DB、--show-config查詢設定。"
---

# clw-twse-monitor — 台股即時監控與推播通知

> 透過臺灣證券交易所 OpenAPI 監控個股行情、董監事持股、月營收、公司治理等，主動推播至 Telegram（含 iPhone / Apple Watch）

## 前置依賴

無。純 Python 3 標準庫（`urllib.request` + `json` + `sqlite3`），免 API Key。

## 核心腳本

```
$SKILL_DIR/clw-twse-monitor/scripts/twse_monitor_v2.py
```

## 設定檔

```
~/.twse_monitor_config.json
```

含：watchlist（關注清單）、thresholds（各股閾值）、Telegram Bot 設定。

## 資料庫

```
~/.twse_monitor.db
```

SQLite，含 stocks（持有成本+行情）和 seen_items（去重快取）兩張表。

---

## 十大監控模組

### 監控模式（可任意組合，一次指定多個）

```bash
python3 $SKILL_DIR/clw-twse-monitor/scripts/twse_monitor_v2.py --check-messages
python3 $SKILL_DIR/clw-twse-monitor/scripts/twse_monitor_v2.py --check-messages --check-market
python3 $SKILL_DIR/clw-twse-monitor/scripts/twse_monitor_v2.py --daily
```

| 參數 | 說明 | 觸發條件 |
|------|------|----------|
| `--check-messages` | 個股重大訊息 | 有新訊息才推 |
| `--check-dividend` | 除權除息預告 | 有新預告才推 |
| `--check-valuation` | 殖利率/本益比/淨值比 | 有變動才推 |
| `--check-price` | 個股日成交行情 | 每日首次推 |
| `--check-threshold` | 股價閾值（漲跌停/價格/百分比） | 觸發才推 |
| `--check-realtime` | **盤中即時報價 + 閾值** | 每 10 分鐘（盤中） |
| `--check-bfp` | **四大買賣點（BFP）** | 有買/賣訊號 |
| `--check-alert` | 注意/處置/變更交易/暫停交易 | 關注股入列才推 |
| `--check-insider` | 董監事持股轉讓+持股明細 | 有新申報才推 |
| `--check-revenue` | 月營收+EPS+財測差異 | 有新資料才推 |
| `--check-governance` | 裁罰/違規/經營權異動/ESG | 有新事件才推 |
| `--check-market` | 大盤指數+台灣50+加權歷史 | **每次都推** |

`--daily`：一次跑以上全部（不含 realtime、price、threshold、bfp，另有獨立 cron）。

### 管理模式

```bash
# 設定持有成本
python3 $SKILL_DIR/clw-twse-monitor/scripts/twse_monitor_v2.py --cost 2330 2150

# 查詢 DB（格式化表格）
python3 $SKILL_DIR/clw-twse-monitor/scripts/twse_monitor_v2.py --show-db
python3 $SKILL_DIR/clw-twse-monitor/scripts/twse_monitor_v2.py --show-db --table stocks

# 查詢設定檔（美觀分段）
python3 $SKILL_DIR/clw-twse-monitor/scripts/twse_monitor_v2.py --show-config 
```

### Debug 模式

```bash
python3 $SKILL_DIR/clw-twse-monitor/scripts/twse_monitor_v2.py --debug --check-threshold
# Log 寫入 /tmp/twse_monitor.log，含所有判斷過程
```

---

## 閾值設定

以 2330 台積電為例，完整欄位：

| 欄位 | 預設值 | 說明 |
|------|--------|------|
| `max_price` | close + 10 | 漲破此價位 → 🟡 警告 |
| `min_price` | close - 10 | 跌破此價位 → 🟡 警告 |
| `max_pct_up` | 5 | 單日漲幅 > 5% → 🔵 參考 |
| `max_pct_down` | 5 | 單日跌幅 > 5% → 🔵 參考 |
| `circuit_up` | true | 漲停通知（±10%） |
| `circuit_down` | true | 跌停通知 |
| `circuit_pct` | 10 | 漲跌停幅度 |

支援三種格式：
- 絕對數值：`2400`
- 相對差額：`"+10"` / `"-10"`（close ± 10）
- 百分比：`"+5%"` / `"-5%"` / `"90%"`（close × 1.05 / 0.95 / 0.90）

---

## 通知分級

| 等級 | 觸發條件 | iPhone / Apple Watch |
|------|----------|----------------------|
| 🔴 緊急 | 漲停/跌停/裁罰/經營權+變更交易 | 響鈴 + 抬手 |
| 🟡 警告 | 價格閾值/違反申報/經營權異動 | 響鈴 |
| 🟠 警告 | 變更交易 | 響鈴 |
| 🔵 參考 | 百分比警告/ESG 揭露 | 一般推播 |
| ⚠️ | 注意股票 | 一般推播 |

---

## Cron Job 配置

7 個 Job 的完整配置（OpenClaw + crontab 雙格式）見 `references/twse-monitor-cron.md`。

---

## 參考文件

| 文件 | 說明 |
|------|------|
| `references/twse-monitor-usage.md` | 完整使用手冊（10 模組用法+範例） |
| `references/twse-monitor-cron.md` | Cron Job 配置指南（雙格式） |
| `references/twse-api-reference.md` | TWSE OpenAPI 143 endpoints 完整清單 |

---

## 常見操作速查

```bash
# 每日總檢查
python3 $SKILL_DIR/clw-twse-monitor/scripts/twse_monitor_v2.py --daily

# 盤中即時報價（每 10 分鐘）
python3 $SKILL_DIR/clw-twse-monitor/scripts/twse_monitor_v2.py --check-realtime

# 收盤行情 + 閾值 + BFP（14:00）
python3 $SKILL_DIR/clw-twse-monitor/scripts/twse_monitor_v2.py --check-price --check-threshold --check-bfp

# 設定持有成本
python3 $SKILL_DIR/clw-twse-monitor/scripts/twse_monitor_v2.py -cost 2330 2150

# 查看所有 DB 資料
python3 $SKILL_DIR/clw-twse-monitor/scripts/twse_monitor_v2.py --show-db

# 查看設定檔
python3 $SKILL_DIR/clw-twse-monitor/scripts/twse_monitor_v2.py --show-config

# Debug 模式
python3 $SKILL_DIR/clw-twse-monitor/scripts/twse_monitor_v2.py --debug --check-threshold
```
