---
name: clw-gold-monitor-pro
version: 3.0.0
description: "多金屬價格監控系統 v3。台銀黃金存摺 + 國際金屬現貨（黃金/白銀/鉑金），快取比對 + 交叉驗證，Telegram 告警。"
metadata:
  emoji: "🥇"
  last_update: "2026-05-11"
---

# clw-gold-monitor-pro — 多金屬價格監控系統

## v3.0.0（2026-05-11）

架構重構：拆分為 `gold_local_monitor.py`（台銀）+ `gold_intl_monitor.py`（國際現貨），快取比對取代 SQLite。

- ✅ 移除 SQLite 依賴，改用 JSON 快取（`/tmp/`）
- ✅ 台銀監控新增玉山銀行交叉驗證
- ✅ 國際金屬支援 Yahoo Finance + Alpha Vantage fallback
- ✅ 配置檔遷移至 `~/.gold_monitor_pro_config.json`

## 📊 架構

| 腳本 | 監控對象 | 資料來源 | 快取 TTL |
|------|----------|----------|----------|
| `gold_local_monitor.py` | 台銀黃金存摺（賣出/買進） | 台銀 day page + 玉山銀行（交叉驗證） | 10 分鐘 |
| `gold_intl_monitor.py` | 國際黃金/白銀/鉑金現貨 | Yahoo Finance → Alpha Vantage fallback | 60 分鐘 |

## 📦 依賴

- Python 3.9+
- Playwright（台銀 adapter）
- `~/scripts/data_adapters/`（data adapter 模組）

## 🛠️ 使用方式

```bash
# 台銀黃金檢查
python3 $SCRIPT_PATH/gold_local_monitor.py --check

# 國際金屬檢查
python3 $SCRIPT_PATH/gold_intl_monitor.py --check
```

## ⏰ 排程

```cron
# 價格監控（每 10 分鐘，週一至五 09:00-21:00）
*/10 9-21 * * 1-5 python3 $SCRIPT_PATH/gold_local_monitor.py --check
*/10 9-21 * * 1-5 python3 $SCRIPT_PATH/gold_intl_monitor.py --check
```

## 📁 相關檔案

| 檔案 | 說明 |
|------|------|
| `$SCRIPT_PATH/gold_local_monitor.py` | 台銀黃金監控 |
| `$SCRIPT_PATH/gold_intl_monitor.py` | 國際金屬監控 |
| `$SCRIPT_PATH/data_adapters/` | 數據適配器 |
| `~/.gold_monitor_pro_config.json` | 配置檔（閾值、Telegram、告警通道） |
| `/tmp/gold_monitor_local_baseline.json` | 台銀快取（自動清理 7 天） |
| `/tmp/gold_monitor_intl_*.json` | 國際金屬快取（自動清理 7 天） |

## ⚙️ 配置檔格式

`~/.gold_monitor_pro_config.json`：

```json
{
  "thresholds": {
    "gold_local": 50,
    "gold_intl": 15,
    "silver_intl": 5,
    "platinum_intl": 100
  },
  "channels": {
    "telegram": {
      "enabled": true,
      "bot_token": "YOUR_BOT_TOKEN",
      "chat_id": "YOUR_CHAT_ID"
    }
  }
}
```
