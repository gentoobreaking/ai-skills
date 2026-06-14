"""
cnyes_stock_scraper - 鉅亨網台股新聞自動抓取

環境變數：
  TELEGRAM_BOT_TOKEN          Telegram Bot Token
  TELEGRAM_CHAT_ID            Telegram Chat ID
  IDEAS2TASKS_TASKS_DIR       可覆蓋預設的 tasks 目錄路徑
"""

import fcntl
import json
import os
import re
import shutil
import tempfile
import urllib.request
import urllib.parse
from datetime import datetime
from playwright.sync_api import sync_playwright

CHROME_SYSTEM = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
HISTORY_FILE = os.path.expanduser("~/.qclaw/cnyes_stock_history.json")
BASE_URL = "https://news.cnyes.com/news/cat/tw_stock"
TRENDING_URL = "https://news.cnyes.com/trending?exp=a"

PAGE_LOAD_TIMEOUT = 30000
DOM_READY_TIMEOUT = 20000
INITIAL_WAIT_MS = 3000
MAX_SCROLLS = 12
SCROLL_WAIT_MS = 1500


def load_telegram_config():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    return token, chat_id


TELEGRAM_MAX_LENGTH = 4096


def send_telegram(messages):
    token, chat_id = load_telegram_config()
    if not token or not chat_id:
        print("[Telegram] 缺少 TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID，跳過通知")
        return

    if isinstance(messages, str):
        messages = [messages]

    for i, msg in enumerate(messages):
        try:
            data = urllib.parse.urlencode({
                "chat_id": chat_id,
                "text": msg,
                "parse_mode": "HTML"
            }).encode()
            req = urllib.request.Request(
                f"https://api.telegram.org/bot{token}/sendMessage",
                data=data
            )
            urllib.request.urlopen(req, timeout=10)
            tag = f" (第 {i+1}/{len(messages)} 則)" if len(messages) > 1 else ""
            print(f"[Telegram] 通知已發送{tag}")
        except Exception as e:
            print(f"[Telegram] 發送失敗: {e}")


def _item_lines(item):
    time_str = f"【{item['time']}】" if item.get("time") else ""
    return [f"🔹 {time_str}{item['title']}", f"   {item['url']}", ""]


def _trending_item_lines(item):
    rank = item.get("rank", 0)
    return [f"{rank}. {item['title']}", f"   {item['url']}", ""]


def _split_messages(header, item_blocks, max_len=TELEGRAM_MAX_LENGTH):
    messages = []
    lines = [header, ""]

    for block in item_blocks:
        block_text = "\n" + "\n".join(block)
        if len(block_text) > max_len:
            if lines != [header, ""]:
                messages.append("\n".join(lines).strip())
            messages.append((header + "\n\n" + "\n".join(block)).strip()[:max_len])
            lines = [header, ""]
            continue
        candidate = "\n".join(lines + block)
        if len(candidate) > max_len:
            messages.append("\n".join(lines).strip())
            lines = [header, ""]
        lines.extend(block)

    if lines != [header, ""]:
        messages.append("\n".join(lines).strip())

    if not messages:
        messages.append(header)

    total_items = len(item_blocks)
    sent_items = sum(1 for m in messages if m.count("\n") > 1)
    if sent_items < total_items:
        print(f"[Telegram] 因長度限制，僅發送 {sent_items}/{total_items} 筆新聞")

    return messages


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {}
    with open(HISTORY_FILE) as f:
        fcntl.flock(f, fcntl.LOCK_SH)
        return json.load(f)


def save_history(date, news_list):
    os.makedirs(os.path.dirname(HISTORY_FILE) or ".", exist_ok=True)

    with open(HISTORY_FILE, "a") as lock_f:
        fcntl.flock(lock_f, fcntl.LOCK_EX)

        try:
            lock_f.seek(0)
            hist = json.load(lock_f)
        except (json.JSONDecodeError, ValueError):
            hist = {}

        hist[date] = news_list

        tmp = tempfile.NamedTemporaryFile(
            mode="w", delete=False,
            dir=os.path.dirname(HISTORY_FILE) or ".",
            suffix=".tmp"
        )
        try:
            json.dump(hist, tmp, ensure_ascii=False, indent=2)
            tmp.close()
            shutil.move(tmp.name, HISTORY_FILE)
        except:
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)
            raise


def get_new_news(date, news_list):
    hist = load_history()
    existing = set(n["url"] for n in hist.get(date, []))
    return [n for n in news_list if n["url"] not in existing]


def fetch_news(date_str, use_system_chrome=False):
    url = f"{BASE_URL}?date={date_str}"
    news = []

    with sync_playwright() as p:
        browser_kwargs = {"headless": True, "args": ["--no-sandbox", "--disable-dev-shm-usage"]}
        if use_system_chrome:
            browser_kwargs["executable_path"] = CHROME_SYSTEM
        with p.chromium.launch(**browser_kwargs) as browser:
            with browser.new_page() as page:
                print(f"[抓取] 開啟 {url}")
                page.goto(url, timeout=PAGE_LOAD_TIMEOUT)
                page.wait_for_load_state("domcontentloaded", timeout=DOM_READY_TIMEOUT)
                page.wait_for_timeout(INITIAL_WAIT_MS)

                prev_count = 0
                for _ in range(MAX_SCROLLS):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(SCROLL_WAIT_MS)
                    curr_count = page.locator("a[href*='/news/id/']").count()
                    print(f"  滾動 {_+1}: {curr_count} 篇（+{curr_count - prev_count}）")
                    if curr_count == prev_count:
                        break
                    prev_count = curr_count

                for a in page.locator("a[href*='/news/id/']").all():
                    text = a.inner_text()
                    if re.search(r"區塊鏈", text):
                        continue

                    time_match = re.search(r"(\d{2}:\d{2})", text)
                    time_str = time_match.group(1) if time_match else ""

                    parts = re.split(r"(台股|精選|科技|房產|國際|理財|觀點)", text)
                    raw_title = parts[-1] if len(parts) > 1 else text
                    raw_title = re.sub(r"^\s*\d{2}:\d{2}\s*", "", raw_title)
                    title = raw_title.strip()

                    href = a.get_attribute("href")
                    full_url = f"https://news.cnyes.com{href}" if href.startswith("/") else href

                    if not title:
                        continue

                    news.append({
                        "time": time_str,
                        "title": title,
                        "url": full_url,
                    })

    seen = set()
    unique = []
    for n in news:
        if n["url"] not in seen:
            seen.add(n["url"])
            unique.append(n)

    print(f"[抓取] 完成，共 {len(unique)} 篇台股新聞")
    return unique


TW_KEYWORDS = ['聯發科', '鴻海', '台積電', '台股', '台達化', '永裕', '元大', '竑騰',
               '上市櫃', '大盤', '外資', '投信', '盤中', '盤後', '興櫃', '櫃買']


def _tw_score(title):
    return sum(1 for kw in TW_KEYWORDS if kw in title)


def _parse_numbered_links(page):
    links = page.locator("a[href*='/news/id/']").all()
    result = []
    for a in links:
        text = a.inner_text().strip()
        m = re.match(r'^(\d+)\.\s*(.+)$', text, re.DOTALL)
        if not m:
            continue
        href = a.get_attribute("href")
        full_url = f"https://news.cnyes.com{href}" if href.startswith("/") else href
        result.append({
            "rank": int(m.group(1)),
            "title": m.group(2).strip(),
            "url": full_url,
        })
    return result


def fetch_trending_tw_stock(use_system_chrome=False):
    news = []

    with sync_playwright() as p:
        browser_kwargs = {"headless": True, "args": ["--no-sandbox", "--disable-dev-shm-usage"]}
        if use_system_chrome:
            browser_kwargs["executable_path"] = CHROME_SYSTEM
        with p.chromium.launch(**browser_kwargs) as browser:
            with browser.new_page() as page:
                print(f"[抓取] 開啟 {TRENDING_URL}")
                page.goto(TRENDING_URL, timeout=PAGE_LOAD_TIMEOUT)
                page.wait_for_load_state("domcontentloaded", timeout=DOM_READY_TIMEOUT)
                page.wait_for_timeout(INITIAL_WAIT_MS)

                all_items = _parse_numbered_links(page)
                if not all_items:
                    print("[警告] 頁面中找不到任何編號新聞，可能頁面結構已變更")
                    return []

                tw_news = _detect_tw_section(all_items)

                if not tw_news:
                    print("[警告] 無法識別台股區塊，可能頁面結構已變更或無台股新聞")
                    return []

                print(f"[抓取] 完成，共 {len(tw_news)} 篇台股頭條")
                return tw_news


def _detect_tw_section(items):
    sections = []
    cur = []
    for item in items:
        if item["rank"] == 1 and cur:
            sections.append(cur)
            cur = []
        cur.append(item)
    if cur:
        sections.append(cur)

    scored = [(sum(_tw_score(i["title"]) for i in sec), sec) for sec in sections]
    scored.sort(key=lambda x: x[0], reverse=True)

    best_score, best_section = scored[0]
    if best_score > 0:
        section_label = _guess_section_label(best_section)
        print(f"[抓取] 以內容關鍵字識別『{section_label}』區塊（分數={best_score}）")
        return best_section[:10]

    matches = [i for i in items if _tw_score(i["title"]) > 0]
    if matches:
        print(f"[抓取] 以關鍵字比對取得 {len(matches)} 筆台股相關新聞")
        seen = set()
        unique = []
        for i in matches:
            if i["url"] not in seen:
                seen.add(i["url"])
                unique.append(i)
        unique.sort(key=lambda x: x["rank"])
        return unique[:10]

    return []


def _guess_section_label(section):
    if not section:
        return "未知"
    titles = " ".join(i["title"] for i in section)
    for label in ["台股", "美股", "科技", "房產", "國際", "理財", "觀點"]:
        if label in titles:
            return label
    return f"第{section[0]['rank']}區塊"


def format_telegram(news_list, date_str):
    parts = date_str.split("-")
    friendly_date = f"{parts[0]}/{parts[1]}/{parts[2]}" if len(parts) == 3 else date_str
    header = f"📰 鉅亨網台股快訊｜{friendly_date}"

    if not news_list:
        return [f"{header}\n\n今日尚無新增台股新聞"]

    return _split_messages(header, [_item_lines(n) for n in news_list])


def format_telegram_trending(news_list):
    now_str = datetime.now().strftime("%Y/%m/%d %H:%M")
    header = f"📊 鉅亨網台股頭條｜{now_str}"

    if not news_list:
        return [f"{header}\n\n暫無台股頭條新聞"]

    return _split_messages(header, [_trending_item_lines(n) for n in news_list])
