"""
sinotrade_scraper/telegram.py - Telegram 通知模組
"""

import os
import urllib.parse
import urllib.request


def send_telegram(message):
    """發送 Telegram 通知（從環境變數讀取 token/chat_id）"""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        print("[Telegram] 請設定環境變數 TELEGRAM_BOT_TOKEN 和 TELEGRAM_CHAT_ID")
        return False

    try:
        data = urllib.parse.urlencode({
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=data
        )
        urllib.request.urlopen(req, timeout=10)
        print("[Telegram] 通知已發送")
        return True
    except Exception as e:
        print(f"[Telegram] 發送失敗: {e}")
        return False


if __name__ == "__main__":
    send_telegram("📊 測試通知：sinotrade_scraper Telegram 模組正常運作")
