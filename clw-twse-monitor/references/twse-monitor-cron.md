# TWSE Monitor — Cron Job 配置指南（v2）

## 概覽

TWSE Monitor v2 共 **7 個 Cron Job**，依盤前/盤中/盤後/定期分類：

| # | Job 名稱 | Schedule | 指令 | 說明 |
|---|----------|----------|------|------|
| 1 | twse-realtime | 每 10 分鐘 09-13:30 | `--check-realtime` | **盤中即時報價 + 閾值** |
| 2 | twse-daily | 每日 17:30 | `--daily` | 盤後總檢查（8 模組） |
| 3 | twse-price | 每日 14:00 | `--check-price --check-threshold --check-bfp` | 收盤行情 + 閾值 + BFP |
| 4 | twse-alert | 每小時 09-16 | `--check-alert` | 注意/處置/變更交易/暫停交易 |
| 5 | twse-insider | 每日 09:00 | `--check-insider` | 開盤前董監事資訊 |
| 6 | twse-revenue | 每月 5-15 日 09:00 | `--check-revenue` | 月營收公告高峰期 |
| 7 | twse-governance | 每週一 09:00 | `--check-governance` | 公司治理/ESG 週檢 |

> **v2 新增**：`twse-realtime`（盤中即時）和 BFP（整合進 `twse-price`）。

---

## 方式一：OpenClaw Cron Job（推薦）

### 配置原則

- **Payload**：全部使用 `systemEvent`（純指令執行，零 AI inference，最省 token）
- **Session**：`sessionTarget: "main"`（復用 main session context）
- **sessionKey**：統一格式 `agent:main:cron:twse-{slug}`
- **通知**：腳本內 `send_telegram()` 自幹，不靠 delivery
- **錯誤處理**：腳本內 `send_telegram(urgent=True)` 報錯

### Job 1：twse-realtime（盤中即時）【v2】

**Schedule**：每 10 分鐘 09:00-13:30（週一至五）

```json
{
  "name": "twse-realtime",
  "schedule": {
    "kind": "cron",
    "expr": "*/10 9-13 * * 1-5",
    "tz": "Asia/Taipei"
  },
  "sessionTarget": "main",
  "sessionKey": "agent:main:cron:twse-realtime",
  "payload": {
    "kind": "systemEvent",
    "text": "python3 /Users/claw/scripts/twse_monitor_v2.py --check-realtime"
  },
  "enabled": true
}
```

### Job 2：twse-daily（盤後總檢查）

**Schedule**：每日 17:30（週一至五）

```json
{
  "name": "twse-daily",
  "schedule": {
    "kind": "cron",
    "expr": "30 17 * * 1-5",
    "tz": "Asia/Taipei"
  },
  "sessionTarget": "main",
  "sessionKey": "agent:main:cron:twse-daily",
  "payload": {
    "kind": "systemEvent",
    "text": "python3 /Users/claw/scripts/twse_monitor_v2.py --daily"
  },
  "enabled": true
}
```

### Job 3：twse-price（收盤行情 + 閾值 + BFP）【v2】

**Schedule**：每日 14:00（週一至五）

```json
{
  "name": "twse-price",
  "schedule": {
    "kind": "cron",
    "expr": "0 14 * * 1-5",
    "tz": "Asia/Taipei"
  },
  "sessionTarget": "main",
  "sessionKey": "agent:main:cron:twse-price",
  "payload": {
    "kind": "systemEvent",
    "text": "python3 /Users/claw/scripts/twse_monitor_v2.py --check-price --check-threshold --check-bfp"
  },
  "enabled": true
}
```

> BFP 需要至少 6 天歷史行情才能正常運作。初次啟用後需等待 6 個交易日才有訊號。

### Job 4：twse-alert（即時警示）

**Schedule**：每小時 09:00-16:00（週一至五）

```json
{
  "name": "twse-alert",
  "schedule": {
    "kind": "cron",
    "expr": "0 9-16 * * 1-5",
    "tz": "Asia/Taipei"
  },
  "sessionTarget": "main",
  "sessionKey": "agent:main:cron:twse-alert",
  "payload": {
    "kind": "systemEvent",
    "text": "python3 /Users/claw/scripts/twse_monitor_v2.py --check-alert"
  },
  "enabled": true
}
```

### Job 5：twse-insider（董監事持股）

**Schedule**：每日 09:00（週一至五）

```json
{
  "name": "twse-insider",
  "schedule": {
    "kind": "cron",
    "expr": "0 9 * * 1-5",
    "tz": "Asia/Taipei"
  },
  "sessionTarget": "main",
  "sessionKey": "agent:main:cron:twse-insider",
  "payload": {
    "kind": "systemEvent",
    "text": "python3 /Users/claw/scripts/twse_monitor_v2.py --check-insider"
  },
  "enabled": true
}
```

> ⚠️ `t187ap11_L`（董監事持股餘額）有 27,000+ 筆，首次執行會全量通知。之後只推新變動。

### Job 6：twse-revenue（月營收高峰期）

**Schedule**：每月 5-15 日 09:00

```json
{
  "name": "twse-revenue",
  "schedule": {
    "kind": "cron",
    "expr": "0 9 5-15 * *",
    "tz": "Asia/Taipei"
  },
  "sessionTarget": "main",
  "sessionKey": "agent:main:cron:twse-revenue",
  "payload": {
    "kind": "systemEvent",
    "text": "python3 /Users/claw/scripts/twse_monitor_v2.py --check-revenue"
  },
  "enabled": true
}
```

### Job 7：twse-governance（公司治理/ESG 週檢）

**Schedule**：每週一 09:00

```json
{
  "name": "twse-governance",
  "schedule": {
    "kind": "cron",
    "expr": "0 9 * * 1",
    "tz": "Asia/Taipei"
  },
  "sessionTarget": "main",
  "sessionKey": "agent:main:cron:twse-governance",
  "payload": {
    "kind": "systemEvent",
    "text": "python3 /Users/claw/scripts/twse_monitor_v2.py --check-governance"
  },
  "enabled": true
}
```

### OpenClaw 驗證指令

```bash
# 列出所有 jobs
cron list

# 手動觸發單一 job
cron run --jobId <jobId>

# 查看執行歷史
cron runs --jobId <jobId>
```

---

## 方式二：系統 crontab（輕量替代）

### 設定方式

```bash
crontab -e
```

```crontab
# ── TWSE Monitor v2 ──────────────────────────────────
# Job 1: 盤中即時報價（週一至五 09-13:30 每 10 分鐘）【v2】
*/10 9-13 * * 1-5 /usr/bin/python3 /Users/claw/scripts/twse_monitor_v2.py --check-realtime >> /tmp/twse_cron.log 2>&1

# Job 2: 盤後總檢查（週一至五 17:30）
30 17 * * 1-5 /usr/bin/python3 /Users/claw/scripts/twse_monitor_v2.py --daily >> /tmp/twse_cron.log 2>&1

# Job 3: 收盤行情 + 閾值 + BFP（週一至五 14:00）【v2】
0 14 * * 1-5 /usr/bin/python3 /Users/claw/scripts/twse_monitor_v2.py --check-price --check-threshold --check-bfp >> /tmp/twse_cron.log 2>&1

# Job 4: 即時警示（週一至五 09-16 每小時）
0 9-16 * * 1-5 /usr/bin/python3 /Users/claw/scripts/twse_monitor_v2.py --check-alert >> /tmp/twse_cron.log 2>&1

# Job 5: 董監事持股（週一至五 09:00）
0 9 * * 1-5 /usr/bin/python3 /Users/claw/scripts/twse_monitor_v2.py --check-insider >> /tmp/twse_cron.log 2>&1

# Job 6: 月營收高峰期（每月 5-15 日 09:00）
0 9 5-15 * * /usr/bin/python3 /Users/claw/scripts/twse_monitor_v2.py --check-revenue >> /tmp/twse_cron.log 2>&1

# Job 7: 公司治理/ESG 週檢（每週一 09:00）
0 9 * * 1 /usr/bin/python3 /Users/claw/scripts/twse_monitor_v2.py --check-governance >> /tmp/twse_cron.log 2>&1
```

### crontab 注意事項

1. **Python 路徑**：crontab 環境變數與終端不同，建議用絕對路徑 `/usr/bin/python3`。若用 Homebrew Python，改為 `/opt/homebrew/bin/python3`。
2. **PATH 問題**：crontab 預設 PATH 很少，若腳本依賴其他工具，在 crontab 頂部加：
   ```crontab
   PATH=/usr/local/bin:/usr/bin:/bin
   ```
3. **Log 位置**：`/tmp/twse_cron.log`，重開機後會清空。若需持久化，改為 `~/twse_cron.log`。
4. **macOS 權限**：首次設定後，系統偏好設定 → 隱私與安全 → 完全磁碟存取權限 → 加入 `/usr/sbin/cron`。

### crontab 驗證指令

```bash
crontab -l                    # 查看目前 crontab
tail -f /tmp/twse_cron.log    # 即時看 log
/usr/bin/python3 /Users/claw/scripts/twse_monitor_v2.py --check-realtime  # 測試即時
/usr/bin/python3 /Users/claw/scripts/twse_monitor_v2.py --check-bfp       # 測試 BFP
```

---

## Schedule 語法速查

| Cron Expr | 意義 |
|-----------|------|
| `*/10 9-13 * * 1-5` | 週一至五 09:00-13:30 每 10 分鐘 |
| `30 17 * * 1-5` | 週一至五 17:30 |
| `0 14 * * 1-5` | 週一至五 14:00 |
| `0 9-16 * * 1-5` | 週一至五 09:00-16:00 每小時 |
| `0 9 5-15 * *` | 每月 5-15 日 09:00 |
| `0 9 * * 1` | 每週一 09:00 |

---

## 各時間點執行分布（無重疊）

| 時間 | 跑的 Job | API 負擔 |
|------|---------|---------|
| 每 10 分鐘（09-13:30） | `twse-realtime`（3 calls，間隔 1s） | 輕 |
| 14:00 | `twse-price`（一次跑完 price + threshold + BFP） | 中 |
| 17:30 | `twse-daily`（8 模組，~8 calls） | 重（但一次完成） |
| 每小時（09-16） | `twse-alert`（1 call） | 輕 |
| 每日 09:00 | `twse-insider`（2 calls） | 中 |
| 每月 5-15 日 09:00 | `twse-revenue`（3 calls） | 中 |
| 每週一 09:00 | `twse-governance`（6 calls） | 中 |

**無同時重疊的 Job**。14:00 的 `twse-price` 把 price + threshold + BFP 合併成一次執行，共享同一批 OHLCV 資料，無多餘 API call。

---

## 兩種方式對比

| 項目 | OpenClaw Cron | 系統 crontab |
|------|--------------|-------------|
| 管理 | Web UI + CLI | `crontab -e` |
| 執行歷史 | `cron runs` | 看 log 檔 |
| 手動觸發 | `cron run` | 手動執行指令 |
| 錯誤通知 | 腳本自幹 Telegram | 腳本自幹 Telegram + log |
| 依賴 | OpenClaw Gateway | 無 |
| 適用場景 | 長期正式運行 | 備案 / 獨立部署 |
| Token 消耗 | systemEvent = 0 | 不經過 AI = 0 |

---

## v1 與 v2 腳本對照

| 項目 | v1 | v2 |
|------|----|----|
| 腳本 | `twse_monitor.py` | `twse_monitor_v2.py` |
| 即時報價 | ❌ | ✅ `--check-realtime` |
| 四大買賣點 | ❌ | ✅ `--check-bfp`（整合進 `twse-price`） |
| Cron Job 數量 | 6 個 | 7 個 |
| 設定檔格式 | 相容 | 相容（新增 `realtime_enabled`、`bfp_enabled`） |
| 依賴 | 零 | 零（純標準庫） |

> 兩版腳本使用同一設定檔 `~/.twse_monitor_config.json`，v1 忽略新欄位，v2 完全支援。
