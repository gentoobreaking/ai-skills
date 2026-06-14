# clw-ideas2tasks

將臨時想法自動分類、拆解為敏捷專案任務。

## 🌟 核心功能

- **想法轉任務**：掃描 `Ideas/` 目錄下的 `.txt` 檔案，自動分類、分配成員並建立 `T*.md` 任務檔。
- **雙向狀態同步**：確保 `Tasks/` 目錄（事實來源）與 Idea 檔案之間的狀態一致。
- **GitHub 整合**：自動將本地任務同步至 GitHub Issues 與 Project Board，支援雙向拉回/推送。
- **多維儀表板**：生成全專案進度概覽（`PROJECTS.md`）與今日動態摘要（`DAILY.md`）。
- **效能分析**：提供速度指標、週期時間統計、燃盡圖趨勢。
- **配置管理**：支援 `.env` 檔案 + 環境變數覆蓋。
- **單元測試**：24 個測試確保狀態解析穩定性。

## 🚀 快速開始

### 1. 環境變數配置
在 `~/.zshrc` 或 `~/.bash_profile` 中加入：
```bash
export IDEAS2TASKS_TASKS_DIR="~/Tasks"
export IDEAS2TASKS_IDEAS_DIR="~/Ideas"
```

### 2. 常用指令

#### 建立 Idea（快速輸入）
```bash
python3 scripts/clw_idea.py "今天突然想做個語音助手"
python3 scripts/clw_idea.py "優化登入流程" --desc "檢查 OAuth"
```

#### 建立任務
```bash
python3 scripts/executor.py --github    # 掃描 Idea 並同步至 GitHub
```

#### GitHub 同步與清理
```bash
python3 scripts/executor.py --sync-github     # 補建缺漏的 GitHub Issue
python3 scripts/executor.py --cleanup-github  # 關閉已完成/跳過任務的 Issue
python3 scripts/executor.py --pull-github     # 從 GitHub 拉回狀態
```

#### 更新儀表板
```bash
python3 scripts/update_projects.py   # 更新 PROJECTS.md（含效能分析）
python3 scripts/update_daily.py      # 更新 DAILY.md
```

#### 執行測試
```bash
python3 -m pytest tests/ -v           # 執行單元測試
```

## 📁 腳本一覽 (scripts/)

| 腳本 | 用途 |
|------|------|
| `clw_idea.py` | 快速建立 Idea 檔的 CLI 工具 |
| `executor.py` | 核心工具：任務建立、GitHub 同步、Issue 清理 |
| `update_projects.py` | 生成 `PROJECTS.md` 專案進度儀表板 |
| `update_daily.py` | 生成 `DAILY.md` 每日任務摘要 |
| `state_sync.py` | 狀態解析核心：Frontmatter 讀取、Status 標準化 |
| `lifecycle.py` | 定時掃描：歸檔已處理 Idea 並發送 Telegram 通知 |
| `migrate_readme.py` | 自動更新各專案的 `README.md` 進度表 |
| `config.py` | 配置管理：.env 檔案 + 環境變數覆蓋 |
| `stats.py` | 效能分析：速度、洞察、燃盡圖 |

## 🛠️ 技術細節

- **Frontmatter 解析**：支援強健的 Markdown 標記解析（如 `- **Status**: done`）。
- **進度計算**：自動排除 `skip`（跳過）任務，提供更真實的完成率。
- **GitHub 整合**：使用 `gh` CLI 進行 Issue 操作與 Project V2 Board 關聯。
- **多策略匹配**：GitHub 同步支援 key 完全匹配 → title 匹配 → 相似度比對。
- **任務依賴管理**：支援 `blocked_by: T001` 或 `blocked_by: [T001, T005]` 欄位，儀表板自動顯示阻擋狀態（⏳）。
- **LLM 上下文感知**：`classify.py` 自動讀取 PROJECTS.md 上下文，幫助 LLM 識別現有專案而非建立重複專案。

---
_Last Update: 2026-05-12 v3.1.0_
