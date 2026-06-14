#!/usr/bin/env python3
"""
TWSE Monitor — 台灣證券交易所開放資料監控腳本
Base URL: https://openapi.twse.com.tw/v1

使用方法：
  python3 twse_monitor.py --check-messages                        # 單一模組
  python3 twse_monitor.py --check-messages --check-market         # 多個模組同時跑
  python3 twse_monitor.py --daily                                 # 每日完整總檢查
  python3 twse_monitor.py --debug --check-threshold               # debug 模式（寫 log）
  python3 twse_monitor.py --help                                  # 顯示說明

設定檔：~/.twse_monitor_config.json
DB：~/.twse_monitor.db
Log：/tmp/twse_monitor.log（--debug 模式開啟時）
"""

import json, os, sys, sqlite3, urllib.request, urllib.error
from datetime import datetime
from typing import List, Optional

# ─── 設定區 ───────────────────────────────────────────
DB_PATH     = os.path.expanduser("~/.twse_monitor.db")
CONFIG_PATH = os.path.expanduser("~/.twse_monitor_config.json")
LOG_PATH    = "/tmp/twse_monitor.log"

DEBUG_MODE  = False

def _load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}

CONFIG = _load_config()

WATCHLIST  = CONFIG.get("watchlist", ["0050", "2330", "00981A"])
THRESHOLDS = CONFIG.get("thresholds", {})

# ─── Debug Logger ──────────────────────────────────────
def _debug(msg: str):
    if DEBUG_MODE:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {msg}"
        print(line)
        try:
            with open(LOG_PATH, "a") as f:
                f.write(line + "\n")
        except Exception:
            pass

# ─── Telegram ─────────────────────────────────────────
def _tg_cfg():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return json.load(f)
    gold = os.path.expanduser("~/.qclaw/gold_monitor_config.json")
    if os.path.exists(gold):
        with open(gold) as f:
            return json.load(f)
    return {}

def send_telegram(text: str, urgent: bool = False) -> bool:
    """
    發送 Telegram 訊息。
    urgent=True → 強制 iOS/watchOS 響鈴 + 抬手
    urgent=False → 一般推播（依用戶 Telegram 設定）
    """
    cfg = _tg_cfg()
    token   = cfg.get("telegram_bot_token")
    chat_id = cfg.get("telegram_chat_id")
    if not token or not chat_id:
        _debug("send_telegram: 無設定，跳過")
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id":              chat_id,
        "text":                 text,
        "parse_mode":           "HTML",
        "disable_notification": False,
    }
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data,
                                      headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            _debug(f"send_telegram: ✅ 發送成功")
            return r.status == 200
    except Exception as e:
        _debug(f"send_telegram: ❌ 失敗 {e}")
        return False

# ─── TWSE API ──────────────────────────────────────────
BASE_URL = "https://openapi.twse.com.tw/v1"

def twse_get(path: str) -> Optional[List]:
    url = f"{BASE_URL}{path}"
    _debug(f"API請求: GET {url}")
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read().decode("utf-8")
            data = json.loads(raw)
            result = data if isinstance(data, list) else [data]
            _debug(f"API回應: {path} → {len(result)} 筆記錄")
            return result
    except Exception as e:
        _debug(f"API錯誤: {path} → {e}")
        send_telegram(f"⚠️ TWSE API 錯誤\n{path}\n{e}", urgent=True)
        return None

# ─── SQLite ────────────────────────────────────────────
def _db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS seen_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT, item_key TEXT UNIQUE, message TEXT, ts TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stocks (
            code TEXT PRIMARY KEY,
            name TEXT,
            cost REAL,          -- 持有成本（豪自己填入）
            close_today REAL,   -- 今日收盤（每日更新）
            close_prev REAL,    -- 昨日收盤（每日更新）
            updated_ts TEXT
        )
    """)
    conn.commit()
    return conn

def already_seen(cat: str, key: str) -> bool:
    conn = _db_conn()
    row = conn.execute(
        "SELECT 1 FROM seen_items WHERE category=? AND item_key=?",
        (cat, key)
    ).fetchone()
    conn.close()
    return row is not None

def mark_seen(cat: str, key: str, msg: str):
    conn = _db_conn()
    conn.execute(
        "INSERT OR REPLACE INTO seen_items (category,item_key,message,ts) VALUES (?,?,?,?)",
        (cat, key, msg, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    _debug(f"DB寫入: seen_items [{cat}] {key}")

def upsert_stock(code: str, name: str, close_today: float, close_prev: float):
    """更新 stocks 表：今日收盤 + 昨日收盤（漲跌幅計算用）"""
    conn = _db_conn()
    conn.execute("""
        INSERT INTO stocks (code,name,close_today,close_prev,updated_ts)
        VALUES (?,?,?,?,?)
        ON CONFLICT(code) DO UPDATE SET
            name=excluded.name,
            close_today=excluded.close_today,
            close_prev=excluded.close_prev,
            updated_ts=excluded.updated_ts
    """, (code, name, close_today, close_prev, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    _debug(f"DB寫入: stocks {code} close={close_today} prev={close_prev}")

def read_stock(code: str) -> Optional[dict]:
    """讀取 stocks 表單筆記錄"""
    conn = _db_conn()
    row = conn.execute("SELECT code,name,cost,close_today,close_prev,updated_ts FROM stocks WHERE code=?", (code,)).fetchone()
    conn.close()
    if row:
        return {"code":row[0],"name":row[1],"cost":row[2],
                "close_today":row[3],"close_prev":row[4],"updated_ts":row[5]}
    return None

def read_last_price(code: str) -> Optional[float]:
    """讀取 stocks.close_prev（昨日收盤）"""
    row = read_stock(code)
    if row and row["close_prev"]:
        return row["close_prev"]
    return None

def _fmt_date(d: str) -> str:
    try:
        return f"{int(d[:3]) + 1911}/{d[3:5]}/{d[5:7]}"
    except:
        return d

def _safe_float(v) -> Optional[float]:
    try:
        return float(v)
    except:
        return None

# ─── 閾值解析 ──────────────────────────────────────────
def _parse_pct_raw(raw) -> Optional[float]:
    if raw is None or raw is False:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    s = str(raw).strip().rstrip("%")
    try:
        return float(s)
    except ValueError:
        return None

def _parse_threshold_value(raw, close_price: float) -> tuple:
    """
    解析閾值，回傳 (threshold_float, is_percent, is_active)

    支援格式：
      2000          → 絕對價格
      \"+10\"         → close + 10
      \"-10\"         → close - 10
      \"+5%\"         → close × 1.05
      \"-5%\"         → close × 0.95
      \"90%\"         → close × 0.90
      null / false  → 不啟用
    """
    if raw is None or raw is False:
        return None, False, False
    if isinstance(raw, (int, float)):
        return float(raw), False, True
    s = str(raw).strip()
    # 純數字（可能是 \"+10\" 或 \"-10\"）
    if s.lstrip("+-").replace(".", "", 1).isdigit():
        delta = float(s)
        if close_price is not None:
            return close_price + delta, False, True
        return None, False, False
    # 百分比
    if s.endswith("%"):
        s_num = s.rstrip("%")
        try:
            pct = float(s_num)
        except ValueError:
            return None, False, False
        if close_price is None or close_price <= 0:
            return None, False, False
        if s.startswith("+"):
            val = close_price * (1 + pct / 100.0)
        elif s.startswith("-"):
            val = close_price * (1 - abs(pct) / 100.0)
        else:
            val = close_price * pct / 100.0
        return val, True, True
    return None, False, False

# ─── 模組一：重大訊息 ────────────────────────────────
def check_major_news() -> str:
    data = twse_get("/opendata/t187ap04_L")
    if not data:
        return ""
    watch = set(WATCHLIST)
    lines = []
    for item in data:
        code = item.get("公司代號", "").strip()
        if code not in watch:
            continue
        key = f"news_{item.get('發言日期','')}_{code}_{item.get('主旨 ', '')[:30]}"
        if already_seen("major_news", key):
            _debug(f"重大訊息已讀過: {code} {item.get('主旨 ','')[:30]}")
            continue
        name    = item.get("公司名稱", "")
        subject = item.get("主旨 ", "").replace("\r\n", " ").strip()
        date    = _fmt_date(item.get("發言日期", ""))
        lines.append(f"📢 <b>{name}({code})</b>\n   {date} · {subject[:80]}")
        mark_seen("major_news", key, subject[:50])
        _debug(f"新重大訊息: {code} {subject[:40]}")

    if lines:
        msg = f"【重大訊息】{len(lines)}則新訊息\n" + "\n\n".join(lines)
        send_telegram(msg)
    return msg

# ─── 模組二：除權除息預告 ─────────────────────────────
def check_dividends() -> str:
    data = twse_get("/exchangeReport/TWT48U_ALL")
    if not data:
        return ""
    watch = set(WATCHLIST)
    lines = []
    for item in data:
        code = item.get("Code", "").strip()
        if code not in watch:
            continue
        key = f"div_{item.get('Date','')}_{code}"
        if already_seen("dividend", key):
            _debug(f"除權除息已讀過: {code}")
            continue
        name   = item.get("Name", "")
        exdate = item.get("Exdividend", "-")
        cash   = item.get("CashDividend", "-")
        stock_r = item.get("StockDividendRatio", "-")
        lines.append(
            f"💰 <b>{name}({code})</b>\n"
            f"   除權息日: {exdate} · 現金股利: {cash} · 股票股利: {stock_r}"
        )
        mark_seen("dividend", key, f"{cash}/{stock_r}")
        _debug(f"新除權除息: {code} 現金={cash} 股票={stock_r}")

    if lines:
        msg = f"【除權除息預告】{len(lines)}則\n" + "\n\n".join(lines)
        send_telegram(msg)
    return msg

# ─── 模組三：殖利率/本益比 ─────────────────────────────
def check_valuation() -> str:
    data = twse_get("/exchangeReport/BWIBBU_ALL")
    if not data:
        return ""
    watch = set(WATCHLIST)
    conn  = _db_conn()
    lines = []
    for item in data:
        code = item.get("Code", "").strip()
        if code not in watch:
            continue
        pe   = item.get("PEratio", "-")
        yld  = item.get("DividendYield", "-")
        pb   = item.get("PBratio", "-")
        key  = f"val_{code}"
        row  = conn.execute(
            "SELECT message FROM seen_items WHERE category='valuation' AND item_key=?",
            (key,)
        ).fetchone()
        msg_val = f"{pe}|{yld}|{pb}"
        changed = False
        if row:
            if row[0] != msg_val:
                changed = True
                lines.append(
                    f"📊 <b>{item.get('Name','')}({code})</b>\n"
                    f"   本益比: {pe} · 殖利率: {yld}% · 淨值比: {pb}\n"
                    f"   (已變動)"
                )
        else:
            lines.append(
                f"📊 <b>{item.get('Name','')}({code})</b>\n"
                f"   本益比: {pe} · 殖利率: {yld}% · 淨值比: {pb}"
            )
            changed = True
        if changed:
            conn.execute(
                "INSERT OR REPLACE INTO seen_items (category,item_key,message,ts) "
                "VALUES ('valuation',?,?,?)",
                (key, msg_val, datetime.now().isoformat())
            )
            _debug(f"新評價資料: {code} PE={pe} Y={yld}% PB={pb}")
    conn.commit()
    conn.close()

    if lines:
        msg = f"【個股評價】{len(lines)}筆\n" + "\n\n".join(lines)
        send_telegram(msg)
    return msg

# ─── 模組四：個股日成交 ───────────────────────────────
def check_daily_price() -> str:
    data = twse_get("/exchangeReport/STOCK_DAY_ALL")
    if not data:
        return ""
    watch = set(WATCHLIST)
    lines = []
    for item in data:
        code   = item.get("Code", "").strip()
        if code not in watch:
            continue
        date   = item.get("Date", "")
        close  = _safe_float(item.get("ClosingPrice"))
        change = _safe_float(item.get("Change"))
        vol    = item.get("TradeVolume", "-")
        name   = item.get("Name", "")
        key    = f"price_{code}_{date}"

        if already_seen("daily_price", key):
            _debug(f"收盤行情已讀過: {code} {date}")
            return ""          # 今日已記錄，不重複通知

        # 用 Change 欄位還原昨日收盤
        prev_close = None
        if close is not None and change is not None and (close - change) != 0:
            prev_close = close - change

        # 更新 stocks 表
        if close is not None:
            upsert_stock(code, name, close, prev_close if prev_close else close)

        try:
            vol_fmt = f"{int(vol):,}"
        except:
            vol_fmt = vol
        chg_str = f"{change:+.2f}" if change is not None else "+?"
        lines.append(
            f"📈 <b>{name}({code})</b>\n"
            f"   收盤: {close:.2f} ({chg_str}) · 成交量: {vol_fmt}"
        )
        mark_seen("daily_price", key,
                  f"{close:.2f}|{change:.4f}" if change is not None else f"{close:.2f}|0")
        _debug(f"新收盤行情: {code} close={close} change={chg_str} prev={prev_close}")

    if lines:
        msg = f"【收盤行情】{len(lines)}筆\n" + "\n\n".join(lines)
        send_telegram(msg)
    return msg

# ─── 模組五：股價閾值監控 ────────────────────────────
def check_price_threshold() -> str:
    """
    以今日收盤行情比對閾值，分級推播：
      🔴 漲停 / 跌停     → urgent
      🟡 價格逾越        → urgent
      🔵 百分比警告      → 一般
    """
    data = twse_get("/exchangeReport/STOCK_DAY_ALL")
    if not data:
        return ""

    watch       = set(WATCHLIST)
    urgent_buf  = []
    norm_buf    = []

    for item in data:
        code   = item.get("Code", "").strip()
        if code not in watch:
            continue
        close  = _safe_float(item.get("ClosingPrice"))
        change = _safe_float(item.get("Change"))
        name   = item.get("Name", "")
        date   = item.get("Date", "")

        if close is None:
            continue

        # ── 昨日收盤（stocks 表 或 Change 欄位還原）─────
        prev_close = read_last_price(code)
        if prev_close is None and change is not None and (close - change) != 0:
            prev_close = close - change
        _debug(f"閾值監控 {code}: close={close} prev={prev_close}")

        # ── 漲跌幅 % ──────────────────────────────
        circuit_pct  = float(THRESHOLDS.get(code, {}).get("circuit_pct", 10.0))
        circuit_up   = THRESHOLDS.get(code, {}).get("circuit_up",   True)
        circuit_down = THRESHOLDS.get(code, {}).get("circuit_down", True)
        pct_move = (close - prev_close) / prev_close * 100 if prev_close and prev_close > 0 else 0.0
        _debug(f"  pct_move={pct_move:.2f}% circuit_up={circuit_up} down={circuit_down}")

        if circuit_up and pct_move >= circuit_pct:
            urgent_buf.append(f"🔴 <b>漲停！{name}({code})</b>\n   收盤: {close:.2f} (+{pct_move:.1f}%)")
            _debug(f"  → 🔴 觸發漲停")
        elif circuit_down and pct_move <= -circuit_pct:
            urgent_buf.append(f"🔴 <b>跌停！{name}({code})</b>\n   收盤: {close:.2f} ({pct_move:.1f}%)")
            _debug(f"  → 🔴 觸發跌停")

        # ── 動態預設閾值（close ± 10）───────────────
        raw_max = THRESHOLDS.get(code, {}).get("max_price")
        raw_min = THRESHOLDS.get(code, {}).get("min_price")
        max_val, max_pct, max_on = _parse_threshold_value(raw_max, close)
        if not max_on:
            max_val, max_pct = close + 10, False
            max_on = True
            _debug(f"  max_price 預設 close+10 = {max_val}")
        min_val, min_pct, min_on = _parse_threshold_value(raw_min, close)
        if not min_on:
            min_val, min_pct = close - 10, False
            min_on = True
            _debug(f"  min_price 預設 close-10 = {min_val}")

        if max_on and max_val is not None and close >= max_val:
            label = "相對高點" if max_pct else "絕對高點"
            urgent_buf.append(f"🟡 <b>{name}({code}) 突破{label}</b>\n   收盤: {close:.2f} ≥ 閾值 {max_val:.2f}")
            _debug(f"  → 🟡 突破 max ({max_val})")
        if min_on and min_val is not None and close <= min_val:
            label = "相對低點" if min_pct else "絕對低點"
            urgent_buf.append(f"🟡 <b>{name}({code}) 跌破{label}</b>\n   收盤: {close:.2f} ≤ 閾值 {min_val:.2f}")
            _debug(f"  → 🟡 跌破 min ({min_val})")

        # ── 百分比閾值（預設 ±5%）─────────────────
        if prev_close and prev_close > 0:
            pct_up   = THRESHOLDS.get(code, {}).get("max_pct_up",   5)
            pct_down = THRESHOLDS.get(code, {}).get("max_pct_down", 5)
            up_val   = _parse_pct_raw(pct_up)
            dn_val   = _parse_pct_raw(pct_down)
            if up_val and pct_move >= up_val:
                urgent_buf.append(f"🔵 <b>{name}({code}) 單日大漲</b>\n   +{pct_move:.1f}%  閾值: ≥{up_val}%")
                _debug(f"  → 🔵 大漲 {pct_move:.1f}% ≥ {up_val}%")
            if dn_val and pct_move <= -dn_val:
                urgent_buf.append(f"🔵 <b>{name}({code}) 單日大跌</b>\n   {pct_move:.1f}%  閾值: ≥{dn_val}%")
                _debug(f"  → 🔵 大跌 {pct_move:.1f}% ≥ {dn_val}%")

    all_buf = urgent_buf + norm_buf
    if not all_buf:
        _debug("閾值監控：無觸發")
        return ""

    parts = []
    if urgent_buf:
        parts.append("🚨 【股價警報】\n" + "\n\n".join(urgent_buf))
    if norm_buf:
        parts.append("【股價提示】\n" + "\n\n".join(norm_buf))

    has_circuit = any("漲停" in l or "跌停" in l for l in urgent_buf)
    msg = "\n\n".join(parts)
    send_telegram(msg, urgent=bool(urgent_buf))
    _debug(f"閾值監控：發送通知 ({len(urgent_buf)} 筆緊急, {len(norm_buf)} 筆一般)")
    return msg

# ─── 模組六：注意/處置股票 ─────────────────────────────
def check_alerts() -> str:
    parts = []

    notice_data = twse_get("/announcement/notice")
    if notice_data:
        watch = set(WATCHLIST)
        lines = []
        for item in notice_data:
            code = item.get("Code", "").strip()
            if not code or code not in watch:
                continue
            key = f"notice_{code}_{item.get('Date','')}"
            if already_seen("alert_notice", key):
                continue
            info   = item.get("TradingInfoForAttention", "")
            close  = item.get("ClosingPrice", "")
            lines.append(f"⚠️ <b>{item.get('Name','')}({code})</b> 已被列為注意股票\n   收盤: {close} · {info[:60]}")
            mark_seen("alert_notice", key, "")
            _debug(f"注意股票: {code}")
        if lines:
            parts.append(f"【注意股票】{len(lines)}則\n" + "\n".join(lines))

    punish_data = twse_get("/announcement/punish")
    if punish_data:
        watch = set(WATCHLIST)
        lines = []
        for item in punish_data:
            code = item.get("Code", "").strip()
            if not code or code not in watch:
                continue
            key = f"punish_{code}_{item.get('Date','')}"
            if already_seen("alert_punish", key):
                continue
            reason = item.get("ReasonsOfDisposition", "")[:60]
            period = item.get("DispositionPeriod", "")
            lines.append(f"🔴 <b>{item.get('Name','')}({code})</b> 處置\n   {reason}\n   期間: {period}")
            mark_seen("alert_punish", key, "")
            _debug(f"處置股票: {code}")
        if lines:
            parts.append(f"【處置股票】{len(lines)}則\n" + "\n".join(lines))

    # ── 變更交易（TWT85U）─────────────────────────────
    change_data = twse_get("/exchangeReport/TWT85U")
    if change_data:
        watch = set(WATCHLIST)
        lines = []
        for item in change_data:
            code = item.get("Code", "").strip()
            if not code or code not in watch:
                continue
            key = f"change_{code}"
            if already_seen("alert_change", key):
                continue
            name = item.get("Name", "")
            info = item.get("PeriodicCallAuctionTrading", "").strip()
            lines.append(f"🟠 <b>{name}({code})</b> 變更交易\n   {info}")
            mark_seen("alert_change", key, "")
            _debug(f"變更交易: {code}")
        if lines:
            parts.append(f"【變更交易】{len(lines)}則\n" + "\n".join(lines))

    # ── 暫停交易（TWTAWU）─────────────────────────────
    halt_data = twse_get("/exchangeReport/TWTAWU")
    if halt_data:
        watch = set(WATCHLIST)
        lines = []
        for item in halt_data:
            code = item.get("Code", "").strip()
            if not code or code not in watch:
                continue
            key = f"halt_{code}_{item.get('TradingHaltDate','')}"
            if already_seen("alert_halt", key):
                continue
            name = item.get("Name", "")
            halt_date = item.get("TradingHaltDate", "")
            halt_time = item.get("TradingHaltTime", "")
            resume_date = item.get("TradingResumptionDate", "")
            lines.append(f"⛔ <b>{name}({code})</b> 暫停交易\n   暫停: {halt_date} {halt_time}\n   恢復: {resume_date or '未定'}")
            mark_seen("alert_halt", key, "")
            _debug(f"暫停交易: {code}")
        if lines:
            parts.append(f"【暫停交易】{len(lines)}則\n" + "\n".join(lines))

    msg = "\n\n".join(parts)
    if msg:
        send_telegram(msg, urgent=bool(punish_data))
    return msg

# ─── 模組八：公司治理 / ESG 監控 ──────────────────────
def check_governance() -> str:
    """監控裁罰案件、違反資訊申報、經營權異動、ESG 重大揭露"""
    watch = set(WATCHLIST)
    parts = []

    # ── 1. 裁罰案件（t187ap22_L）🔴 緊急 ────────────────
    data = twse_get("/opendata/t187ap22_L")
    if data:
        lines = []
        for item in data:
            # 注意：此 API 用「股票代號」而非「公司代號」
            code = item.get("股票代號", "").strip()
            if code not in watch:
                continue
            key = f"penalty_{item.get('發函日期','')}_{code}"
            if already_seen("gov_penalty", key):
                continue
            name   = item.get("公司名稱", "")
            reason = item.get("違規事由", "").replace("\r\n", " ")[:80]
            result = item.get("裁處情形", "")[:60]
            lines.append(
                f"🔴 <b>{name}({code})</b> 裁罰\n"
                f"   {reason}\n   裁處: {result}"
            )
            mark_seen("gov_penalty", key, "")
            _debug(f"裁罰案件: {code}")
        if lines:
            parts.append(f"【裁罰案件】{len(lines)}則\n" + "\n\n".join(lines))

    # ── 2. 違反資訊申報（t187ap23_L）🟡 ────────────────
    data2 = twse_get("/opendata/t187ap23_L")
    if data2:
        lines = []
        for item in data2:
            code = item.get("公司代號", "").strip()
            if code not in watch:
                continue
            key = f"violation_{item.get('出表日期','')}_{code}"
            if already_seen("gov_violation", key):
                continue
            name  = item.get("公司名稱", "")
            # 動態取所有欄位組成摘要
            vals = {k: v for k, v in item.items() if k not in ("出表日期", "公司代號", "公司名稱") and v and v != "-"}
            detail = " · ".join(f"{k}:{str(v)[:30]}" for k, v in vals.items())[:120]
            lines.append(f"🟡 <b>{name}({code})</b> 違反資訊申報\n   {detail}")
            mark_seen("gov_violation", key, "")
            _debug(f"違反資訊申報: {code}")
        if lines:
            parts.append(f"【違反資訊申報】{len(lines)}則\n" + "\n\n".join(lines))

    # ── 3. 經營權異動（t187ap24_L + t187ap27_L）🔴 ──────
    for path, label in [("/opendata/t187ap24_L", "經營權異動"),
                        ("/opendata/t187ap27_L", "經營權異動+變更交易")]:
        d = twse_get(path)
        if not d:
            continue
        cat = "gov_mgmt_change_24" if "24" in path else "gov_mgmt_change_27"
        lines = []
        for item in d:
            code = item.get("公司代號", "").strip()
            if code not in watch:
                continue
            key = f"mgmt_{item.get('出表日期','')}_{code}_{label}"
            if already_seen(cat, key):
                continue
            name = item.get("公司名稱", "")
            date = item.get("經營權異動日期", "")
            desc = item.get("經營權異動說明", "")[:80]
            emoji = "🔴" if "27" in path else "🟠"
            lines.append(f"{emoji} <b>{name}({code})</b> {label}\n   {date}: {desc}")
            mark_seen(cat, key, "")
            _debug(f"{label}: {code}")
        if lines:
            parts.append(f"【{label}】{len(lines)}則\n" + "\n\n".join(lines))

    # ── 4. ESG 重大揭露（t187ap46_L_16 資安 + _21 職安）🔵 ──
    esg_endpoints = [
        ("/opendata/t187ap46_L_16", "資訊安全", "esg_infosec"),
        ("/opendata/t187ap46_L_21", "職業安全衛生", "esg_occupational"),
    ]
    for path, esg_label, cat in esg_endpoints:
        d = twse_get(path)
        if not d:
            continue
        lines = []
        for item in d:
            code = item.get("公司代號", "").strip()
            if code not in watch:
                continue
            report_year = item.get("報告年度", "")
            key = f"esg_{code}_{report_year}_{esg_label}"
            if already_seen(cat, key):
                continue
            name = item.get("公司名稱", "")
            # 動態取有意義欄位
            vals = {k: v for k, v in item.items()
                    if k not in ("出表日期", "報告年度", "公司代號", "公司名稱") and v and str(v).strip() not in ("-", "")}
            detail = " · ".join(f"{k}:{str(v)[:30]}" for k, v in list(vals.items())[:4])[:120]
            lines.append(f"🔵 <b>{name}({code})</b> ESG-{esg_label} ({report_year})\n   {detail}")
            mark_seen(cat, key, "")
            _debug(f"ESG {esg_label}: {code}")
        if lines:
            parts.append(f"【ESG-{esg_label}】{len(lines)}則\n" + "\n\n".join(lines))

    msg = "\n\n".join(parts)
    if msg:
        has_urgent = any("裁罰" in p or "變更交易" in p for p in parts)
        send_telegram(msg, urgent=has_urgent)
    return msg

# ─── 模組九：月營收 / EPS 監控 ────────────────────────
def check_revenue() -> str:
    """監控關注股票的月營收公布 + 產業 EPS 統計 + 財測差異"""
    watch = set(WATCHLIST)
    parts = []

    # ── 1. 月營收（t187ap05_L）─────────────────────────
    data = twse_get("/opendata/t187ap05_L")
    if data:
        lines = []
        for item in data:
            code = item.get("公司代號", "").strip()
            if code not in watch:
                continue
            ym   = item.get("資料年月", "")
            key  = f"revenue_{code}_{ym}"
            if already_seen("revenue", key):
                _debug(f"月營收已讀過: {code} {ym}")
                continue
            name    = item.get("公司名稱", "")
            industry = item.get("產業別", "")
            # 營收數字（單位：千元）
            cur_rev   = item.get("營業收入-當月營收", "-")
            prev_rev  = item.get("營業收入-上月營收", "-")
            yoy_rev   = item.get("營業收入-去年當月營收", "-")
            mom_pct   = item.get("營業收入-上月比較增減(%)", "-")
            yoy_pct   = item.get("營業收入-去年同月增減(%)", "-")
            acc_rev   = item.get("累計營業收入-當月累計營收", "-")
            acc_yoy   = item.get("累計營業收入-前期比較增減(%)", "-")
            # 格式化
            try:
                cur_fmt = f"{int(cur_rev):,}"
            except:
                cur_fmt = cur_rev
            try:
                acc_fmt = f"{int(acc_rev):,}"
            except:
                acc_fmt = acc_rev
            # 民國年格式
            try:
                y = int(ym[:3]) + 1911
                ym_fmt = f"{y}/{ym[3:5]}"
            except:
                ym_fmt = ym
            lines.append(
                f"📊 <b>{name}({code})</b> {industry} · {ym_fmt}\n"
                f"   當月營收: {cur_fmt}\n"
                f"   月增: {mom_pct}%  年增: {yoy_pct}%\n"
                f"   累計: {acc_fmt}  年增: {acc_yoy}%"
            )
            mark_seen("revenue", key, f"{cur_rev}|{yoy_pct}")
            _debug(f"新月營收: {code} {ym} YoY={yoy_pct}%")
        if lines:
            parts.append(f"【月營收公告】{len(lines)}則\n" + "\n\n".join(lines))

    # ── 2. 產業 EPS 統計（t187ap14_L）───────────────────
    data2 = twse_get("/opendata/t187ap14_L")
    if data2:
        lines = []
        for item in data2:
            code = item.get("公司代號", "").strip()
            if code not in watch:
                continue
            yq  = f"{item.get('年度','')}Q{item.get('季別','')}"
            key = f"eps_{code}_{yq}"
            if already_seen("eps", key):
                continue
            name  = item.get("公司名稱", "")
            eps   = item.get("基本每股盈餘(元)", "-")
            rev   = item.get("營業收入", "-")
            oi    = item.get("營業利益", "-")
            ni    = item.get("稅後淨利", "-")
            try:
                rev_fmt = f"{int(rev):,}"
            except:
                rev_fmt = rev
            lines.append(
                f"💰 <b>{name}({code})</b> EPS {eps}元 · {yq}\n"
                f"   營收: {rev_fmt}  營業利益: {oi}  淨利: {ni}"
            )
            mark_seen("eps", key, f"{eps}")
            _debug(f"新EPS: {code} {yq} EPS={eps}")
        if lines:
            parts.append(f"【EPS統計】{len(lines)}則\n" + "\n\n".join(lines))

    # ── 3. 財測差異 10%+（t187ap16_L）───────────────────
    data3 = twse_get("/opendata/t187ap16_L")
    if data3:
        lines = []
        for item in data3:
            code = item.get("公司代號", "").strip()
            if code not in watch:
                continue
            key = f"forecast_{code}_{item.get('年度','')}_{item.get('季別','')}"
            if already_seen("forecast_diff", key):
                continue
            name = item.get("公司名稱", "")
            lines.append(f"⚠️ <b>{name}({code})</b> 財測差異超標\n   {json.dumps(item, ensure_ascii=False)[:200]}")
            mark_seen("forecast_diff", key, "")
            _debug(f"財測差異: {code}")
        if lines:
            parts.append(f"【財測差異警報】{len(lines)}則\n" + "\n\n".join(lines))

    msg = "\n\n".join(parts)
    if msg:
        send_telegram(msg)
    return msg

# ─── 模組九：董監事持股變動 ──────────────────────────
def check_insider() -> str:
    """監控關注股票的內部人持股轉讓申報 + 董監事持股變動"""
    watch = set(WATCHLIST)
    parts = []

    # ── 1. 持股轉讓申報（t187ap12_L）──────────────────
    data = twse_get("/opendata/t187ap12_L")
    if data:
        lines = []
        for item in data:
            code = item.get("公司代號", "").strip()
            if code not in watch:
                continue
            key = f"insider_{item.get('出表日期','')}_{code}_{item.get('姓名','')}_{item.get('預定轉讓方式及股數-轉讓股數','')}"
            if already_seen("insider_transfer", key):
                _debug(f"董監事轉讓已讀過: {code} {item.get('姓名','')}")
                continue
            name     = item.get("公司名稱", "")
            person   = item.get("姓名", "")
            role     = item.get("申報人身分", "")
            method   = item.get("預定轉讓方式及股數-轉讓方式", "")
            shares   = item.get("預定轉讓方式及股數-轉讓股數", "-")
            holding  = item.get("目前持有股數-自有持股", "-")
            period   = item.get("有效轉讓期間", "")
            try:
                shares_fmt = f"{int(shares):,}" if shares else "-"
            except:
                shares_fmt = shares
            try:
                hold_fmt = f"{int(holding):,}" if holding else "-"
            except:
                hold_fmt = holding
            lines.append(
                f"👤 <b>{name}({code})</b>\n"
                f"   {role} {person} 預定轉讓\n"
                f"   方式: {method} · 股數: {shares_fmt} · 持有: {hold_fmt}\n"
                f"   期間: {period}"
            )
            mark_seen("insider_transfer", key, f"{person}:{shares}")
            _debug(f"新持股轉讓: {code} {person} {shares}")
        if lines:
            parts.append(f"【內部人持股轉讓】{len(lines)}則\n" + "\n\n".join(lines))

    # ── 2. 董監事持股餘額（t187ap11_L，資料量大，只取關注股票）──
    data2 = twse_get("/opendata/t187ap11_L")
    if data2:
        lines = []
        for item in data2:
            code = item.get("公司代號", "").strip()
            if code not in watch:
                continue
            key = f"holding_{item.get('資料年月','')}_{code}_{item.get('姓名','')}"
            if already_seen("insider_holding", key):
                continue
            name    = item.get("公司名稱", "")
            person  = item.get("姓名", "")
            title   = item.get("職稱", "")
            current = item.get("目前持股", "-")
            elected = item.get("選任時持股 ", "-")
            pledge  = item.get("設質股數", "-")
            pledge_pct = item.get("設質股數佔持股比例", "-")
            try:
                cur_fmt = f"{int(current):,}"
            except:
                cur_fmt = current
            try:
                elect_fmt = f"{int(elected):,}"
            except:
                elect_fmt = elected
            lines.append(
                f"📋 <b>{name}({code})</b> {title} {person}\n"
                f"   選任時: {elect_fmt} → 目前: {cur_fmt} · 設質: {pledge} ({pledge_pct})"
            )
            mark_seen("insider_holding", key, f"{person}:{current}")
            _debug(f"董監事持股: {code} {person} {current}")
        if lines:
            parts.append(f"【董監事持股明細】{len(lines)}則\n" + "\n\n".join(lines))

    msg = "\n\n".join(parts)
    if msg:
        send_telegram(msg)
    return msg

# ─── 模組十一：盤中即時報價 ──────────────────────────
# 參考 twstock (MIT License) realtime.py 實作
# https://github.com/mlouielu/twstock

def _get_stock_prefix(code: str) -> str:
    """判斷股票是上市(tse)或上櫃(otc)，回傳前綴"""
    # 已知的 OTC 股票（上櫃）
    otc_codes = set()  # 如有上櫃股票加入此處
    if code in otc_codes:
        return "otc"
    return "tse"

def fetch_realtime_quote(code: str) -> Optional[dict]:
    """
    抓取盤中即時報價（參考 twstock MIT 原始碼）
    回傳 dict: {code, name, open, high, low, close, volume, prev_close}
    """
    prefix = _get_stock_prefix(code)
    stock_id = f"{prefix}_{code}.tw"
    ts = int(datetime.now().timestamp() * 1000)
    url = f"http://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch={stock_id}&_={ts}"
    _debug(f"即時報價請求: {url}")
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode("utf-8"))
        if not data.get("msgArray"):
            _debug(f"即時報價: {code} msgArray 為空")
            return None
        item = data["msgArray"][0]
        result = {
            "code": code,
            "name": item.get("n", ""),
            "open": _safe_float(item.get("o")),
            "high": _safe_float(item.get("h")),
            "low": _safe_float(item.get("l")),
            "close": _safe_float(item.get("z")),
            "volume": _safe_float(item.get("v")),
            "prev_close": _safe_float(item.get("y")),
        }
        _debug(f"即時報價: {code} O={result['open']} H={result['high']} L={result['low']} C={result['close']} V={result['volume']}")
        return result
    except Exception as e:
        _debug(f"即時報價錯誤: {code} {e}")
        return None

def check_realtime() -> str:
    """盤中即時報價 + 閾值監控（用即時價替代收盤價）"""
    if not CONFIG.get("realtime_enabled", True):
        _debug("即時報價: 已關閉")
        return ""

    urgent_buf = []
    norm_buf = []

    for code in WATCHLIST:
        q = fetch_realtime_quote(code)
        if not q or q["close"] is None:
            continue

        close = q["close"]
        prev_close = q["prev_close"]
        name = q["name"]
        vol = q["volume"]

        if prev_close and prev_close > 0:
            pct_move = (close - prev_close) / prev_close * 100
        else:
            pct_move = 0.0

        _debug(f"即時閾值 {code}: close={close} prev={prev_close} pct={pct_move:.2f}%")

        t = THRESHOLDS.get(code, {})
        circuit_pct = float(t.get("circuit_pct", 10.0))
        circuit_up = t.get("circuit_up", True)
        circuit_down = t.get("circuit_down", True)

        # 漲停/跌停
        if circuit_up and pct_move >= circuit_pct:
            urgent_buf.append(f"🔴 <b>漲停！{name}({code})</b>\n   即時: {close:.2f} (+{pct_move:.1f}%)")
            _debug(f"  → 🔴 即時漲停")
        elif circuit_down and pct_move <= -circuit_pct:
            urgent_buf.append(f"🔴 <b>跌停！{name}({code})</b>\n   即時: {close:.2f} ({pct_move:.1f}%)")
            _debug(f"  → 🔴 即時跌停")

        # 動態閾值
        raw_max = t.get("max_price")
        raw_min = t.get("min_price")
        max_val, max_pct, max_on = _parse_threshold_value(raw_max, close)
        if not max_on:
            max_val, max_pct = close + 10, False
            max_on = True
        min_val, min_pct, min_on = _parse_threshold_value(raw_min, close)
        if not min_on:
            min_val, min_pct = close - 10, False
            min_on = True

        if max_on and max_val is not None and close >= max_val:
            urgent_buf.append(f"🟡 <b>{name}({code}) 突破高點</b>\n   即時: {close:.2f} ≥ {max_val:.2f}")
        if min_on and min_val is not None and close <= min_val:
            urgent_buf.append(f"🟡 <b>{name}({code}) 跌破低點</b>\n   即時: {close:.2f} ≤ {min_val:.2f}")

        # 百分比
        pct_up = _parse_pct_raw(t.get("max_pct_up", 5))
        pct_down = _parse_pct_raw(t.get("max_pct_down", 5))
        if pct_up and pct_move >= pct_up:
            urgent_buf.append(f"🔵 <b>{name}({code}) 盤中大漲</b>\n   +{pct_move:.1f}%")
        if pct_down and pct_move <= -pct_down:
            urgent_buf.append(f"🔵 <b>{name}({code}) 盤中大跌</b>\n   {pct_move:.1f}%")

        # 更新 stocks 表即時價
        conn = _db_conn()
        conn.execute("UPDATE stocks SET close_today=? WHERE code=?", (close, code))
        conn.commit()
        conn.close()

    all_buf = urgent_buf + norm_buf
    if not all_buf:
        _debug("即時報價：無觸發")
        return ""

    parts = []
    if urgent_buf:
        parts.append("🚨 【盤中即時警報】\n" + "\n\n".join(urgent_buf))
    if norm_buf:
        parts.append("【盤中提示】\n" + "\n\n".join(norm_buf))

    msg = "\n\n".join(parts)
    send_telegram(msg, urgent=bool(urgent_buf))
    return msg


# ─── 模組十二：四大買賣點（Best Four Point）──────────────
# 參考 twstock (MIT License) analytics.py 實作
# https://github.com/mlouielu/twstock
# 原始授權：MIT License, Copyright (c) mlouielu

def _moving_average(data: list, window: int) -> list:
    """計算簡單移動平均線（SMA）"""
    result = []
    for i in range(len(data)):
        if i < window - 1:
            result.append(None)
        else:
            result.append(sum(data[i - window + 1:i + 1]) / window)
    return result

def _continuous(ma: list) -> int:
    """判斷均線連續趨勢：1=上揚, -1=下滑, 0=盤整"""
    if len(ma) < 2 or ma[-1] is None or ma[-2] is None:
        return 0
    if ma[-1] > ma[-2]:
        return 1
    elif ma[-1] < ma[-2]:
        return -1
    return 0

def _ma_bias_ratio(ma3: list, ma6: list) -> list:
    """計算 3/6 均線乖離率"""
    result = []
    for i in range(len(ma3)):
        if ma3[i] is None or ma6[i] is None or ma6[i] == 0:
            result.append(None)
        else:
            result.append((ma3[i] - ma6[i]) / ma6[i])
    return result

def _ma_bias_ratio_pivot(bias: list, days: int = 3) -> tuple:
    """
    極轉點偵測
    回傳 (best_buy_pivot, best_sell_pivot)
    - buy_pivot: True = 近 days 天內有乖離率極大值（可能反轉向下→買點閘門）
    - sell_pivot: True = 近 days 天內有乖離率極小值（可能反轉向上→賣點閘門）
    """
    if len(bias) < days + 1:
        return False, False

    recent = [b for b in bias[-(days + 1):] if b is not None]
    if len(recent) < 2:
        return False, False

    buy_pivot = False
    sell_pivot = False

    # 極大值：近 days 天內出現高峰（前低後高再低）
    for i in range(1, len(recent) - 1):
        if recent[i] > recent[i - 1] and recent[i] > recent[i + 1] and recent[i] > 0:
            buy_pivot = True
        if recent[i] < recent[i - 1] and recent[i] < recent[i + 1] and recent[i] < 0:
            sell_pivot = True

    return buy_pivot, sell_pivot

def check_best_four_point() -> str:
    """
    四大買賣點判斷（參考 twstock MIT 原始碼）
    需至少 6 天歷史 OHLCV 才能計算 MA3/MA6
    """
    if not CONFIG.get("bfp_enabled", True):
        _debug("BFP: 已關閉")
        return ""

    bfp_days = int(CONFIG.get("bfp_days", 31))
    parts = []

    for code in WATCHLIST:
        # 從 stocks 表讀歷史 OHLCV（需累積）
        conn = _db_conn()
        rows = conn.execute(
            "SELECT item_key, message FROM seen_items "
            "WHERE category='daily_price' AND item_key LIKE ? "
            "ORDER BY ts DESC LIMIT ?",
            (f"price_{code}_%", bfp_days)
        ).fetchall()
        conn.close()

        if len(rows) < 6:
            _debug(f"BFP {code}: 歷史資料不足（{len(rows)}/6）")
            continue

        # 解析歷史價格（由舊到新）
        closes = []
        volumes = []
        opens = []
        for key, msg in reversed(rows):
            parts_k = msg.split("|")
            closes.append(float(parts_k[0]))
            volumes.append(float(parts_k[1].replace("+", "")))
            # opens 暫用收盤近似（daily_price 未存開盤價）
            opens.append(float(parts_k[0]))

        # 計算均線
        ma3 = _moving_average(closes, 3)
        ma6 = _moving_average(closes, 6)
        bias = _ma_bias_ratio(ma3, ma6)
        cont = _continuous(ma3)
        buy_pivot, sell_pivot = _ma_bias_ratio_pivot(bias)

        _debug(f"BFP {code}: close={closes[-1]} vol={volumes[-1]} MA3={ma3[-1]} MA6={ma6[-1]} cont={cont} bias={bias[-1]}")
        _debug(f"  buy_pivot={buy_pivot} sell_pivot={sell_pivot}")

        # 四大買點判斷
        buy_reasons = []
        if len(closes) >= 2 and len(volumes) >= 2 and len(opens) >= 2:
            # 買1：量大收紅
            if volumes[-1] > volumes[-2] and closes[-1] > opens[-1]:
                buy_reasons.append("量大收紅")
            # 買2：量縮價不跌（修正版：今日收 ≥ 昨日收）
            if volumes[-1] < volumes[-2] and closes[-1] >= closes[-2]:
                buy_reasons.append("量縮價不跌")
            # 買3：三日均線上揚
            if cont == 1:
                buy_reasons.append("三日均線上揚")
            # 買4：MA3 > MA6
            if ma3[-1] is not None and ma6[-1] is not None and ma3[-1] > ma6[-1]:
                buy_reasons.append("MA3>MA6")

        # 四大賣點判斷
        sell_reasons = []
        if len(closes) >= 2 and len(volumes) >= 2 and len(opens) >= 2:
            # 賣1：量大收黑
            if volumes[-1] > volumes[-2] and closes[-1] < opens[-1]:
                sell_reasons.append("量大收黑")
            # 賣2：量縮價跌（修正版：今日收 < 昨日收）
            if volumes[-1] < volumes[-2] and closes[-1] < closes[-2]:
                sell_reasons.append("量縮價跌")
            # 賣3：三日均線下滑
            if cont == -1:
                sell_reasons.append("三日均線下滑")
            # 賣4：MA3 < MA6
            if ma3[-1] is not None and ma6[-1] is not None and ma3[-1] < ma6[-1]:
                sell_reasons.append("MA3<MA6")

        # 閘門 + 去重
        name = read_stock(code)["name"] if read_stock(code) else code
        bfp_key = f"bfp_{code}_{closes[-1]}"
        if already_seen("bfp_signal", bfp_key):
            _debug(f"BFP {code}: 已通知過")
            continue

        if buy_reasons and buy_pivot:
            msg = (
                f"🟢【四大買點】{name}({code})\n"
                f"   觸發：{'、'.join(buy_reasons)}\n"
                f"   收盤: {closes[-1]:.2f} | MA3: {ma3[-1]:.2f} | MA6: {ma6[-1]:.2f}"
            )
            parts.append(msg)
            mark_seen("bfp_signal", bfp_key, "+".join(buy_reasons))
            _debug(f"  → 🟢 買點觸發")

        if sell_reasons and sell_pivot:
            msg = (
                f"🔴【四大賣點】{name}({code})\n"
                f"   觸發：{'、'.join(sell_reasons)}\n"
                f"   收盤: {closes[-1]:.2f} | MA3: {ma3[-1]:.2f} | MA6: {ma6[-1]:.2f}"
            )
            parts.append(msg)
            mark_seen("bfp_signal", bfp_key, "+".join(sell_reasons))
            _debug(f"  → 🔴 賣點觸發")

    if not parts:
        _debug("BFP：無觸發")
        return ""

    msg = "\n\n".join(parts)
    send_telegram(msg, urgent=True)
    return msg

# ─── 模組：大盤統計 ────────────────────────────────
def check_market() -> str:
    """大盤指數每日摘要（含加權指數 + 台灣50 + 歷史走勢）"""
    watch = set(WATCHLIST)
    parts = []

    # ── 1. 大盤統計（MI_INDEX）────────────────────────
    data = twse_get("/exchangeReport/MI_INDEX")
    if data:
        item       = data[0]
        index_name = item.get("指數", "加權指數")
        close      = item.get("收盤指數", "-")
        direction  = item.get("漲跌", "+")
        change_pts = item.get("漲跌點數", "-")
        change_pct = item.get("漲跌百分比", "-")
        note       = item.get("特殊處理註記", "")
        date_fmt   = _fmt_date(item.get("日期", ""))

        emoji    = "🔺" if direction == "+" else "🔻"
        note_txt = f" ({note})" if note else ""
        parts.append(
            f"{emoji} <b>{index_name}</b>\n"
            f"   收盤: {close} {direction}{change_pts} ({change_pct}%){note_txt}"
        )
        _debug(f"大盤: {index_name} {close} {direction}{change_pts} ({change_pct}%)")

    # ── 2. 台灣50指數（TAI50I）───────────────────────
    data2 = twse_get("/indicesReport/TAI50I")
    if data2:
        for item in data2:
            idx   = item.get("Taiwan50Index", "-")
            total = item.get("Taiwan50TotalReturnIndex", "-")
            date_fmt = _fmt_date(item.get("Date", ""))
            parts.append(f"📊 <b>臺灣50指數</b>\n   {date_fmt} · 價格: {idx} · 報酬: {total}")
            _debug(f"台灣50: {idx}")

    # ── 3. 加權指數歷史（MI_5MINS_HIST）─────────────────
    data3 = twse_get("/indicesReport/MI_5MINS_HIST")
    if data3:
        for item in data3:
            open_  = item.get("OpeningIndex", "-")
            high   = item.get("HighestIndex", "-")
            low    = item.get("LowestIndex", "-")
            close_ = item.get("ClosingIndex", "-")
            date_fmt = _fmt_date(item.get("Date", ""))
            parts.append(
                f"📈 <b>加權指數走勢</b>\n"
                f"   {date_fmt} · 開: {open_} · 高: {high} · 低: {low} · 收: {close_}"
            )
            _debug(f"加權歷史: open={open_} close={close_}")

    if not parts:
        return ""

    msg = f"【大盤收盤】\n\n" + "\n\n".join(parts)
    send_telegram(msg)
    return msg

# ─── CLI 入口 ──────────────────────────────────────────
MODES = {
    "--check-messages":  ("重大訊息",      check_major_news),
    "--check-dividend":  ("除權除息預告",  check_dividends),
    "--check-valuation": ("殖利率/本益比", check_valuation),
    "--check-price":     ("個股日成交",    check_daily_price),
    "--check-threshold": ("股價閾值監控",  check_price_threshold),
    "--check-alert":     ("注意/處置股票", check_alerts),
    "--check-insider":   ("董監事持股",    check_insider),
    "--check-revenue":   ("月營收/EPS",   check_revenue),
    "--check-governance":("公司治理/ESG", check_governance),
    "--check-realtime":  ("盤中即時報價",  check_realtime),
    "--check-bfp":       ("四大買賣點",    check_best_four_point),
    "--check-market":    ("大盤統計",      check_market),
    "--daily":          ("每日總檢查",    None),
}

HELP_TEXT = """TWSE Monitor — 台灣證券交易所開放資料監控

【監控模式】
  python3 twse_monitor.py --daily                         # 每日完整總檢查
  python3 twse_monitor.py --check-messages               # 單一模組
  python3 twse_monitor.py --check-messages --check-market # 多模組同時跑
  python3 twse_monitor.py --check-price --check-threshold # 可任意組合
  python3 twse_monitor.py --debug --check-threshold      # debug 模式（寫 log）

【管理模式】
  python3 twse_monitor.py --cost 2330 2150               # 設定持有成本
  python3 twse_monitor.py --show-db                      # 顯示 DB 所有表
  python3 twse_monitor.py --show-db --table stocks       # 只看 stocks
  python3 twse_monitor.py --show-config                  # 顯示設定檔

【可用監控參數】（可同時指定多個）
  --check-messages    重大訊息（盤後掃描）
  --check-dividend    除權除息預告
  --check-valuation   殖利率 / 本益比 / 股價淨值比（僅變動時通知）
  --check-price       個股日成交行情（每日首次執行才通知）
  --check-threshold   股價閾值監控（漲跌停 / 價格 / 百分比）
  --check-alert       注意股票 / 處置股票警示
  --check-market      大盤加權指數收盤行情
  --daily             一次跑全部模組（不含 price/threshold）

【管理參數】
  --cost CODE VALUE   設定持有成本，例：--cost 0050 88.5
  --show-db           顯示 DB 內容（可用 --table 指定表）
  --table stocks|seen_items  搭配 --show-db 使用
  --show-config       顯示設定檔內容

【Debug 模式】
  --debug             開啟除錯，寫入 /tmp/twse_monitor.log

【閾值格式】
  2400        → 絕對價格
  \\"+10\\"       → close + 10
  \\"-10\\"       → close - 10
  \\"+5%\\"       → close × 1.05
  \\"-5%\\"       → close × 0.95
  \\"90%\\"       → close × 0.90
  （不填 → 動態預設：max=close+10, min=close-10, pct_up/down=5%）
"""

def cmd_set_cost(code: str, value: float):
    """設定持有成本"""
    conn = _db_conn()
    row = conn.execute("SELECT name, close_today FROM stocks WHERE code=?", (code,)).fetchone()
    if row:
        name, close = row[0], row[1]
        conn.execute("UPDATE stocks SET cost=? WHERE code=?", (value, code))
    else:
        name = code
        close = None
        conn.execute("INSERT INTO stocks (code,name,cost,close_today,close_prev,updated_ts) VALUES (?,?,?,?,?,datetime('now'))",
                     (code, name, value, None, None))
    conn.commit()
    conn.close()
    _debug(f"設定成本: {code} cost={value}")

    # 格式化輸出
    print(f"\n✅ 持有成本已更新")
    print(f"   股票：{code} {name}")
    print(f"   成本：{value:,.2f}")
    if close and close > 0:
        pnl = close - value
        pnl_pct = pnl / value * 100 if value > 0 else 0
        emoji = "📈" if pnl >= 0 else "📉"
        print(f"   現價：{close:,.2f}（close_today）")
        print(f"   未實現損益：{emoji} {pnl:+,.2f}（{pnl_pct:+.2f}%）")
    else:
        print(f"   現價：尚無收盤資料")

def cmd_show_db(table: str = None):
    """格式化顯示 DB 內容"""
    conn = _db_conn()

    tables_to_show = [table] if table else ["stocks", "seen_items"]
    for tbl in tables_to_show:
        if tbl == "stocks":
            rows = conn.execute(
                "SELECT code, name, cost, close_today, close_prev, updated_ts FROM stocks ORDER BY code"
            ).fetchall()
            if not rows:
                print(f"\n📊 stocks 表：無資料")
                continue
            print(f"\n📊 stocks 表（{len(rows)} 筆）")
            print(f"{'代碼':<8} {'名稱':<16} {'成本':>10} {'今日收盤':>10} {'昨日收盤':>10} {'未實現損益':>14} {'更新時間':<20}")
            print(f"{'─'*8} {'─'*16} {'─'*10} {'─'*10} {'─'*10} {'─'*14} {'─'*20}")
            for r in rows:
                code, name, cost, today, prev, ts = r
                cost_s = f"{cost:,.2f}" if cost else "-"
                today_s = f"{today:,.2f}" if today else "-"
                prev_s = f"{prev:,.2f}" if prev else "-"
                pnl_s = "-"
                if cost and today and cost > 0:
                    pnl = today - cost
                    pnl_pct = pnl / cost * 100
                    emoji = "📈" if pnl >= 0 else "📉"
                    pnl_s = f"{emoji}{pnl:+,.0f}({pnl_pct:+.1f}%)"
                ts_s = ts[:16] if ts else "-"
                print(f"{code:<8} {name:<16} {cost_s:>10} {today_s:>10} {prev_s:>10} {pnl_s:>14} {ts_s:<20}")

        elif tbl == "seen_items":
            rows = conn.execute(
                "SELECT category, item_key, message, ts FROM seen_items ORDER BY ts DESC LIMIT 30"
            ).fetchall()
            if not rows:
                print(f"\n📝 seen_items 表：無資料")
                continue
            print(f"\n📝 seen_items 表（最近 {len(rows)} 筆）")
            print(f"{'類別':<14} {'識別鍵':<42} {'內容摘要':<30} {'時間':<20}")
            print(f"{'─'*14} {'─'*42} {'─'*30} {'─'*20}")
            for r in rows:
                cat, key, msg, ts = r
                msg_s = (msg[:28] + "..") if msg and len(msg) > 30 else (msg or "-")
                ts_s = ts[:16] if ts else "-"
                print(f"{cat:<14} {key:<42} {msg_s:<30} {ts_s:<20}")
        else:
            print(f"❌ 未知的表：{tbl}（可用：stocks, seen_items）")

    # 統計
    print(f"\n📊 DB 檔案：{DB_PATH}")
    for tbl in ["stocks", "seen_items"]:
        cnt = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        print(f"   {tbl}: {cnt} 筆")
    conn.close()

def cmd_show_config():
    """格式化顯示設定檔"""
    if not os.path.exists(CONFIG_PATH):
        print(f"❌ 設定檔不存在：{CONFIG_PATH}")
        return

    with open(CONFIG_PATH) as f:
        cfg = json.load(f)

    print(f"\n📋 設定檔：{CONFIG_PATH}")

    # watchlist
    wl = cfg.get("watchlist", [])
    print(f"\n🔍 關注清單（{len(wl)} 檔）")
    print(f"   {', '.join(wl)}")

    # thresholds
    thresholds = cfg.get("thresholds", {})
    if thresholds:
        print(f"\n⚙️ 閾值設定（{len(thresholds)} 檔）")
        print(f"{'代碼':<8} {'max_price':>10} {'min_price':>10} {'max_pct_up':>10} {'max_pct_down':>12} {'漲停':>4} {'跌停':>4} {'幅度':>4}")
        print(f"{'─'*8} {'─'*10} {'─'*10} {'─'*10} {'─'*12} {'─'*4} {'─'*4} {'─'*4}")
        for code, t in thresholds.items():
            mx = str(t.get('max_price', '-'))
            mn = str(t.get('min_price', '-'))
            pu = str(t.get('max_pct_up', '-'))
            pd = str(t.get('max_pct_down', '-'))
            cu = '✅' if t.get('circuit_up', True) else '❌'
            cd = '✅' if t.get('circuit_down', True) else '❌'
            cp = str(t.get('circuit_pct', '-'))
            print(f"{code:<8} {mx:>10} {mn:>10} {pu:>10} {pd:>12} {cu:>4} {cd:>4} {cp:>4}")

    # telegram
    token = cfg.get('telegram_bot_token', '')
    chat_id = cfg.get('telegram_chat_id', '')
    token_masked = token[:8] + '...' + token[-4:] if len(token) > 12 else '***'
    print(f"\n📱 Telegram")
    print(f"   Bot Token: {token_masked}")
    print(f"   Chat ID:   {chat_id}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="TWSE Monitor — 台灣證券交易所開放資料監控",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=HELP_TEXT
    )
    parser.add_argument("--debug", action="store_true", help="開啟除錯模式")
    parser.add_argument("--cost", nargs=2, metavar=("CODE", "VALUE"), help="設定持有成本，例：--cost 2330 2150")
    parser.add_argument("--show-db", action="store_true", help="顯示 DB 內容")
    parser.add_argument("--table", type=str, choices=["stocks", "seen_items"], help="指定顯示的表")
    parser.add_argument("--show-config", action="store_true", help="顯示設定檔內容")
    for m in MODES:
        parser.add_argument(m, action="store_true")
    args = parser.parse_args()

    DEBUG_MODE = args.debug
    if DEBUG_MODE:
        open(LOG_PATH, "w").close()
        _debug("=== Debug 模式啟動 ===")

    # ── 管理指令（不跑監控）─────────────────────────────
    if args.cost:
        code, val = args.cost
        try:
            val_f = float(val)
        except ValueError:
            print(f"❌ 成本必須是數字：{val}")
            sys.exit(1)
        cmd_set_cost(code, val_f)
        sys.exit(0)

    if args.show_db:
        cmd_show_db(args.table)
        sys.exit(0)

    if args.show_config:
        cmd_show_config()
        sys.exit(0)

    # ── 監控模式 ─────────────────────────────────────────
    def safe_run(fn, label):
        try:
            return fn() or ""
        except Exception as e:
            err = f"【{label}】執行錯誤: {e}"
            print(err, file=sys.stderr)
            _debug(err)
            send_telegram(f"⚠️ {err}", urgent=True)
            return err

    active = {
        k: v for k, v in MODES.items()
        if getattr(args, k.lstrip("-").replace("-", "_"), False)
    }

    if "--daily" in active:
        active = {k: v for k, v in MODES.items()
                   if k not in ("--daily", "--check-price", "--check-threshold")}

    if not active:
        parser.print_help()
        sys.exit(0)

    for flag, (label, fn) in active.items():
        if fn is None:
            continue
        result = safe_run(fn, label)
        status = "完成" if result else "無新資料"
        print(f"[{label}] {status}")

    for flag in ["--check-price", "--check-threshold"]:
        key = flag.lstrip("-").replace("-", "_")
        if getattr(args, key, False):
            fn = MODES[flag][1]
            result = safe_run(fn, MODES[flag][0])
            status = "完成" if result else "無新資料"
            print(f"[{MODES[flag][0]}] {status}")

    if DEBUG_MODE:
        _debug("=== Debug 模式結束 ===")
        print(f"\n📋 Debug log: {LOG_PATH}")
