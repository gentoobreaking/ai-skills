#!/usr/bin/env python3
"""update_daily.py - 生成 DAILY.md 每日儀表板"""
import os, re, subprocess, sys
from pathlib import Path
from datetime import date, timedelta

# 加入目前路徑以導入 state_sync
sys.path.insert(0, str(Path(__file__).parent))
from state_sync import (
    TASKS_DIR, read_task_status, read_task_title, read_frontmatter_field
)

OUTPUT_FILE = TASKS_DIR / "DAILY.md"
TODAY = date.today()
YESTERDAY = TODAY - timedelta(days=1)
NOW = subprocess.run(["date", "+%Y-%m-%d %H:%M"], capture_output=True, text=True).stdout.strip()

def autofill_updated(task_file, content):
    """若 status=done 但沒有 updated，自動補上 created 或今天"""
    status = read_task_status(task_file)
    if status != "done":
        return False
    
    updated = read_frontmatter_field(content, "updated")
    if updated:
        return False
        
    # 補上 created 日期（若無則用今天）
    fill_date = read_frontmatter_field(content, "created") or str(TODAY)
    # 在 status: 行後插入 updated: (支援帶有 markdown 標記的 status 行)
    new_content = re.sub(r'^(.*status:.*)$', r'\1\nupdated: ' + fill_date, content, flags=re.IGNORECASE | re.MULTILINE)
    task_file.write_text(new_content, encoding="utf-8")
    return True

SKIP_DIRS = {"_inbox", "_verification", "_done"}

# 掃描所有專案
today_created = []
today_done = []
pending_tasks = []
inprogress_tasks = []

for project_dir in sorted(TASKS_DIR.iterdir()):
    if not project_dir.is_dir() or project_dir.name in SKIP_DIRS:
        continue
    tasks_dir = project_dir / "tasks"
    if not tasks_dir.is_dir():
        continue

    for task_file in sorted(tasks_dir.glob("T*.md")):
        content = task_file.read_text(encoding="utf-8", errors="replace")
        
        # 自動補 updated（若 done 但缺少）
        if autofill_updated(task_file, content):
            # 重新讀取內容
            content = task_file.read_text(encoding="utf-8", errors="replace")
            
        status = read_task_status(task_file)
        created = read_frontmatter_field(content, "created")
        updated = read_frontmatter_field(content, "updated")
        title = read_task_title(task_file)
        priority = read_frontmatter_field(content, "priority").lower()
        
        task_id = task_file.stem
        project = project_dir.name
        task_url = f"https://github.com/openclawchen8-lgtm/openclaw-tasks/blob/main/{project}/tasks/{task_file.name}"
        task_link = f"[{task_id}]({task_url})"

        if created == str(TODAY):
            today_created.append((project, task_link, title))
        if updated == str(TODAY) and status == "done":
            today_done.append((project, task_link, title))
        if status == "pending":
            pending_tasks.append((project, task_link, title, priority))
        elif status == "in-progress":
            inprogress_tasks.append((project, task_link, title, priority))

# pending 依 priority 排序（high → medium → low → none）
def priority_sort_key(t):
    p = t[3]
    if p == "high": return 0
    if p == "medium": return 1
    if p == "low": return 2
    return 3

pending_tasks.sort(key=priority_sort_key)
inprogress_tasks.sort(key=lambda t: priority_sort_key(t[:3] + (t[3],)) if len(t) == 4 else 3)

# 產出內容
def make_table(rows, cols):
    if not rows:
        return "_無_"
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join("-" * (len(c) if i == len(cols)-1 else len(c)) for i, c in enumerate(cols)) + " |"
    body = "\n".join("| " + " | ".join(str(r) for r in row) + " |" for row in rows)
    return f"{header}\n{sep}\n{body}"

new_section = make_table(today_created, ["專案", "任務", "標題"])
done_section = make_table(today_done, ["專案", "任務", "標題"])
high_pending = [(p, tid, t, pri) for p, tid, t, pri in pending_tasks if pri == "high"]
pending_section = make_table(pending_tasks, ["專案", "任務", "標題", "優先"])
inprogress_section = make_table(inprogress_tasks, ["專案", "任務", "標題", "優先"])

md = f"""# 📅 Daily Dashboard - {TODAY}

> 最後更新: {NOW} · 自動生成

---

## 🆕 今日新增任務

{new_section}

---

## ✅ 今日完成任務

{done_section}

---

## 🔥 待處理高優先級

{make_table(high_pending, ["專案", "任務", "標題", "優先"])}

---

## 🔄 進行中

{inprogress_section}

---

## 📋 所有待處理任務

{pending_section}

---

## 🔗 快速連結

- [完整專案視圖 → PROJECTS.md](https://github.com/openclawchen8-lgtm/openclaw-tasks/blob/main/PROJECTS.md)
- [每日儀表板 → DAILY.md](https://github.com/openclawchen8-lgtm/openclaw-tasks/blob/main/DAILY.md)
- [Tasks 根目錄](https://github.com/openclawchen8-lgtm/openclaw-tasks/tree/main)
- 腳本: `scripts/update_projects.py` · `scripts/update_daily.py`

---
_自動生成，請勿手動編輯_
"""

OUTPUT_FILE.write_text(md, encoding="utf-8")
print(f"✅ DAILY.md 更新完成: {NOW} (新增:{len(today_created)} 完成:{len(today_done)} 待處理:{len(pending_tasks)} 進行中:{len(inprogress_tasks)})")
