---
name: clw-kgi-monitor
description: |
  凱基股股漲 YouTube 頻道 AI 供應鏈影片監控。
  抓取頻道影片，過濾 AI 供應鏈關鍵詞，符合條件即時推 Telegram。
  觸發條件：用戶提到「凱基」「kgi」「股股漲」「YouTube 監控」。
metadata:
  emoji: "🎬"
  version: "1.0.0"
  last_update: "2026-05-11"
---

# clw-kgi-monitor — 凱基股股漲 YouTube 監控

## 核心功能

- 自動抓取[凱基股股漲](https://www.youtube.com/@KGISIA.channel/videos)頻道影片
- AI 供應鏈關鍵詞過濾（台積、HBM、CoWoS、NVIDIA 等 25 個）
- 增量比對，只推新影片
- Telegram 通知（含影片標題、關鍵詞、時長、連結）

## 使用方式

```bash
# 抓取近 1 天
python3 scripts/kgi_monitor.py

# 抓取 + 發 Telegram 通知
python3 scripts/kgi_monitor.py --telegram

# 指定範圍
python3 scripts/kgi_monitor.py --range 3d --telegram

# 指定日期
python3 scripts/kgi_monitor.py --date 20260511 --telegram
```

## 環境變數

| 變數 | 用途 | 預設值 |
|------|------|--------|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token（`--telegram` 時需要） | 無 |
| `TELEGRAM_CHAT_ID` | Telegram Chat ID（`--telegram` 時需要） | 無 |
| `KGI_HISTORY_FILE` | 已處理影片歷史檔 | `~/.kgi_monitor_history.json` |
| `KGI_STATE_FILE` | 監控狀態檔 | `~/.kgi_monitor_state.json` |
| `YT_DLP_BIN` | yt-dlp 路徑 | `yt-dlp`（PATH） |

## 依賴

- `yt-dlp`（YouTube 抓取工具）
- 網路可存取 YouTube

## 排程

```cron
30 21 * * 1-5 python3 /path/to/kgi_monitor.py --range 1d --telegram
```

## AI 供應鏈關鍵詞

AI、半導體、封裝、台積、矽光子、三五族、記憶體、HBM、測試、光通訊、CPO、功率半導體、先進製程、伺服器、PCB、機器人、AI5、NVIDIA、輝達、聯發科、AMD、Intel、光電共封裝、CoWoS、先進封裝、轉單、GB200、H100、供應鏈、晶片
