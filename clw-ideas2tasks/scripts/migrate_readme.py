#!/usr/bin/env python3
"""
為所有專案建立/更新 README.md，任務狀態以 T*.md 為準。

支援兩種格式：
- standard（預設）：含已實作/Skip/開發中/待實作/Task列表 5 區塊
- simple：標準任務列表格式（Task | 名稱 | 狀態）

用法：
  python3 migrate_readme.py              # 全量更新所有專案（標準格式）
  python3 migrate_readme.py md-viewer-app  # 只更新指定專案
  python3 migrate_readme.py --dry-run   # 預覽不寫入
  python3 migrate_readme.py --format simple  # 指定簡單格式
"""
import re
import sys
import argparse
import os
from pathlib import Path
from datetime import datetime

# ===== 路徑設定 =====
def _env_dir(env_key: str, name: str) -> Path:
    val = os.environ.get(env_key)
    if val:
        return Path(os.path.expanduser(val)).resolve()
    raise EnvironmentError(f"請設定環境變數 {env_key}（{name}目錄）")

try:
    TASKS_ROOT = _env_dir("IDEAS2TASKS_TASKS_DIR", "Tasks")
except EnvironmentError as e:
    print(e, file=sys.stderr)
    sys.exit(1)

# GitHub Tasks repo URL template
GITHUB_TASKS_BASE = "https://github.com/openclawchen8-lgtm/openclaw-tasks/blob/main"


def make_task_link(project_name, task_stem, display=None):
    """Generate a clickable Markdown link for a task.
    
    Args:
        project_name: e.g. "md-viewer-app"
        task_stem:    e.g. "T001-評估-Fyne-環境" (without .md)
        display:       shown text, defaults to formatted T ID like "T001"
    """
    url = f"{GITHUB_TASKS_BASE}/{project_name}/tasks/{task_stem}.md"
    # Format display as T### (or T###-suffix)
    if display is None:
        display = format_task_id(parse_task_num(task_stem + ".md") or task_stem)
    return f"[{display}]({url})"
SKIP_DIRS = {".git", "_inbox", "_verification"}

STATUS_MAP = {
    "done": "done", "完成": "done",
    "in-progress": "in-progress", "in progress": "in-progress", "進行中": "in-progress",
    "pending": "pending", "待處理": "pending", "open": "pending",
    "skip": "skip", "skipped": "skip",
}
EMOJI_MAP = {
    "done": "✅",
    "in-progress": "🔧",
    "pending": "📋",
    "skip": "⚠️"
}

def normalize_status(raw):
    raw = raw.lower().strip()
    for key, norm in STATUS_MAP.items():
        if key in raw:
            return norm
    return "pending"

def get_emoji(s): return EMOJI_MAP.get(s, "📋")


def parse_frontmatter(content):
    fm_match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
    status, title = "pending", None
    if fm_match:
        for line in fm_match.group(1).splitlines():
            lm = re.match(r"^\s*status\s*:\s*(.+)", line, re.I)
            if lm:
                raw = lm.group(1).strip().lower().split("#")[0].strip().replace("_", "-").replace("_", "-")
                status = normalize_status(raw)
            tm = re.match(r'^\s*title\s*:\s*(.+)', line, re.I)
            if tm:
                title = tm.group(1).strip().strip('"\'')
    if not title:
        tm = re.match(r"^#+\s*[-*]?\s*\*?T\d+[-+]?\d*\s*[\|：:]\s*(.+)", content)
        if tm:
            title = tm.group(1).strip().rstrip("|：:")
    # body 內的 - **Status**: xxx（比 frontmatter 優先）
    body_status = None
    for line in content.splitlines():
        sm = re.match(r"^(-?\s*-?\s*\*+\s*[Ss]tatus\s*\*+\s*:\s*)(.+)", line.strip())
        if sm:
            raw = sm.group(2).lower().strip().split("#")[0].strip().replace("_", "-")
            if raw in ("done", "完成"): body_status = "done"
            elif raw in ("in-progress", "in progress", "in_progress", "🔧"): body_status = "in-progress"
            elif raw in ("pending", "待處理", "待實作", "📋"): body_status = "pending"
            elif raw in ("skip", "skipped", "⚠️"): body_status = "skip"
            else: body_status = raw
    if status == "pending" and body_status:
        status = body_status
    return status, title


def parse_body_status(content):
    for line in content.splitlines():
        sm = re.match(r"^(-?\s*-?\s*\*+\s*Status\s*\*+\s*:\s*)(.+)", line.strip())
        if sm:
            raw = sm.group(2).lower().strip().split("#")[0].strip().replace("_", "-")
            raw = re.sub(r"^[✅🔄❌⏳⬜🔵🟢📋➕🔧]\s*", "", raw)
            return normalize_status(raw)
    return "pending"


def parse_task_num(name):
    # 支援 T001-中文標題.md、T011-Menubar.md、T010-B1.md、T011-FIX-01.md 等格式
    # 保留完整 ID（如 11-Menubar、10-B1）而非只取數字部分
    m = re.match(r"^T(.+?)\.md$", name)
    if not m: return None
    raw_id = m.group(1)
    # 數字部分正規化（前導零移除）
    num_m = re.match(r"^0*(\d+)", raw_id)
    if not num_m: return None
    num = int(num_m.group(1))
    # 如果有子 ID（如 -Menubar、-B1、-FIX-01），保留完整 ID
    if raw_id != str(num):
        return str(num) + raw_id[len(num_m.group(0)):]
    return str(num)


def get_task_meta(path):
    content = path.read_text(encoding="utf-8")
    fm_status, fm_title = parse_frontmatter(content)
    body_status = parse_body_status(content)
    status = fm_status if fm_status != "pending" else body_status
    if status == "pending" and body_status != "pending":
        status = body_status
    title = fm_title or f"任務 {path.stem}"
    num = parse_task_num(path.name)
    # 讀取 assignee
    assignee = None
    fm_match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
    if fm_match:
        for line in fm_match.group(1).splitlines():
            am = re.match(r"^\s*assignee\s*:\s*(.+)", line, re.I)
            if am:
                assignee = am.group(1).strip()
                break
    stem = path.stem  # e.g. "T001-評估-Fyne-環境"（含完整後綴）
    return {"num": num, "status": status, "title": title, "assignee": assignee, "path": path, "stem": stem}


def is_valid_task_col(col1):
    col = col1.strip()
    if not col: return False
    if re.search(r"[\u4e00-\u9fff]", col): return False
    if "→" in col or "`" in col: return False
    if not re.match(r"^\d", col): return False
    return True


def parse_readme_task_col(task_col):
    # 支援中文後綴：T001、T001-評估、T001-評估-Fyne-環境 等
    m = re.match(r"^T0*(\d+)(-[^\s\|:\[\]]+)?", task_col.strip(), re.I)
    if not m: return None
    return m.group(1) + (m.group(2) or "")


def parse_readme_tasks(readme_path):
    tasks = {}
    if not readme_path.exists():
        return tasks
    for line in readme_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"): continue
        if "|--" in stripped or stripped.startswith("| Task"): continue
        cols = [c.strip() for c in stripped.split("|")]
        if len(cols) < 5: continue
        task_col = cols[1].strip()
        if not is_valid_task_col(task_col): continue
        num = parse_readme_task_col(task_col)
        if not num: continue
        title = cols[2].strip() if len(cols) > 2 else "未知"
        assignee = cols[3].strip() if len(cols) > 3 else "未指派"
        status_col = cols[4].strip()
        status = normalize_status(status_col)
        tasks[num] = {"num": num, "status": status, "title": title,
                      "assignee": assignee, "from_readme": True}
    return tasks


def ensure_task_file(task_dir, task_info):
    num = task_info["num"]
    title = task_info["title"]
    status = task_info["status"]
    assignee = task_info.get("assignee", "未指派")
    today = datetime.now().strftime("%Y-%m-%d")
    path = task_dir / f"T{num}.md"
    content = f"""---
title: {title}
status: {status}
assignee: {assignee}
created: {today}
updated: {today}
---

# T{num} - {title}

## 目標
（描述這個任務要達成什麼）

## 驗收標準
- [ ] 標準1
- [ ] 標準2

## 備註
（風險、待處理事項注意點）
"""
    path.write_text(content, encoding="utf-8")
    return path


# =============================================================================
# 格式生成器：standard（標準格式）
# =============================================================================

def build_readme_standard(project_name, tasks):
    def sort_key(t):
        n = t["num"]
        m = re.match(r"(\d+)(.*)", n)
        return (int(m.group(1)) if m else 0, m.group(2) if m else "")
    sorted_tasks = sorted(tasks.values(), key=sort_key)
    rows = []
    for t in sorted_tasks:
        emoji = get_emoji(t["status"])
        status_text = f"{emoji} {t['status']}"
        assignee = t.get("assignee", "未指派")
        title = t.get("title", f"任務 {t['num']}")
        stem = t.get("stem", t["num"])
        task_link = make_task_link(proj_name, stem)
        rows.append(f"| {task_link} | {title} | {assignee} | 中 | {status_text} |")
    rows_text = "\n".join(rows) if rows else "| | | | | |"
    return f"""# {project_name}

## 任務狀態

| Task | 標題 | 負責人 | 優先順序 | 狀態 |
|------|------|--------|---------|------|
{rows_text}

## 更新規範

每次狀態變更時，**同時更新** T\*.md 與本檔案：

**pending → in-progress**：T\*.md 改 `status: in-progress`，README 改 `⬜ pending` → `🔄 in-progress`

**in-progress → done**：T\*.md 改 `status: done`，README 改 `🔄 in-progress` → `✅ done`

- 更新 T\*.md 時一併更新 `updated` 欄位
- 完成後同步 GitHub Issue 狀態（`--sync-state`）
"""


# =============================================================================
# 格式生成器：標準格式（已實作/Skip/開發中/待實作 4 區塊）
# =============================================================================

MDVIEWER_TASK_LINKS = {
    # 從 task title 提取功能名稱（用於「已實作功能」區塊）
    # 格式：num -> (功能名稱, Task 引用)
    # 由 generate_standard_readme 動態生成，這裡保留作為 fallback
}

def extract_feature_name(title):
    """從 task title 提取功能名稱（用於「已實作功能」區塊）"""
    # 移除 [T###] 及其變體（如 [T011-A]、[T010-B1]、[T011-FIX-01]）
    title = re.sub(r'^\s*\[T\d+[^\]]*\]\s*', '', title)
    title = title.strip()
    # 移除常見的任務描述前綴
    title = re.sub(r'^(實作|實驗|研究|評估|建立|修復|更新|新增)\s*', '', title)
    return title.strip()


def format_task_id(num):
    """格式化 Task ID 顯示（如 11-A → T11-A，10 → T010）"""
    # 提取數字部分和子 ID（如有）
    m = re.match(r'^(\d+)(.*)', num)
    if not m: return f'T{num}'
    base = int(m.group(1))
    suffix = m.group(2)
    # 如果有子 ID（如 -A、-Menubar、-FIX-01），用 T{base}{suffix}
    if suffix:
        return f'T{base}{suffix}'
    # 否則用標準化形式（前導零）
    return f'T{base:03d}'


def mdviewer_sort_key(t):
    """排序：先按數字，再按子 ID（如有）"""
    n = t["num"]
    m = re.match(r'(\d+)(.*)', n)
    return (int(m.group(1)) if m else 0, m.group(2) if m else "")


def generate_standard_readme(project_dir, tasks):
    """生成標準格式 README（含已實作/Skip/開發中/待實作/Task列表 5 區塊）"""
    
    sorted_tasks = sorted(tasks.values(), key=mdviewer_sort_key)
    
    # 分組
    done_tasks = [t for t in sorted_tasks if t["status"] == "done"]
    skip_tasks = [t for t in sorted_tasks if t["status"] == "skip"]
    in_progress_tasks = [t for t in sorted_tasks if t["status"] == "in-progress"]
    pending_tasks = [t for t in sorted_tasks if t["status"] == "pending"]
    
    # 統計
    done_count = len(done_tasks)
    skip_count = len(skip_tasks)
    pending_count = len(pending_tasks)
    in_progress_count = len(in_progress_tasks)
    
    # ----- 已實作功能 -----
    implemented_rows = []
    for t in done_tasks:
        feature_name = extract_feature_name(t["title"])
        implemented_rows.append(f"| {feature_name} |")
    implemented_section = "\n".join(implemented_rows) if implemented_rows else "| （無） |"
    
    # ----- Skip 項目 -----
    skip_rows = []
    for t in skip_tasks:
        # 嘗試從 title 提取說明
        desc = t.get("title", "")
        desc = re.sub(r'^\[T\d+[-+]?\d*\]\s*', '', desc)
        desc = re.sub(r'^(實作|實驗|研究|評估)\s*', '', desc)
        stem = t.get("stem", t["num"])
        task_link = make_task_link(project_dir.name, stem)
        skip_rows.append(f"| {task_link} | {desc.strip()} |")
    skip_section = "\n".join(skip_rows) if skip_rows else "| | |"
    
    # ----- 開發中 -----
    # ----- 開發中 -----
    in_progress_rows = []
    for t in in_progress_tasks:
        name = t.get("title", "")
        name = re.sub(r'^\[T\d+[^\]]*\]\s*', '', name)
        stem = t.get("stem", t["num"])
        task_link = make_task_link(project_dir.name, stem)
        in_progress_rows.append(f"| {task_link} | {name.strip()} | |")
    in_progress_section = "\n".join(in_progress_rows) if in_progress_rows else "| | | |"
    
    # ----- 待實作 -----
    pending_rows = []
    for t in pending_tasks:
        name = t.get("title", "")
        name = re.sub(r'^\[T\d+[^\]]*\]\s*', '', name)
        stem = t.get("stem", t["num"])
        task_link = make_task_link(project_dir.name, stem)
        pending_rows.append(f"| {task_link} | {name.strip()} | |")
    pending_section = "\n".join(pending_rows) if pending_rows else "| | | |"
    
    # ----- Task 列表 -----
    task_list_rows = []
    for t in sorted_tasks:
        emoji = get_emoji(t["status"])
        status_text = emoji
        if t["status"] == "done": status_text = "✅ done"
        elif t["status"] == "skip": status_text = "⏭️ skip"
        elif t["status"] == "in-progress": status_text = "🔧 in-progress"
        else: status_text = "📋 pending"
        
        name = t.get("title", "")
        name = re.sub(r'^\[T\d+[-+]?\d*\]\s*', '', name)
        
        # 點擊連結
    for t in sorted_tasks:
        emoji = get_emoji(t["status"])
        status_text = emoji
        if t["status"] == "done": status_text = "✅ done"
        elif t["status"] == "skip": status_text = "⏭️ skip"
        elif t["status"] == "in-progress": status_text = "🔧 in-progress"
        else: status_text = "📋 pending"
        
        name = t.get("title", "")
        name = re.sub(r'^\[T\d+[^\]]*\]\s*', '', name)
        
        stem = t.get("stem", t["num"])  # 含後綴的完整檔名
        task_link = make_task_link(project_dir.name, stem)
        task_list_rows.append(f"| {task_link} | {name.strip()} | {status_text} |")
    task_list_section = "\n".join(task_list_rows) if task_list_rows else "| | | |"
    
    # 組裝
    readme = f"""# {project_dir.name}

## 已實作功能

| 功能 |
|------|
{implemented_section}

## Skip 項目

| Task | 說明 |
|------|------|
{skip_section}

## 開發中

| Task | 名稱 | 說明 |
|------|------|------|
{in_progress_section}

## 待實作

| Task | 名稱 | 說明 |
|------|------|------|
{pending_section}

## Task 列表

| # | 名稱 | 狀態 |
|---|------|------|
{task_list_section}

**✅ done: {done_count} | 🔧 in-progress: {in_progress_count} | ⏭️ skip: {skip_count} | 📋 pending: {pending_count}**
"""
    return readme


# =============================================================================
# 主邏輯
# =============================================================================

def process_project(proj_dir, fmt, dry_run=False):
    """處理單一專案"""
    proj_name = proj_dir.name
    tasks_dir = proj_dir / "tasks"
    readme_path = proj_dir / "README.md"
    
    task_files = list(tasks_dir.glob("T*.md")) if tasks_dir.exists() else []
    tasks = {}
    
    for tf in task_files:
        try:
            meta = get_task_meta(tf)
            if meta["num"]:
                tasks[meta["num"]] = meta
        except Exception as e:
            print(f"   ⚠️ 讀取 {tf.name} 失敗: {e}")
    
    # 合併 README 中已有但 T*.md 中沒有的任務
    if readme_path.exists():
        readme_tasks = parse_readme_tasks(readme_path)
        for num, info in readme_tasks.items():
            if num not in tasks:
                tasks[num] = info
    
    if not tasks:
        return "skipped", f"{proj_name}（無任務）"
    
    # 生成 README
    if fmt == "standard":
        new_readme = generate_standard_readme(proj_dir, tasks)
    else:
        new_readme = build_readme_standard(proj_name, tasks)
    
    new_readme += f"\n> 自動生成於 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    
    if dry_run:
        return "dry-run", f"{proj_name}（預覽模式）"
    
    readme_path.write_text(new_readme, encoding="utf-8")
    
    # 統計
    done = sum(1 for t in tasks.values() if t["status"] == "done")
    skip = sum(1 for t in tasks.values() if t["status"] == "skip")
    in_progress = sum(1 for t in tasks.values() if t["status"] == "in-progress")
    pending = sum(1 for t in tasks.values() if t["status"] == "pending")
    
    if not readme_path.exists():
        return "created", f"{proj_name}（done:{done} in-progress:{in_progress} skip:{skip} pending:{pending}）"
    else:
        return "updated", f"{proj_name}（done:{done} in-progress:{in_progress} skip:{skip} pending:{pending}）"


def main():
    parser = argparse.ArgumentParser(description="更新專案 README.md")
    parser.add_argument("project", nargs="?", help="專案名稱（可選，不指定則處理所有）")
    parser.add_argument("--dry-run", action="store_true", help="預覽不寫入")
    parser.add_argument("--format", choices=["standard", "simple"],
                        help="指定輸出格式 (standard 含已實作/Skip/開發中/待實作 4 區塊；simple 為純任務列表)")
    args = parser.parse_args()
    
    fmt = args.format or "standard"
    dry_run = args.dry_run
    project_filter = args.project
    
    results = {"created": [], "updated": [], "skipped": [], "dry-run": [], "errors": []}
    
    if project_filter:
        proj_dir = TASKS_ROOT / project_filter
        if not proj_dir.exists():
            print(f"❌ 專案不存在: {project_filter}")
            return
        if proj_dir.name in SKIP_DIRS:
            print(f"❌ 專案被排除: {project_filter}")
            return
        proj_dirs = [proj_dir]
    else:
        proj_dirs = sorted(TASKS_ROOT.iterdir())
    
    for proj_dir in proj_dirs:
        if not proj_dir.is_dir() or proj_dir.name in SKIP_DIRS:
            continue
        
        try:
            status, msg = process_project(proj_dir, fmt, dry_run)
            results[status].append(msg)
        except Exception as e:
            results["errors"].append(f"{proj_dir.name}: {e}")
    
    # 輸出結果
    if results["created"]:
        print(f"✅ 新建 README：{len(results['created'])} 個")
        for p in results["created"]: print(f"   - {p}")
    
    if results["updated"]:
        print(f"🔄 更新 README：{len(results['updated'])} 個")
        for p in results["updated"]: print(f"   - {p}")
    
    if results["dry-run"]:
        print(f"👀 預覽（未寫入）：{len(results['dry-run'])} 個")
        for p in results["dry-run"]: print(f"   - {p}")
    
    if results["skipped"]:
        print(f"⏭️  跳過：{len(results['skipped'])} 個")
        for p in results["skipped"]: print(f"   - {p}")
    
    if results["errors"]:
        print(f"❌ 錯誤：{len(results['errors'])} 個")
        for e in results["errors"]: print(f"   - {e}")
    else:
        print(f"\n✨ 完成")


if __name__ == "__main__":
    main()
