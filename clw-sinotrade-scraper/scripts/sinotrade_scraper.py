#!/usr/bin/env python3
"""
sinotrade_scraper.py - 永豐投顧台股報告自動抓取（含預覽摘要）
用法：
  python3 sinotrade_scraper.py           # 抓取並存檔
  python3 sinotrade_scraper.py --telegram # 抓取 + 發 Telegram 通知（有新報告才發）
"""

import asyncio
import json
import os
import re
import sys
import urllib.request
import urllib.parse
from datetime import datetime
from playwright.async_api import async_playwright

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
HISTORY_FILE = os.path.expanduser("~/.sinotrade_history.json")
BASE_URL = "https://scm.sinotrade.com.tw/"

# 個股報告識別 pattern（Company (Code TT)｜Title YYYYMMDD）
STOCK_REPORT_PATTERN = re.compile(r"^(.+?)\s*\((\d{4,5})\s*TT\)｜(.+?)\s*(\d{8})$")

# 噪音關鍵字（正文外的干擾文字）
NAV_NOISE = {
    "永豐投顧 SinoPac Inv.Service", "會員申請", "會員訂閱", "訂閱介紹",
    "研究報告", "永續ESG", "登入", "觀看收聽", "報告下載",
    "推薦更多", "關於永豐投顧", "最新公告", "羅素基金",
    "隱私權聲明", "客戶資料保密措施", "金融友善服務專區",
    "企業團網站", "永豐證券投資顧問股份有限公司",
    "SinoPac Securities Investment Service Corporation",
    "台北市忠孝西路一段80號14樓", "110年金管投顧新字第024號",
    "© 永豐投顧版權所有",
}
HEADER_NOISE = {
    "譜瑞-KY (4966 TT)｜毛利率承壓 20260423",
    "宏捷科 (8086 TT)｜2026 年獲利迎來歷史高峰 20260423",
    "聯亞 (3081 TT)｜訂單能見度已看到 2028 年 20260423",
}
# 正文截止關鍵字
CONTENT_END_MARKERS = ["登入會員，看更多", "登入會員", "看更多", "完整報告", "►"]


# ─── Telegram ────────────────────────────────────────────────────────────────

def send_telegram(message):
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        print("[Telegram] 請設定環境變數 TELEGRAM_BOT_TOKEN 和 TELEGRAM_CHAT_ID")
        return
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
    except Exception as e:
        print(f"[Telegram] 發送失敗: {e}")


# ─── 報告詳情頁預覽抓取 ──────────────────────────────────────────────────────

async def fetch_report_preview(page, guid: str) -> str:
    article_url = f"https://scm.sinotrade.com.tw/Article/Inner/{guid}"
    await page.goto(article_url, timeout=15000)
    await page.wait_for_load_state("domcontentloaded", timeout=12000)
    await page.wait_for_timeout(2000)

    body = await page.locator("body").inner_text()
    lines = body.splitlines()

    content_lines = []
    skip_tail = False
    for line in lines:
        stripped = line.strip()
        if any(m in stripped for m in CONTENT_END_MARKERS):
            skip_tail = True
        if skip_tail:
            continue
        if stripped in NAV_NOISE or stripped in HEADER_NOISE:
            continue
        if stripped and len(stripped) > 15:
            content_lines.append(stripped)

    raw = " ".join(content_lines)
    raw = re.sub(r"\s{2,}", " ", raw).strip()
    return raw if len(raw) > 50 else ""


# ─── 報告列表抓取 ──────────────────────────────────────────────────────────

async def fetch_reports_async():
    reports = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path=CHROME,
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
        )
        page = await browser.new_page()

        print(f"[抓取] 開啟 {BASE_URL}")
        await page.goto(BASE_URL, timeout=30000)
        await page.wait_for_load_state("networkidle", timeout=20000)
        await page.wait_for_timeout(2000)

        await page.locator("text=研究報告").first.hover()
        await page.wait_for_timeout(2000)

        links = await page.query_selector_all("a")
        print(f"[抓取] 找到 {len(links)} 個連結")

        for link in links:
            try:
                text = (await link.inner_text()).strip()
                href = await link.get_attribute("href") or ""
                m = STOCK_REPORT_PATTERN.match(text)
                if m:
                    guid = href.rstrip("/").split("/")[-1]
                    reports.append({
                        "name": m.group(1).strip(),
                        "code": m.group(2),
                        "title": m.group(3).strip(),
                        "date": m.group(4),
                        "url": href,
                        "guid": guid,
                        "raw": text,
                    })
            except Exception:
                continue

        await browser.close()

    print(f"[抓取] 共找到 {len(reports)} 篇個股報告")
    return reports


async def enrich_reports_with_preview(reports: list) -> list:
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path=CHROME,
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
        )
        page = await browser.new_page()

        for i, r in enumerate(reports):
            guid = r.get("guid") or r.get("url", "").split("/")[-1]
            if not guid:
                r["preview"] = ""
                continue
            try:
                print(f"[預覽] [{i+1}/{len(reports)}] 抓取 {r['code']} {r['name']} (guid={guid[:8]}...) ...")
                preview = await fetch_report_preview(page, guid)
                r["preview"] = preview
                if preview:
                    print(f"  → 預覽長度: {len(preview)} 字｜{preview[:80]}...")
                else:
                    print(f"  → 無公開正文（個股脈動等需會員登入）")
            except Exception as e:
                print(f"  → 預覽抓取失敗: {e}")
                r["preview"] = ""

        await browser.close()
    return reports


# ─── 歷史管理 ──────────────────────────────────────────────────────────────

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"reports": {}}


def save_history(history):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def find_new_reports(today_reports, history):
    today = datetime.now().strftime("%Y-%m-%d")
    prev_urls = set()
    for date_key, reps in history.get("reports", {}).items():
        if date_key != today:
            for rep in reps:
                prev_urls.add(rep.get("url", ""))
    return [r for r in today_reports if r.get("url") not in prev_urls]


# ─── 格式化 ─────────────────────────────────────────────────────────────────

def _truncate(preview: str, max_chars: int = 200) -> str:
    if len(preview) <= max_chars:
        return preview
    return preview[:max_chars].rstrip() + "..."


def format_telegram_message(new_reports, today_disp: str) -> str:
    lines = [f"📊 <b>永豐投顧台股報告</b>｜{today_disp}\n"]
    lines.append(f"共 {len(new_reports)} 篇新報告\n")

    for r in new_reports:
        code = r.get("code", "")
        name = r.get("name", "")
        title = r.get("title", "")
        date_raw = r.get("date", "")
        date_fmt = f"{date_raw[:4]}.{date_raw[4:6]}.{date_raw[6:8]}" if len(date_raw) == 8 else date_raw
        url = r.get("url", "")
        preview = r.get("preview", "")

        lines.append(f"📊 <b>{name} ({code} TT)</b>")
        lines.append(f"📅 {date_fmt}｜個股脈動")
        lines.append(f"📝 {title}")

        if preview:
            lines.append(f"🔍 預覽：{_truncate(preview, 200)}")
        else:
            lines.append("🔍 預覽：（無公開摘要，請登入會員閱讀完整內容）")

        if url:
            lines.append(f"🔗 <a href=\"{url}\">閱讀報告</a>")

        lines.append("─" * 20)
        lines.append("")

    return "\n".join(lines)


# ─── 主程式 ─────────────────────────────────────────────────────────────────

async def async_main():
    send_notify = "--telegram" in sys.argv
    today = datetime.now().strftime("%Y-%m-%d")
    today_disp = datetime.now().strftime("%Y.%m.%d")

    reports = await fetch_reports_async()

    if not reports:
        print("[結果] 今日無個股報告")
        if send_notify:
            send_telegram(f"📊 永豐投顧 {today_disp}：今日無個股報告")
        return

    print(f"\n=== {today} 個股報告 ===")
    for r in reports:
        print(f"  {r['code']} {r['name']} | {r['title']}")

    history = load_history()
    new_reports = find_new_reports(reports, history)
    print(f"\n[增量] 新增報告: {len(new_reports)} 篇（共 {len(reports)} 篇）")

    if new_reports and send_notify:
        print("\n[預覽] 開始抓取新報告預覽摘要...")
        new_reports = await enrich_reports_with_preview(new_reports)

    history["reports"][today] = [
        {k: v for k, v in r.items() if k not in ("preview", "guid")} for r in reports
    ]
    history["last_updated"] = datetime.now().isoformat()
    save_history(history)
    print(f"[存檔] 已寫入 {HISTORY_FILE}")

    if send_notify and new_reports:
        msg = format_telegram_message(new_reports, today_disp)
        print("\n=== Telegram 預覽 ===")
        print(msg[:500])
        print("...")
        send_telegram(msg)
    elif send_notify and not new_reports:
        print("[Telegram] 無新報告，跳過通知")


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
