---
name: ideas2tasks
description: |
  將臨時想法自動分類、拆解為敏捷專案任務。
  觸發條件：用戶提到「idea轉task」「ideas2tasks」「想法拆分」「專案規劃」「task管理」,
  或要求掃描 Ideas 目錄、建立專案任務、分配團隊成員。
metadata:
  emoji: "📋"
  version: "3.0.0"
  last_update: "2026-05-11"
---

# ideas2tasks — 想法轉敏捷任務

## v3.0.0 重構紀錄（2026-05-12 更新）

**變更摘要：**
- ✅ **儀表板整合**：將 `update_projects.py` 與 `update_daily.py` 移入 Skill 系統並重構。
- ✅ **模組化優化**：腳本全面改用 `state_sync.py` 進行狀態解析與路徑配置，消除重複代碼。
- ✅ **GitHub 清理功能**：`executor.py` 新增 `--cleanup-github` 模式，自動關閉已完成任務的 Issue。
- ✅ **強健解析**：優化 Frontmatter 解析器，支援 Markdown 標記（`-`, `**`）與行內註解。
- ✅ **完成率優化**：進度計算邏輯自動排除 `skip` 任務。
- ✅ executor.py 預設模式改為直接掃 Ideas/（不再依賴 lifecycle_status.json）。
- ✅ executor.py 建立 task 時使用 task-template.md。
- ✅ 移除 lifecycle_status.json 依賴（全系統零引用）。

### v3.1.0 功能新增（2026-05-12）
- ✅ **GitHub 雙向同步**：`executor.py` 新增 `--pull-github` 從 GitHub 拉回本地、`--reverse-only` 只推送本地完成狀態
- ✅ **效能分析儀表板**：`stats.py` 提供速度與洞察分析，顯示燃盡圖與週期時間
- ✅ **配置管理**：支援 `.env` 檔案（`config.py`）+ 環境變數覆蓋 + 預設值
- ✅ **單元測試**：`tests/test_state_sync.py` 提供 24 個測試確保狀態解析穩定性

**crontab 排程（系統 crontab）：**
```cron
30 8 * * 1-5 python3 /path/to/executor.py --github          # 掃 Ideas/ + 建 tasks + 同步 GitHub
0  *  *  *  *  python3 /path/to/executor.py --sync-github      # 全域掃 T*.md 補建缺漏 Issue
0  9  *  *  *  python3 /path/to/lifecycle.py --telegram        # 掃描通知
```

---

# 📋 使用前準備

## 0. 路徑設定（必要）

腳本透過環境變數或 `.env` 檔案取得目錄路徑：

**方式一：環境變數（推薦）**
```bash
export IDEAS2TASKS_TASKS_DIR="~/Tasks"
export IDEAS2TASKS_IDEAS_DIR="~/Ideas"
```
建議加入 shell 設定檔（如 `~/.zshrc`）永久生效。

**方式二：.env 檔案（v3.1.0 新增）**
在 Skill 目錄下建立 `.env` 檔案：
```bash
IDEAS2TASKS_TASKS_DIR=~/Tasks
IDEAS2TASKS_IDEAS_DIR=~/Ideas
```
優先順序：環境變數 > .env 檔案 > 預設值。

## 1. Telegram 通知（可選）

需設定環境變數（僅 `--telegram` 模式會讀取，未設定不影響主流程）：
```bash
export TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN"
export TELEGRAM_CHAT_ID="YOUR_CHAT_ID"
```

## 2. GitHub CLI（可選）

如需同步 GitHub Issues + Board：
```bash
brew install gh && gh auth login
```
必要權限：`repo`、`read:project`

### 3. 建立 Idea 的便捷方式（v3.1.0 新增）

快速建立 Idea 檔案：
```bash
python3 scripts/clw_idea.py "今天突然想做個語音助手"
python3 scripts/clw_idea.py "優化登入流程" --desc "檢查 OAuth"
python3 scripts/clw_idea.py "新功能" --open    # 建立後用編輯器開啟
```

可設為 shell alias：
```bash
alias clw-idea='python3 /path/to/skills/clw-ideas2tasks/scripts/clw_idea.py'
```

---

# 📂 目錄結構

```
$IDEAS2TASKS_IDEAS_DIR/           # 臨時想法存放區
  ├── *.txt                        # 待處理的 idea 檔案
  └── _done/                       # 已處理歸檔區（自動移入）

$IDEAS2TASKS_TASKS_DIR/           # 專案任務區
  └── <project-name>/
      ├── README.md                # 專案概覽（自動生成）
      └── tasks/
          ├── T001.md
          ├── T002.md
          └── ...
```

## 👥 團隊成員

| 角色 | 名稱 | OpenClaw Agent ID |
|------|------|-------------------|
| Planner | 豪（用戶本人） | `main` |
| Coder 1 | 碼農 1 號 | `agent-coder1` |
| Coder 2 | 碼農 2 號 | `agent-coder2` |
| DocWriter | 安安 | `agent-ann` |
| Reviewer | 樂樂 | `agent-lele` |
| Researcher | 研研 | `agent-researcher` |

---

# 🔄 完整邏輯流程

```
╔══════════════════════════════════════════════════════════════════════════════════╗
║                         clw-ideas2tasks 系統邏輯流程圖                        ║
╚══════════════════════════════════════════════════════════════════════════════════╝


┌──────────────────────────────────────────────────────────────────────────────────────┐
│                              📥 輸入層（資料來源）                               │
├──────────────────────────────────────────────────────────────────────────────────────┤
│  ~/Ideas/                  ~/Tasks/                    GitHub                    │
│  *.txt（創意檔）            */tasks/T*.md（任務檔）       openclaw-tasks repo      │
│  ├─ task.1 / task.2 /...   ├─ T001.md, T002.md,...     ├─ Issues (#1～302)       │
│  ├─ project name          ├─ project README.md        └─ Project Board          │
│  └─ _done/（已歸檔）       └─ PROJECTS.md, DAILY.md         (PVT_kwH...)          │
└──────────────────────────────────────────────────────────────────────────────────────┘
           │                        │                        ▲
           │                        │                        │
           ▼                        ▼                        │
┌──────────────────────────────────────────────────────────────────────────────────┐
│                              🔧 共享模組                                         │
├──────────────────────────────────────────────────────────────────────────────────┤
│                              state_sync.py                                        │
│  ┌────────────────────────────────────────────────────────────────────────────┐   │
│  │ TASKS_DIR / IDEAS_DIR（環境變數控制）                                        │   │
│  │ read_task_status()  write_task_status()   read_task_title()              │   │
│  │ get_tasks_dir_status()   scan_tasks_dir()                                 │   │
│  │ merge_classify_with_tasks_status()  should_skip_task()                  │   │
│  │ sync_idea_to_task_done()   on_task_done()   normalize_all_task_statuses()│   │
│  └────────────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────────┘
           │                        │
           ▼                        ▼
┌────────────────────────────┐  ┌──────────────────────────────┐
│      scan.py               │  │      classify.py              │
│  scan_ideas()              │  │  classify_idea()              │
│  掃 *.txt → list[dict]     │  │  解析 → 拆任務 → 指派成員      │
└────────────────────────────┘  └──────────────────────────────┘
           │                        │
           └────────┬───────────────┘
                    ▼
           ┌──────────────────────────────┐
           │  executor.py（主入口）         │
           │  create_tasks_from_ideas()    │
           │  1. scan_ideas()             │
           │  2. classify_idea()          │
           │  3. should_skip_task() ──→ 去重檢查（TASKS_DIR/*/tasks/）│
           │  4. 寫入 T*.md              │ ← templates/task-template.md
           │  5. 更新 project README.md  │
           └──────────────────────────────┘
                    │
                    ├──────────────────────────────────────────┐
                    ▼                                            ▼
┌──────────────────────────────┐    ┌────────────────────────────────────────────┐
│  lifecycle.py（每日 cron）    │    │  GitHub 同步模組（executor.py 內）          │
│  run_scan()                   │    │  sync_single_task_to_github()              │
│  run_classify()              │    │    ├─ gh issue create                      │
│  merge_classify_w_tasks()   │    │    └─ gh api addProjectV2ItemById          │
│  sync_idea_to_task_done()    │    │  sync_todos_to_github()                  │
│  archive_done_ideas()        │    │  cleanup_github_issues()                  │
│  scan_tasks_dir()            │    │  repair_github_issue_urls()               │
│  send_telegram()            │    │  sync_board() ← (2026-05-12 新增)         │
└──────────────────────────────┘    └────────────────────────────────────────────┘
                    │                           │
                    ▼                           ▼
           ┌───────────────┐         ┌────────────────────────────────┐
           │ executor_     │         │  executor_status.json           │
           │ status.json  │         └────────────────────────────────┘
           └───────────────┘
                    │
                    ▼
           ┌──────────────────────────────┐    ┌────────────────────────────────┐
           │  update_projects.py           │    │  update_daily.py                │
           │  → TASKS_DIR/PROJECTS.md     │    │  → TASKS_DIR/DAILY.md           │
           │  （專案儀表板）               │    │  （今日任務儀表板）              │
           └──────────────────────────────┘    └────────────────────────────────┘
                    │                           │
                    ▼                           ▼
           ┌──────────────────────────────┐    ┌────────────────────────────────┐
           │  stats.py                    │    │  migrate_readme.py              │
           │  generate_stats_report()     │    │  更新專案 README.md 任務列表     │
           │  calculate_velocity_stats() │    │  task_audit.py 稽核一致性       │
           └──────────────────────────────┘    └────────────────────────────────┘


╔══════════════════════════════════════════════════════════════════════════════════╗
║                            🚀 執行模式與指令流向                                 ║
╚══════════════════════════════════════════════════════════════════════════════════╝

┌─ executor.py ─────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│  # 預設模式：掃 Ideas → 建 Tasks                                                  │
│  python3 executor.py                                                           │
│     └─ create_tasks_from_ideas() → scan + classify + 去重 → 寫 T*.md              │
│                                                                                 │
│  # 建 Tasks + 同步 GitHub                                                        │
│  python3 executor.py --github                                                   │
│     └─ create_tasks_from_ideas() + sync_tasks_to_github()                       │
│                                                                                 │
│  # 只同步 GitHub（已有 T*.md，缺 Issue 的建 Issue）                                 │
│  python3 executor.py --sync-github                                              │
│     └─ sync_todos_to_github() → gh issue create                                 │
│                                                                                 │
│  # 清理：關閉 done/skip 的 GitHub Issue + 修補 URL                                 │
│  python3 executor.py --cleanup-github                                            │
│     └─ cleanup_github_issues() → gh issue close + 補 github_issue:              │
│                                                                                 │
│  # 修補錯誤共用的 URL                                                             │
│  python3 executor.py --repair-github                                             │
│     └─ repair_github_issue_urls() → 搜尋 + 建新 Issue + 更新 URL                  │
│                                                                                 │
│  # 同步 Project Board（補加入 Board）                                            │
│  python3 executor.py --sync-board                                               │
│     └─ sync_board() → gh api addProjectV2ItemById                               │
│                                                                                 │
│  # 統一 Status 格式                                                              │
│  python3 executor.py --normalize                                                │
│     └─ normalize_all_task_statuses()                                            │
└─────────────────────────────────────────────────────────────────────────────────┘


```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                         lifecycle.py 處理邏輯流程圖                            ║
╚═══════════════════════════════════════════════════════════════════════════════╝


╔═══════════════════════════════════════════════════════════════════════════════╗
║                            main() 入口                                       ║
╚═══════════════════════════════════════════════════════════════════════════════╝

              ┌────────────────────────────────────────┐
              │  python3 lifecycle.py [args]             │
              └──────────────────┬───────────────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
        ┌───────────┐    ┌─────────────┐   ┌────────────┐
        │ --telegram │    │ --json      │   │ (default)  │
        └─────┬─────┘    └──────┬──────┘   └─────┬──────┘
              │                │                │
              ▼                ▼                ▼
        build_telegram_  build_full_     build_telegram_
        summary()        summary()        summary()


╔═══════════════════════════════════════════════════════════════════════════════╗
║                    main() — 核心流程（5 步）                                   ║
╚═══════════════════════════════════════════════════════════════════════════════╝

  ┌─ Step 1：掃描 ideas ──────────────────────────────────────────────────────┐
  │  run_scan(ideas_dir)                                                       │
  │    └─→ scan_ideas()                                                       │
  │        └─→ Ideas/*.txt → [filename, content, project_hint, ...]           │
  └───────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
  ┌─ Step 2：分類 + 合併 Tasks/ 狀態 ──────────────────────────────────────┐
  │  run_classify(ideas) × N                                                 │
  │    └─→ 對每個 idea：                                                      │
  │            classify_idea(idea)                                            │
  │                  │                                                        │
  │                  └── merge_classify_with_tasks_status(classified)          │
  │                             │                                            │
  │                             └── TASKS_DIR/*/tasks/T*.md                  │
  │                                 read_task_status()                       │
  │                                 移除已 done/in-progress 的 tasks         │
  │                                 統計 pending_count                       │
  └───────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
  ┌─ Step 3：同步 Tasks/ done → idea 檔 done 標記 ─────────────────────────┐
  │  for each result:                                                         │
  │    sync_idea_to_task_done(project_name)                                  │
  │      └─→ 讀取 TASKS_DIR/{proj}/tasks/T*.md 的 Status                     │
  │          Task done → idea 檔中 task.N 標記 done                          │
  └───────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
  ┌─ Step 4：歸檔已完成 idea → _done/ ─────────────────────────────────────┐
  │  archive_done_ideas(results, ideas_dir, dry_run)                         │
  │    └─→ 遍歷每個 idea 的 tasks[]                                           │
  │              │                                                            │
  │              └── tasks[] 為空（all done）──→ shutil.move → _done/        │
  └───────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
  ┌─ Step 5：掃描 Tasks/（待處理追蹤的主要來源）─────────────────────────────┐
  │  scan_tasks_dir()                                                        │
  │    └─→ TASKS_DIR/*/tasks/T*.md                                          │
  │        read_task_status()                                                │
  │        回傳：[{project, pending_count, in_progress_count, tasks[], ...}] │
  └───────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
  ┌─ 分支輸出 ───────────────────────────────────────────────────────────────┐
  │                                                                          │
  │  IF --json:                                                              │
  │    → JSON 結構 {new_ideas, tasks_pending, tasks_in_progress,             │
  │               results[], tasks_report[]}                                  │
  │                                                                          │
  │  IF --telegram:                                                         │
  │    build_telegram_summary() ──→ send_telegram()                         │
  │      │  （無待處理 → console 只顯示 "Ideas scan 完成"）                   │
  │      └─→ 失敗時 fallback 輸出 console                                    │
  │                                                                          │
  │  IF (default):                                                           │
  │    build_full_summary() ──→ console 完整摘要                            │
  └──────────────────────────────────────────────────────────────────────────┘


╔═══════════════════════════════════════════════════════════════════════════════╗
║                          關鍵設計原則                                         ║
╚═══════════════════════════════════════════════════════════════════════════════╝

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  TASKS_DIR/*/tasks/T*.md 是待處理的唯一事實來源                             │
  │                                                                          │
  │  lifecycle.py 的 scan_tasks_dir() 回傳的 pending/in-progress 任務         │
  │  是每日 Telegram 通知 和 daily 掃描的核心數據                              │
  └──────────────────────────────────────────────────────────────────────────┘
                                    │
  ┌──────────────────────────────────────────────────────────────────────────┐
  │  Ideas/ → 單向 → 建立 tasks/ 專案                                         │
  │                                                                          │
  │  之後追蹤一律從 Tasks/ 目錄來，不再回頭看 idea 檔                        │
  │  idea 檔完成使命後歸檔到 _done/                                          │
  └──────────────────────────────────────────────────────────────────────────┘
```


┌─ lifecycle.py（每日 09:00 cron）──────────────────────────────────────────────┐
│                                                                                 │
│  python3 lifecycle.py --telegram                                                │
│     └─ scan_ideas() → classify() → merge() → archive() → send_telegram()        │
│                                                                                 │
│  python3 lifecycle.py --dry-run                                                 │
│     └─ 同上但只輸出，不發送                                                       │
│                                                                                 │
│  python3 lifecycle.py --json                                                    │
│     └─ 同上但輸出 JSON                                                           │
└─────────────────────────────────────────────────────────────────────────────────┘


╔══════════════════════════════════════════════════════════════════════════════════╗
║                              資料流向總結                                        ║
╚══════════════════════════════════════════════════════════════════════════════════╝

  Ideas/*.txt
     │  scan_ideas()
     ▼
  classify_idea()  ─────→  PROJECTS.md（專案上下文，避免重名）
     │
     ├─ should_skip_task()  ──→  比對 TASKS_DIR/*/tasks/T*.md（去重）
     │
     ▼
  merge_classify_with_tasks_status()  ──→  TASKS_DIR/*/tasks/T*.md（ground truth）
     │
     ▼
  executor.py: create_tasks_from_ideas()
     │
     ├─→ TASKS_DIR/<proj>/tasks/T*.md（寫入）
     ├─→ TASKS_DIR/<proj>/README.md（更新）
     ├─→ GitHub Issue（sync_single_task_to_github）
     │     │
     │     ├─ gh issue create
     │     └─ gh api addProjectV2ItemById（加入 Board）
     │
     └─→ state_sync: sync_idea_to_task_done()（回寫 idea done 標記）

  lifecycle.py: scan_tasks_dir()  ──→  TASKS_DIR/*/tasks/*.md（讀取）
     │
     ├─→ update_projects.py  →  PROJECTS.md
     ├─→ update_daily.py     →  DAILY.md
     └─→ Telegram（send_telegram）


  ┌──────────────────────────────────────────────────────────┐
  │              Ground Truth（事實來源）原則                  │
  │                                                          │
  │  TASKS_DIR/*/tasks/T*.md 的 Status: done  ───┐         │
  │           是任務完成與否的唯一依據               │         │
  │                                            ▼         │
  │  lifecycle.py 依賴此狀態決定是否歸檔 idea 檔     │         │
  │  executor.py 依賴此狀態避免重複建立 task        │         │
  │  GitHub 同步依賴此狀態關閉對應的 Issue          │         │
  └────────────────────────────────────────────────┘
```

---

# 🛠️ Executor

executor.py 是任務建立的核心工具。

### 預設模式（掃 Ideas/ 建 Tasks）

```bash
python3 scripts/executor.py                       # 掃描 Ideas/ → 建立缺漏的 Tasks
python3 scripts/executor.py --github              # 建 Tasks 後同步 GitHub Issues + Board
python3 scripts/executor.py --dry-run             # 預覽模式
python3 scripts/executor.py --normalize           # 執行前統一 Status 格式
python3 scripts/executor.py --no-spawn            # 建 Tasks 但不提示 spawn
```

流程：`scan_ideas()` → `classify_idea()` → `merge_classify_with_tasks_status()` → 去重 → 建 T*.md

### GitHub Sync 模式（獨立）

```bash
python3 scripts/executor.py --sync-github          # 掃所有 T*.md，缺漏的建 Issue
python3 scripts/executor.py --sync-github --dry-run
```

不掃 Ideas/，只檢查 T*.md frontmatter 是否有 `github_issue:`，缺則建立。

### Project Board Sync 模式（獨立）

```bash
python3 scripts/executor.py --sync-board          # 將 GitHub Issues 同步到 Project Board
python3 scripts/executor.py --sync-board --dry-run
```

找出 GitHub 上存在但未加入 Project Board 的 Issues，並將其加入。Board 和 GitHub Issues 從此保持完全同步。

### GitHub Cleanup 模式（自動關閉 + 修補 URL）

```bash
python3 scripts/executor.py --cleanup-github        # 清理並修補
python3 scripts/executor.py --cleanup-github --dry-run  # 預覽
```

Strategy 1: 搜尋 `[proj] T###` → 關閉 done/skip 的。Strategy 2: 搜尋 `github_issue:` URL → 驗證匹配。Strategy 4: 搜尋不到時自動建立新 Issue 並填入 URL。

**流程：**
1. 一次取得所有 OPEN Issues（高效）
2. 遍歷 done/skip 任務：
   - **有 `github_issue:`** → 直接用，跳過搜尋
   - **缺 `github_issue:`** → 依序嘗試：
     - 策略 1：gh search `[proj] T###`
     - 策略 2：gh search `T###`（無專案前綴）
     - 策略 3：建立新 Issue（廢除相似度比對，避免誤配）
3. 全部收集完 → 比對 OPEN Issues → 自動關閉

**找到/建立的 Issue URL 會自動補上 `github_issue:` 欄位。**

### --repair-github（修補模式）

```bash
python3 scripts/executor.py --repair-github        # 修補錯誤共用的 URL
python3 scripts/executor.py --repair-github --dry-run  # 預覽
```

**用途**：當多個任務指向同一 Issue（通常是 cleanup 相似度誤配），檢查並修補為正確的 Issue。

### 其他 GitHub 模式

| 指令 | 用途 |
|------|------|
| `--github` | 建 Tasks 後同步 GitHub |
| `--sync-github` | 直接掃 T*.md 建缺漏 Issue |
| `--cleanup-github` | 關閉 done/skip 的 Issue + 修補 URL |
| `--repair-github` | 修補錯誤共用的 github_issue URL |
| `--sync-board` | 將 GitHub Issues 同步到 Project Board |
| `--pull-github` | 從 GitHub 拉回狀態 |
| `--reverse-only` | 只推送本地 done 到 GitHub |

多策略匹配：key 完全匹配 → title 匹配 → 相似度比對，支援多格式任務命名（如 T001.md 或 T001-描述.md）。
- **LLM 上下文感知**：`classify.py` 在分類時自動讀取 PROJECTS.md 上下文，避免建立重複專案（如已有 gold-analysis 時，會建議歸類至此而非新建 gold-tracker）。

---

# ⏰ Lifecycle（每日定時）

## 流程（5 步）

1. **掃描 ideas** — `run_scan()` → `scan_ideas()` → Ideas/*.txt
2. **分類 + 合併** — `classify_idea()` → `merge_classify_with_tasks_status()` 合併 Tasks/ 實際狀態
3. **同步 done** — `sync_idea_to_task_done()` 回寫 idea 檔 done 標記
4. **歸檔** — `archive_done_ideas()` 全 done 的 idea → `_done/`
5. **掃描 Tasks/** — `scan_tasks_dir()` 取待處理（唯一事實來源）

## 設計原則

- **Tasks/ 是唯一事實來源**：每日追蹤全從 `scan_tasks_dir()` 而非 idea 檔
- **Ideas/ 單向流動**：建立後不再回頭看 idea 檔

## 指令

```bash
python3 scripts/lifecycle.py --telegram          # fresh scan + Telegram 通知
python3 scripts/lifecycle.py --dry-run           # 預覽模式
python3 scripts/lifecycle.py --json              # 輸出 JSON
```

---

# 📝 Task 檔案格式

由 `templates/task-template.md` 生成：

```markdown
---
title: {title}
status: pending
assignee: {assignee}
created: YYYY-MM-DD
updated: YYYY-MM-DD
github: 
---

# T{num} - {title}

## 目標
（描述這個任務要達成什麼）

## 驗收標準
- [ ] 標準1
- [ ] 標準2

## 備註
（風險、待處理事項注意點）
```

---

# 📊 專案 README 格式

由 `migrate_readme.py` 自動生成（預設 standard 格式）：

```bash
python3 scripts/migrate_readme.py <project-name>           # 單一專案
python3 scripts/migrate_readme.py                          # 全量更新
python3 scripts/migrate_readme.py --dry-run                # 預覽
python3 scripts/migrate_readme.py <project> --format simple # 舊格式
```

---

# 🔧 狀態同步系統

核心原則：Tasks/ 目錄是 ground truth。

| 腳本 | 用途 |
|------|------|
| `state_sync.py` | 共用模組：正規化讀取、去重、合併 |
| `sync_status.py` | 同步 T*.md 狀態回 idea 檔 |
| `task_completion_hook.py` | Agent 完成時呼叫，雙向同步 |
| `task_audit.py` | 稽核 T*.md vs README.md 一致性 |

```bash
python3 scripts/sync_status.py --dry-run          # 檢查同步狀態
python3 scripts/sync_status.py --fix-history       # 修復歷史不一致
python3 scripts/task_audit.py                     # 稽核一致性
```

---

# 📁 scripts/ 檔案一覽

| 檔案 | 用途 |
|------|------|
| `executor.py` | 核心工具：掃 Ideas/ 建 Tasks + GitHub 同步 |
| `lifecycle.py` | 定時掃描：分類 + 歸檔 + Telegram 通知 |
| `scan.py` | 掃描 Ideas/ 目錄 |
| `classify.py` | 分類 idea、拆分 tasks、分配成員 |
| `state_sync.py` | 共用狀態同步模組 |
| `sync_status.py` | 狀態同步修復工具 |
| `task_completion_hook.py` | Task 完成掛鉤 |
| `task_audit.py` | T*.md vs README 稽核 |
| `migrate_readme.py` | README 生成/更新工具 |
| `read_task_status.py` | 讀取 task 狀態 |
| `config.py` | 配置管理：.env 檔案 + 環境變數覆蓋 |
| `stats.py` | 效能分析：速度、洞察、燃盡圖 |

# 🧪 測試

```bash
cd /path/to/skills/clw-ideas2tasks
python3 -m pytest tests/ -v         # 執行所有單元測試
```

目前測試覆蓋 `state_sync.py` 的 Frontmatter 解析、Status 讀寫、邊界情況。

---

# ⚠️ 重要規則

1. **專案命名必須先確認** — 不可未確認就直接建立目錄
2. **Task 拆分上限 10 個** — 超過需說明原因並等確認
3. **已標記 done 的 idea task** — 整體仍需分析是否還有未完成項
4. **歸檔不刪除** — 移到 `_done/` 而非刪除
5. **空檔案跳過** — 0 bytes 的 .txt 不處理
6. **Tasks/ 是 ground truth** — T*.md 的 Status 欄位為最終狀態
