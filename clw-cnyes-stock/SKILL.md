---
name: cnyes-stock-scraper
description: "鉅亨網台股新聞自動抓取，支援增量比對與 Telegram 通知。"
metadata:
  emoji: "📰"
  version: "1.0.0"
  last_update: "2026-05-12"
---

# cnyes-stock-scraper — 鉅亨網台股新聞抓取

## 核心功能

- 自動抓取鉅亨網台股新聞（分類頁面 + Trending 頭條）
- 增量比對，僅推送新增新聞
- Telegram 通知（自動分段，避免超過 4096 字元）
- Trending 台股區塊智能識別（關鍵字密度評分）
- 歷史檔併發保護（`fcntl.flock` + atomic write）

## 使用方式

```bash
# 抓取今日新聞並存檔
python3 -m cnyes_stock_scraper

# 抓取 + 發 Telegram 通知
TELEGRAM_BOT_TOKEN=xxx TELEGRAM_CHAT_ID=xxx python3 -m cnyes_stock_scraper --telegram

# 指定日期
python3 -m cnyes_stock_scraper --date 2026-05-12

# 抓取 Trending 台股頭條
python3 -m cnyes_stock_scraper --trending

# 使用系統 Chrome
python3 -m cnyes_stock_scraper --system-chrome
```

## 環境變數

| 變數 | 用途 | 預設值 |
|------|------|--------|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token（`--telegram` 時需要） | 無 |
| `TELEGRAM_CHAT_ID` | Telegram Chat ID（`--telegram` 時需要） | 無 |
| `IDEAS2TASKS_TASKS_DIR` | 覆蓋預設的 tasks 目錄路徑 | 無 |

## 排程

```cron
# 每日 08:30 抓取台股新聞並發送 Telegram
30 8 * * 1-5 PYTHONPATH=$SKILL_DIR TELEGRAM_BOT_TOKEN=xxx TELEGRAM_CHAT_ID=xxx python3 -m cnyes_stock_scraper --telegram
```

## 技術細節

- **抓取引擎**: Playwright + Chromium（支援 --system-chrome 使用系統 Chrome）
- **通知通道**: Telegram Bot API（環境變數）
- **歷史檔**: `~/.qclaw/cnyes_stock_history.json`
- **增量比對**: 以 URL 去重，避免重複通知
