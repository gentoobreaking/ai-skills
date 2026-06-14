#!/usr/bin/env python3
"""
kgi_monitor.py - 凱基股股漲 YouTube 頻道監控腳本
抓取頻道影片，過濾 AI 供應鏈關鍵詞，符合條件的即時推 Telegram

環境變數：
  TELEGRAM_BOT_TOKEN  — Telegram Bot Token（--telegram 時需要）
  TELEGRAM_CHAT_ID    — Telegram Chat ID（--telegram 時需要）
  KGI_HISTORY_FILE    — 歷史檔路徑（預設 ~/.kgi_monitor_history.json）
  KGI_STATE_FILE      — 狀態檔路徑（預設 ~/.kgi_monitor_state.json）

依賴：
  yt-dlp（需在 PATH 或指定 YT_DLP_BIN 環境變數）
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path

# ---- 路徑設定 ----
HISTORY_FILE = Path(os.environ.get("KGI_HISTORY_FILE", "~/.kgi_monitor_history.json")).expanduser()
STATE_FILE = Path(os.environ.get("KGI_STATE_FILE", "~/.kgi_monitor_state.json")).expanduser()

# yt-dlp：環境變數 > PATH
YT_DLP_BIN = os.environ.get("YT_DLP_BIN", "yt-dlp")

# ---- 關鍵詞庫 ----
AI_KEYWORDS = [
    "AI", "半導體", "封裝", "台積", "矽光子", "三五族",
    "記憶體", "HBM", "測試", "光通訊", "CPO", "功率半導體",
    "先進製程", "伺服器", "PCB", "機器人", "AI5",
    "NVIDIA", "輝達", "聯發科", "AMD", "Intel",
    "光電共封裝", "CoWoS", "先進封裝", "轉單",
    "GB200", "H100", "供應鏈", "晶片",
]

CHANNEL_URL = "https://www.youtube.com/@KGISIA.channel/videos"

# ============================================================
# 工具函式
# ============================================================

def send_telegram(message):
    """發送 Telegram 訊息"""
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
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            if result.get("ok"):
                print("✅ Telegram 訊息已發送")
                return True
            print(f"⚠️ Telegram 發送失敗: {result}")
            return False
    except Exception as e:
        print(f"⚠️ Telegram 發送異常: {e}")
        return False


def load_history():
    """讀取已處理影片 ID 清單"""
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data.get("processed_ids", []))
    except Exception:
        return set()


def save_history(processed_ids: set):
    """寫入已處理影片 ID"""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump({"processed_ids": list(processed_ids)}, f, ensure_ascii=False, indent=2)


def load_state():
    """讀取監控狀態"""
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state: dict):
    """寫入監控狀態"""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# ============================================================
# yt-dlp 整合
# ============================================================

def fetch_youtube_videos(days: int = 1, target_date: datetime = None) -> list:
    """
    用 yt-dlp 抓取頻道影片清單
    """
    import subprocess

    if target_date:
        start_date = target_date
    else:
        start_date = datetime.now() - timedelta(days=days)

    start_str = start_date.strftime("%Y%m%d")

    cmd = [
        YT_DLP_BIN,
        "--flat-playlist",
        "--print", "%(id)s|%(title)s|%(upload_date)s|%(duration)s",
        "--dateafter", start_str,
        "--playlist-end", "50",
        CHANNEL_URL
    ]

    print(f"🔍 抓取 YouTube 影片（近 {days} 天，起於 {start_str}）...")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"⚠️ yt-dlp 執行異常: {result.stderr}")
            return []

        lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
        videos = []
        for line in lines:
            parts = line.split("|")
            if len(parts) >= 3:
                vid = {
                    "id": parts[0],
                    "title": parts[1],
                    "upload_date": parts[2],
                    "duration": parts[3] if len(parts) > 3 else "NA"
                }
                if target_date:
                    d = datetime.strptime(vid["upload_date"], "%Y%m%d")
                    if d.date() != target_date.date():
                        continue
                videos.append(vid)

        print(f"📹 抓到 {len(videos)} 部影片")
        return videos

    except subprocess.TimeoutExpired:
        print("⚠️ yt-dlp 執行逾時")
        return []
    except Exception as e:
        print(f"⚠️ 抓取失敗: {e}")
        return []


def filter_by_keywords(videos: list) -> list:
    """關鍵詞過濾，大小寫不敏感"""
    matched = []
    for v in videos:
        title_lower = v["title"].lower()
        if v["title"].startswith("Episode "):
            continue
        for kw in AI_KEYWORDS:
            if kw.lower() in title_lower:
                v["matched_keyword"] = kw
                matched.append(v)
                break
    return matched


# ============================================================
# 訊息格式化
# ============================================================

def format_duration(seconds_str: str) -> str:
    """將秒數轉為「X 分鐘」"""
    try:
        sec = int(float(seconds_str))
        mins = sec // 60
        return f"{mins} 分鐘"
    except Exception:
        return "NA"


def format_telegram_message(videos: list, days: int = 1) -> str:
    """格式化 Telegram 通知訊息"""
    if not videos:
        return f"""🎬 <b>凱基股股漲 監控報告</b>
📅 {datetime.now().strftime('%Y-%m-%d')}（近 {days} 天）

✅ 近無符合 AI 供應鏈關鍵詞的新影片。

🔗 <a href="{CHANNEL_URL}">觀看頻道</a>"""

    lines = [f"🎬 <b>凱基股股漲 監控報告</b>",
             f"📅 {datetime.now().strftime('%Y-%m-%d')}（近 {days} 天）",
             "",
             f"🔍 符合 AI 供應鏈關鍵詞的影片（共 {len(videos)} 集）：",
             ""]

    for i, v in enumerate(videos, 1):
        title = v["title"].replace("《凱基股股漲》", "").strip()
        duration = format_duration(v["duration"])
        date_fmt = f"{v['upload_date'][:4]}/{v['upload_date'][4:6]}/{v['upload_date'][6:8]}"
        matched = v.get("matched_keyword", "")
        url = f"https://www.youtube.com/watch?v={v['id']}"

        lines.append(f"{i}️⃣ {title}")
        lines.append(f"   #{matched} | {date_fmt} | {duration}")
        lines.append(f"   🔗 {url}")
        lines.append("")

    lines.append(f"🔗 <a href=\"{CHANNEL_URL}\">觀看頻道</a>")

    return "\n".join(lines)


# ============================================================
# 主邏輯
# ============================================================

def run_monitor(days: int = 1, target_date: datetime = None, send_notify: bool = False):
    """執行監控流程"""
    print("=" * 50)
    print(f"🚀 kgi-monitor 啟動（{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}）")
    print(f"   範圍: 近 {days} 天 | Telegram: {'是' if send_notify else '否'}")
    print("=" * 50)

    # 1. 抓取影片
    videos = fetch_youtube_videos(days=days, target_date=target_date)
    if not videos:
        print("⚠️ 無法抓取任何影片，請確認網路或頻道狀態")
        return

    # 2. 關鍵詞過濾
    matched = filter_by_keywords(videos)
    print(f"✅ 符合關鍵詞: {len(matched)} 部")

    # 3. 讀取歷史，過濾已處理
    history = load_history()
    new_videos = [v for v in matched if v["id"] not in history]

    if new_videos:
        print(f"🆕 新影片（未通知過）: {len(new_videos)} 部")
    else:
        print("✅ 無新影片")

    # 4. 顯示結果
    if new_videos:
        print("\n📋 符合條件的新影片:")
        for v in new_videos:
            print(f"  - [{v['upload_date']}] {v['title'][:50]}... (#{v.get('matched_keyword', '')})")

    # 5. 發送 Telegram
    if send_notify and new_videos:
        msg = format_telegram_message(new_videos, days)
        send_telegram(msg)

    # 6. 更新歷史
    all_processed = history | {v["id"] for v in new_videos}
    save_history(all_processed)
    print(f"📝 已更新歷史記錄（共 {len(all_processed)} 部）")

    # 7. 更新 state
    state = load_state()
    state["last_run"] = datetime.now().isoformat()
    state["last_new_count"] = len(new_videos)
    state["last_range"] = f"{days}d"
    save_state(state)

    print("✅ 完成")


# ============================================================
# CLI 入口
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="凱基股股漲 YouTube 頻道 AI 供應鏈監控腳本"
    )
    parser.add_argument("--range", "-r", default="1d", choices=["1d", "3d", "7d"],
                        help="時間範圍: 1d（預設）、3d、7d")
    parser.add_argument("--date", "-d", default=None,
                        help="指定日期（YYYYMMDD），優先於 --range")
    parser.add_argument("--telegram", "-t", action="store_true",
                        help="啟用 Telegram 通知")
    args = parser.parse_args()

    target_date = datetime.strptime(args.date, "%Y%m%d") if args.date else None
    days = {"1d": 1, "3d": 3, "7d": 7}[args.range]
    run_monitor(days=days, target_date=target_date, send_notify=args.telegram)
