---
name: telegram-reverse-notify
description: "從 Telegram 輪詢訊息並寫入本地 inbox，供 OpenCode Agent 讀取與處理，實現從 Telegram 反向通知 Agent，並透過 tasks-finish-notify 發送完成回饋。"
metadata:
  author: local
  version: "1.1.0"
---

# telegram-reverse-notify

## 用途
讓你能夠透過 Telegram 傳訊息給 OpenCode Agent，實現「反向通知」。

由於 OpenCode 本身沒有內建 Webhook 伺服器，此 skill 採用 **輪詢 (polling)** 方式，搭配 `tasks-finish-notify` 完成雙向通知循環。

## 雙向通知完整流程

```
Step 1. 你在 Telegram 傳訊息給 Bot
   ↓
Step 2. OpenCode Agent 執行 telegram_poll.sh check 抓取訊息並顯示
   ↓
Step 3. Agent 根據訊息內容執行任務（建立檔案、修改程式碼、git 操作等）
   ↓
Step 4. 任務完成後，Agent 呼叫 tasks-finish-notify 發送 Telegram 通知回給你，並 say 播報「任務已完成」
```

## 檔案結構

| 檔案 | 用途 |
|------|------|
| `SKILL.md` | 本說明文件 |
| `telegram_poll.py` | 主要輪詢腳本（Python） |
| `telegram_poll.sh` | Shell 執行包裝器 |
| `inbox.txt` | 訊息收件匣（Agent 讀取後會清空） |
| `.offset` | 記錄已處理的 Telegram update_id（自動產生） |

## 設定（首次使用前必須完成）

### 1. 環境變數

若需重新設定，請加入 shell 設定檔（`~/.zshrc` 等）：

```bash
export TELEGRAM_BOT_TOKEN="你的 Bot Token"
export TELEGRAM_CHAT_ID="你的 chat_id"
```

### 2. 取得 chat_id
先傳一個訊息給你的 Bot，然後執行：

```bash
curl -s "https://api.telegram.org/bot<BOT_TOKEN>/getUpdates"
```

從 JSON 找到 `"chat":{"id":123456789}` 即為你的 `chat_id`。

## 如何在 OpenCode 呼叫

在對話框對 Agent 說：

```
請檢查 telegram-reverse-notify 的 inbox，看看我從 Telegram 傳來什麼訊息，然後處理它。
```

或更完整的指令：

```
請執行 ~/skills/telegram-reverse-notify/telegram_poll.sh check，顯示接收到的 Telegram 訊息內容，並根據訊息內容執行對應任務（建立檔案、修改程式碼等），完成後呼叫 ~/skills/tasks-finish-notify/notify.sh 發 Telegram 通知回給我，並 say 播報「任務已完成」。
```

Agent 會依序：
1. 執行 `telegram_poll.sh check` → 抓到訊息並顯示給你看
2. 根據訊息內容採取行動（如建立 `hello.txt`、修改檔案等）
3. 呼叫 `tasks-finish-notify/notify.sh "任務已完成：..."` → 發 Telegram 通知 + say 播報

## 範例

你在 Telegram 傳：「請幫我建立一個 hello.txt，內容是 Hello World」

Agent 在 OpenCode 執行後會：

```
接收到 Telegram 訊息：{"text": "請幫我建立一個 hello.txt，內容是 Hello World", ...}

正在執行任務：建立 hello.txt...
(建立檔案 hello.txt，內容為 Hello World)

任務完成，發送 Telegram 通知...
(呼叫 tasks-finish-notify，手機收到通知並 say 播報「任務已完成」)
```

## 背景持續監聽（選用）

若要長期監聽 Telegram 訊息，可執行：

```bash
~/skills/telegram-reverse-notify/telegram_poll.sh poll
```

每 5 秒輪詢一次，有新訊息會印出並寫入 `inbox.txt`。按 `Ctrl+C` 停止。

## 安全提醒

- Bot Token 請勿外洩，不要 commit 到 GitHub
- 不要讓此腳本執行來自 Telegram 的任意 shell 指令（防止命令注入）
- `inbox.txt` 和 `.offset` 僅供本地使用，不建議 push 到 Git
