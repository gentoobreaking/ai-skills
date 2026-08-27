#!/usr/bin/env python3
"""update_daily.py - 生成 DAILY.md 每日儀表板"""

import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# 加入目前路徑以導入 state_sync
sys.path.insert(0, str(Path(__file__).parent))
from state_sync import (
    TASKS_DIR,
    read_frontmatter_field,
    read_task_status,
    read_task_title,
)

OUTPUT_FILE = TASKS_DIR / "DAILY.md"
TODAY = date.today()
TODAY_STR = TODAY.isoformat()
TODAY_START = datetime.combine(TODAY, datetime.min.time())
TODAY_END = datetime.combine(TODAY, datetime.max.time())
NOW = subprocess.run(
    ["date", "+%Y-%m-%d %H:%M"], capture_output=True, text=True
).stdout.strip()
REPO_BASE = "https://github.com/gentoobreaking/ai-tasks"

SKIP_DIRS = {"_inbox", "_verification", "_done"}


def parse_updated(date_str: str):
    """解析 updated 日期，回傳 datetime 或 None"""
    if not date_str:
        return None
    for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%d %H:%M"]:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None


def is_today(dt: datetime) -> bool:
    return TODAY_START <= dt <= TODAY_END


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

        status = read_task_status(task_file)
        created = read_frontmatter_field(content, "created")
        updated = read_frontmatter_field(content, "updated")
        title = read_task_title(task_file)
        priority = read_frontmatter_field(content, "priority").lower()

        task_id = task_file.stem
        project = project_dir.name
        task_url = f"{REPO_BASE}/blob/main/{project}/tasks/{task_file.name}"
        task_link = f"[{task_id}]({task_url})"

        if created == TODAY_STR:
            today_created.append((project, task_link, title))
        if updated == TODAY_STR and status == "done":
            today_done.append((project, task_link, title))
        if status == "pending":
            pending_tasks.append((project, task_link, title, priority))
        elif status == "in-progress":
            inprogress_tasks.append((project, task_link, title, priority))


# pending 依 priority 排序（high → medium → low → none）
def priority_sort_key(t):
    p = t[3]
    if p == "high":
        return 0
    if p == "medium":
        return 1
    if p == "low":
        return 2
    return 3


pending_tasks.sort(key=priority_sort_key)
inprogress_tasks.sort(key=priority_sort_key)

# 今日統計計數
today_created_count = len(today_created)
today_done_count = len(today_done)
today_inprogress_count = len(inprogress_tasks)
today_pending_count = len(pending_tasks)

today_active = today_done_count + today_inprogress_count + today_pending_count
today_completion_rate = (
    (today_done_count * 100 // today_active) if today_active > 0 else 0
)

# 今日效能分析：速率、循環時間

daily_completions = {}
cycle_times = []

for project_dir in sorted(TASKS_DIR.iterdir()):
    if not project_dir.is_dir() or project_dir.name in SKIP_DIRS:
        continue
    tasks_dir = project_dir / "tasks"
    if not tasks_dir.is_dir():
        continue
    for task_file in sorted(tasks_dir.glob("T*.md")):
        content = task_file.read_text(encoding="utf-8", errors="replace")
        updated_str = read_frontmatter_field(content, "updated")
        updated_dt = parse_updated(updated_str)
        if updated_dt and is_today(updated_dt):
            daily_completions[TODAY_STR] = daily_completions.get(TODAY_STR, 0) + 1
        created_str = read_frontmatter_field(content, "created")
        if updated_dt and is_today(updated_dt) and created_str:
            try:
                created_dt = datetime.strptime(
                    created_str.split("#")[0].strip(), "%Y-%m-%d"
                )
                cycle = (updated_dt - created_dt).days
                if cycle >= 0:
                    cycle_times.append(cycle)
            except ValueError:
                pass

avg_cycle = sum(cycle_times) / len(cycle_times) if cycle_times else 0
today_velocity = daily_completions.get(TODAY_STR, 0)
week_velocity = sum(
    daily_completions.get(
        (datetime.combine(TODAY, datetime.min.time()) - timedelta(days=i)).strftime(
            "%Y-%m-%d"
        ),
        0,
    )
    for i in range(7)
)

# 今日總覽表
overview_section = f"""## 📊 今日總覽

| 指標 | 數量 |
|------|------|
| 新增任務 | {today_created_count} |
| 完成任務 | {today_done_count} |
| 進行中 | {today_inprogress_count} |
| 待處理 | {today_pending_count} |
| 完成率 | {today_completion_rate}% |"""

# 今日效能分析
perf_section = f"""## 📈 今日效能分析

| 指標 | 數值 |
|------|------|
| 今日完成速率 | {today_velocity} 任務 |
| 近 7 日速率 | {week_velocity} 任務 |
| 平均循環天數 | {avg_cycle:.1f} 天 |
| 今日完成任務循環時間樣本 | {len(cycle_times)} 筆 |"""


# 產出內容
def make_table(rows, cols):
    if not rows:
        return "_無_"
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join("-" * len(c) for c in cols) + " |"
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

{overview_section}

---

{perf_section}

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

- [完整專案視圖 → PROJECTS.md](https://github.com/gentoobreaking/ai-tasks/blob/main/PROJECTS.md)
- [每日儀表板 → DAILY.md](https://github.com/gentoobreaking/ai-tasks/blob/main/DAILY.md)
- [Tasks 根目錄](https://github.com/gentoobreaking/ai-tasks/tree/main)
- 腳本: `scripts/update_projects.py` · `scripts/update_daily.py`

---
_自動生成，請勿手動編輯_
"""

OUTPUT_FILE.write_text(md, encoding="utf-8")
_tmp = OUTPUT_FILE.with_suffix(OUTPUT_FILE.suffix + ".tmp")
_tmp.write_text(md, encoding="utf-8")
_tmp.replace(OUTPUT_FILE)
print(
    f"✅ DAILY.md 更新完成: {NOW} (新增:{len(today_created)} 完成:{len(today_done)} 待處理:{len(pending_tasks)} 進行中:{len(inprogress_tasks)})"
)
