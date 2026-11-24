#!/usr/bin/env python3
"""
telegram_poll.py - 從 Telegram 輪詢訊息，寫入 inbox 供 OpenCode Agent 讀取

用法:
    telegram_poll.py check    輪詢一次，輸出新訊息並清空 inbox
    telegram_poll.py poll     持續輪詢（背景監聽），Ctrl+C 停止

需要環境變數:
    TELEGRAM_BOT_TOKEN
"""

import os
import sys
import time
import json
from pathlib import Path

try:
    import requests
except ImportError:
    print("請先安裝 requests: pip3 install requests", file=sys.stderr)
    sys.exit(1)

BASE_DIR = Path(__file__).resolve().parent
INBOX = BASE_DIR / "inbox.txt"
OFFSET_FILE = BASE_DIR / ".offset"

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    print("錯誤: 請設定 TELEGRAM_BOT_TOKEN 環境變數", file=sys.stderr)
    sys.exit(1)


def load_offset() -> int:
    try:
        return int(OFFSET_FILE.read_text(encoding="utf-8").strip() or "0")
    except (FileNotFoundError, ValueError):
        return 0


def save_offset(offset: int) -> None:
    OFFSET_FILE.write_text(str(offset), encoding="utf-8")


def poll_once(offset: int):
    """呼叫 Telegram getUpdates，回傳 (new_offset, messages)"""
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    params = {"offset": offset, "timeout": 30, "limit": 100}
    try:
        r = requests.get(url, params=params, timeout=35)
        data = r.json()
        if not data.get("ok"):
            return offset, []
        results = data.get("result", [])
        new_offset = offset
        messages = []
        for update in results:
            new_offset = update["update_id"] + 1
            msg = update.get("message", {})
            text = msg.get("text", "")
            from_id = msg.get("from", {}).get("id")
            date = msg.get("date", "")
            if text and from_id:
                messages.append(
                    {
                        "text": text,
                        "from_id": from_id,
                        "date": date,
                    }
                )
        return new_offset, messages
    except Exception as e:
        print(f"[telegram_poll] 錯誤: {e}", file=sys.stderr)
        return offset, []


def append_messages(messages):
    with open(INBOX, "a", encoding="utf-8") as f:
        for msg in messages:
            f.write(json.dumps(msg, ensure_ascii=False) + "\n")


def read_and_clear_inbox() -> str:
    if not INBOX.exists():
        return ""
    content = INBOX.read_text(encoding="utf-8")
    INBOX.write_text("", encoding="utf-8")
    return content


def cmd_check() -> None:
    """單次輪詢，輸出新訊息並清空 inbox（供 Agent 讀取）"""
    offset = load_offset()
    new_offset, messages = poll_once(offset)
    if messages:
        append_messages(messages)
        save_offset(new_offset)
    content = read_and_clear_inbox()
    if content:
        print(content, end="")
    else:
        print("(無新訊息)")


def cmd_poll() -> None:
    """持續輪詢，每 5 秒檢查一次"""
    offset = load_offset()
    print("[telegram_poll] 開始輪詢 Telegram... (Ctrl+C 停止)")
    try:
        while True:
            offset, messages = poll_once(offset)
            if messages:
                append_messages(messages)
                save_offset(offset)
                for msg in messages:
                    print(f"[Telegram] {msg['text']}")
            time.sleep(5)
    except KeyboardInterrupt:
        save_offset(offset)
        print("\n[telegram_poll] 已停止")


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "check"
    if mode == "check":
        cmd_check()
    elif mode == "poll":
        cmd_poll()
    else:
        print("用法: telegram_poll.py [check|poll]", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
