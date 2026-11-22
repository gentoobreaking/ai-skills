# tasks-finish-notify

## 用途
任務完成後，透過 Telegram 傳送通知訊息給你，並在本機用 `say` 播報「任務已完成」。

## 觸發時機
當 AI agent 完成一項任務，且需要通知使用者時，可呼叫此 skill。

## 設定（首次使用前必須完成）

### 1. 建立 Telegram Bot 並取得 Token
在 Telegram 裡找 `@BotFather`，傳送 `/newbot` 建立機器人，它會回傳一個 **Bot Token**（例如 `123456:ABC-DEF1234...`）。

### 2. 取得你的 chat_id
先傳一個任何訊息給你剛建立的機器人，然後在終端執行：

```bash
curl -s "https://api.telegram.org/bot<BOT_TOKEN>/getUpdates"
```

從回傳的 JSON 裡找到 `"chat":{"id":123456789}`，該數字即為你的 `chat_id`。

### 3. 設定環境變數
將下列環境變數加入你的 shell 設定檔（例如 `~/.zshrc`、`~/.bash_profile` 或 OpenCode 的環境變數）：

```bash
export TELEGRAM_BOT_TOKEN="你的 Bot Token"
export TELEGRAM_CHAT_ID="你的 chat_id"
```

設定後記得 `source ~/.zshrc` 讓變數生效。

## 如何呼叫

這個 skill 可由 AI agent 在任務結束時自動呼叫，也可手動執行：

```bash
~/skills/tasks-finish-notify/notify.sh "任務已完成：cairn-research git push"
```

引數為選擇性，預設訊息為「任務已完成」。

## 檔案結構
- `SKILL.md`：本說明文件
- `notify.sh`：執行通知的腳本（curl 呼叫 Telegram API + `say` 播報）
