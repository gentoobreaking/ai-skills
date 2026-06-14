---
name: sinotrade-scraper
description: "永豐投顧台股報告自動抓取系統，每日 08:30 推送新增報告至 Telegram。"
metadata:
  emoji: "📊"
  version: "1.2.0"
  last_update: "2026-05-11"
---

# sinotrade-scraper — 永豐投顧台股報告抓取

## v1.2.0（2026-05-11）

- ✅ 移除配置檔依賴，改用環境變數（`TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`）
- ✅ 移除 `~/gold_monitor_config.json` 依賴
- ✅ 歷史檔移至 `~/.sinotrade_history.json`
- ✅ 移除舊版腳本相容段落

## 核心功能

- 自動抓取永豐投顧台股報告
- 增量比對，僅推送新增報告
- Telegram 通知（含預覽摘要）

## 使用方式

```bash
# 抓取並存檔
python3 -m sinotrade_scraper

# 抓取 + 發 Telegram 通知
python3 -m sinotrade_scraper --telegram
```

## 環境變數

| 變數 | 用途 | 預設值 |
|------|------|--------|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token（`--telegram` 時需要） | 無 |
| `TELEGRAM_CHAT_ID` | Telegram Chat ID（`--telegram` 時需要） | 無 |
| `SINOTRADE_CHROME_PATH` | Chrome 路徑 | 系統 Chrome |
| `SINOTRADE_HISTORY_FILE` | 歷史檔路徑 | `~/.sinotrade_history.json` |

## 排程

```cron
30 8 * * 1-5 PYTHONPATH=$SKILL_DIR python3 -m sinotrade_scraper --telegram
```

## 技術細節

- **抓取引擎**: Playwright + 系統 Chrome
- **通知通道**: Telegram Bot API（環境變數）
- **歷史檔**: `~/.sinotrade_history.json`
