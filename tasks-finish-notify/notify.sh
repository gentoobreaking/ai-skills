#!/usr/bin/env bash
#
# tasks-finish-notify / notify.sh
#
# 任務完成通知：
#   1. 透過 Telegram Bot API 傳送訊息
#   2. 在本機用 `say` 播報「任務已完成」
#
# 使用方式：
#   ./notify.sh [可選的訊息內容]
#
# 需要先設定環境變數：
#   export TELEGRAM_BOT_TOKEN="你的 Bot Token"
#   export TELEGRAM_CHAT_ID="你的 chat_id"
#

set -euo pipefail

BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
CHAT_ID="${TELEGRAM_CHAT_ID:-}"
MESSAGE="${1:-任務已完成}"

# 若沒設定 Telegram 憑證，只執行本機 say，並提示使用者
if [[ -z "$BOT_TOKEN" || -z "$CHAT_ID" ]]; then
    echo "[tasks-finish-notify] TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID 未設定，跳過 Telegram 通知" >&2
else
    RESPONSE=$(curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
        -d "chat_id=${CHAT_ID}" \
        -d "text=${MESSAGE}" \
        -d "parse_mode=HTML" \
        --connect-timeout 10 \
        --max-time 20) || true

    if echo "$RESPONSE" | grep -q '"ok":true'; then
        echo "[tasks-finish-notify] Telegram 訊息已傳送：${MESSAGE}"
    else
        echo "[tasks-finish-notify] Telegram 發送失敗：${RESPONSE}" >&2
    fi
fi

# 本機語音播報（macOS say）
if command -v say >/dev/null 2>&1; then
    say "任務已完成"
else
    echo "[tasks-finish-notify] say 指令不可用，跳過語音播報" >&2
fi
