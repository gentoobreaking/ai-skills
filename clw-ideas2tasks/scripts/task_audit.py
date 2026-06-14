#!/usr/bin/env python3
"""
task_audit.py — 任務一致性稽核工具

比對每個專案的 T*.md Status 與 README.md 中同一 task 的狀態是否一致。
T*.md 是 source of truth，README.md 是團隊可見的彙整，兩邊必須同步。

用法：
  python3 task_audit.py                        # 全域稽核
  python3 task_audit.py --project openclaw-scrum  # 指定專案稽核
  python3 task_audit.py --dry-run             # 不實際修改，只顯示結果
"""
import os
import re
import sys
from pathlib import Path
from datetime import datetime

# ===== 路徑設定 =====
def _env_dir(env_key: str, name: str) -> Path:
    val = os.environ.get(env_key)
    if val:
        return Path(os.path.expanduser(val)).resolve()
    raise EnvironmentError(f"請設定環境變數 {env_key}（{name}目錄）")

try:
    TASKS_DIR = _env_dir("IDEAS2TASKS_TASKS_DIR", "Tasks")
except EnvironmentError as e:
    print(e, file=sys.stderr)
    sys.exit(1)

# ── 本地讀取 ───────────────────────────────────────────

def read_task_meta(fp):
    """讀取 T*.md 的 Status 和標題。支援 YAML frontmatter 和 Markdown task 格式。"""
    content = fp.read_text(encoding="utf-8")

    # 1. 先檢查 YAML frontmatter（--- 之間的內容）
    fm_match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
    fm_status = None
    fm_title = None
    if fm_match:
        fm_text = fm_match.group(1)
        # 兩階段：第一輪只收集 status；第二輪才處理 title/id
        # 狀態只要第一個
        for line in fm_text.splitlines():
            lm = re.match(r"^\s*status\s*:\s*(.+)", line, re.I)
            if lm and fm_status is None:
                raw = lm.group(1).strip().lower()
                raw = re.sub(r"^[✅🔄❌⏳⬜⏭️⚠️🔵🟢📋➕\U0001F7E0\U0001F7E1]\s*", "", raw)
                raw = raw.split("#")[0].strip().replace("_", "-")
                if raw in ("done", "完成", "✅"):
                    fm_status = "done"
                elif raw in ("in-progress", "in progress", "in_progress", "進行中"):
                    fm_status = "in-progress"
                elif raw in ("pending", "待處理", "待實作"):
                    fm_status = "pending"
                elif raw in ("skip", "skipped", "❌"):
                    fm_status = "skip"
                else:
                    fm_status = raw
        # 第二輪：title 優先，id 只在完全沒有 title 時才 fallback
        for line in fm_text.splitlines():
            tm = re.match(r"^\s*title\s*:\s*(.+)", line, re.I)
            if tm:
                fm_title = tm.group(1).strip().strip('"\'')
                break
        if fm_title is None:
            for line in fm_text.splitlines():
                ti = re.match(r"^\s*id\s*:\s*(.+)", line, re.I)
                if ti:
                    fm_title = ti.group(1).strip()
                    break

    # 2. 再找 Markdown body 裡的 - **Status**: 格式
    body_status = None
    body_title = None
    body = fm_match.group(0) if fm_match else content  # 跳過 frontmatter

    in_fm = False
    for line in content.splitlines():
        if line.strip() == "---":
            in_fm = not in_fm
            continue
        if in_fm:
            continue  # 跳過 frontmatter
        sm = re.match(
            r"^(-?\s*-?\s*\*+\s*[Ss]tatus\s*\*+\s*:\s*)(.+)",
            line.strip(),
            re.I,
        )
        if sm:
            raw = sm.group(2).lower().strip().split("#")[0].strip().replace("_", "-")
            raw = re.sub(r"^[✅🔄❌⏳⬜⏭️⚠️🔵🟢📋➕\U0001F7E0\U0001F7E1]\s*", "", raw)
            if raw in ("done", "完成"):
                body_status = "done"
            elif raw in ("in-progress", "in progress", "進行中"):
                body_status = "in-progress"
            elif raw in ("pending", "待處理", "待實作", "skip", "skipped"):
                body_status = "pending"
            else:
                body_status = raw
        if body_title is None:
            tm = re.match(r"^#+\s*[-*]?\s*\*?T\d+[-+:]?\d*\s*[|：:\-]\s*(.+)", line.strip())
            if tm:
                body_title = tm.group(1).strip().rstrip("|：:")

    # frontmatter 優先，body 作為 fallback
    return {
        "status": fm_status or body_status or "pending",
        "title": fm_title or body_title,
    }


def read_readme_tasks(readme_path):
    """解析 README.md，回傳 {task_id: {"status": ..., "line": ...}}。
    表格格式：| T001 | 標題 | 負責人 | Status |
    用 pipe 數量定位欄位，不靠 regex 猜測。"""
    tasks = {}
    if not readme_path.exists():
        return tasks

    for line in readme_path.read_text(encoding="utf-8").splitlines():
        # 跳过表头和分隔行
        stripped = line.strip()
        if not stripped.startswith("|") or stripped.startswith("|--") or "---" in stripped:
            continue
        if "T001" in stripped and "標題" in stripped:
            continue  # 表头行

        cols = [c.strip() for c in stripped.split("|")]
        cols = [c for c in cols if c]  # 移除空字串

        if len(cols) < 2:
            continue

        # 第一欄可能是純文字 T001 或 Markdown link [T001](url)
        raw_col = cols[0]
        # 解析 Markdown link：extract text inside [...]
        link_m = re.match(r"^\[([^\]]+)\]\(", raw_col)
        if link_m:
            raw_col = link_m.group(1)  # 取出 link 文字，如 "T006"
        # 例如：T001 / T001-評估-Fyne-環境 / T028-FIX-ISSUES
        tid_match = re.match(r"^T(\d+)(-[^\s\|:\[\]]*)?\s*", raw_col, re.I)
        if not tid_match:
            continue
        # 跳過假的 task ID（更新規範表格行，如 T`in-progress`）
        if "→" in raw_col or "`" in raw_col:
            continue
        # 正規化：去除 leading zeros，與 T*.md stem 的解析邏輯一致
        tid_num = tid_match.group(1)  # "001" / "8"
        tid_suffix = tid_match.group(2) or ""
        if re.search(r'[\u4e00-\u9fff]', tid_suffix):
            tid_suffix = ""  # 含中文就放棄後綴
        tid = str(int(tid_num)) + tid_suffix  # "8" / "8-1"

        # 最後一欄是 Status（通用規則）
        last_col = cols[-1].lower().strip()
        last_col = re.sub(r"[\U0001F300-\U0001F9FF\u200d✅🔄❌⏳⬜⏭️]+\s*", "", last_col)
        last_col = re.sub(r"[\U0001F300-\U0001F9FF\u200d✅🔄❌⏳⬜⏭️]+$", "", last_col).strip()

        if last_col in ("done", "完成", "closed", "✅"):
            status = "done"
        elif last_col in ("in-progress", "in progress", "進行中", "in review", "review", "🔄"):
            status = "in-progress"
        elif last_col in ("pending", "待處理", "待實作", "todo", "open", "⬜", "🔵"):
            status = "pending"
        elif last_col in ("skip", "skipped"):
            status = "skip"
        else:
            status = last_col  # 未知狀態保留原文

        tasks[tid] = {"status": status, "line": stripped[:100]}

    return tasks


# ── 比對邏輯 ───────────────────────────────────────────

def _normalize_stem(stem):
    """Normalize a T*.md stem to match readme_tasks key format.
    e.g. "T001-評估-Fyne-環境" → "1"
         "T008-1" → "8-1"
         "T028-FIX-ISSUES" → "28-FIX-ISSUES"
    """
    # Extract leading T + number + optional ASCII suffix
    m = re.match(r"^T(\d+)(-[^\s\|:\[\]]*)?$", stem, re.I)
    if not m:
        return stem  # fallback: return as-is
    num_str, suffix = m.group(1), (m.group(2) or "")
    # Discard suffix if it contains Chinese
    if re.search(r'[\u4e00-\u9fff]', suffix):
        suffix = ""
    return str(int(num_str)) + suffix  # "001" → "1"


def audit_project(project_dir):
    """稽核單一專案，回傳 (consistent, inconsistent, warnings)。"""
    consistent = []
    inconsistent = []
    warnings = []

    tasks_dir = project_dir / "tasks"
    readme_path = project_dir / "README.md"

    if not tasks_dir.exists():
        return [], [], [f"  tasks/ 目錄不存在"]

    readme_tasks = read_readme_tasks(readme_path) if readme_path.exists() else {}

    # 掃描所有 T*.md，用 normalized stem 當 key（與 readme_tasks 一致）
    for tf in sorted(tasks_dir.glob("T*.md")):
        tid = _normalize_stem(tf.stem)  # 規範化：與 readme_tasks key 一致
        md_meta = read_task_meta(tf)
        md_status = md_meta["status"]
        md_title = md_meta["title"]
        readme_meta = readme_tasks.get(tid)
        raw_stem = tf.stem
        # 統一顯示：純數字 stem（T001）就補上 title，已有後綴則直接用
        if md_title and re.match(r"^T\d+$", raw_stem, re.I):
            display = f"{raw_stem}-{md_title}"
            title_in_display = True
        else:
            display = raw_stem
            title_in_display = False
        if readme_meta is None:
            # README 裡沒有這條任務
            title_suffix = "" if title_in_display else (f" 「{md_title}」" if md_title else "")
            warnings.append(
                f"  [{display}] T*.md 有，但 README.md 無  |  md={md_status}{title_suffix}"
            )
            continue

        readme_status = readme_meta["status"]

        if md_status == readme_status:
            consistent.append(f"  ✅ [{display}] {md_status}")
        else:
            title_suffix = "" if title_in_display else (f"  「{md_title}」" if md_title else "")
            inconsistent.append(
                f"  ❌ [{display}] 不一致  |  T*.md={md_status}  README={readme_status}{title_suffix}"
            )
            inconsistent.append(f"       README: {readme_meta['line']}")

    return consistent, inconsistent, warnings


# ── 主程式 ─────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="任務一致性稽核")
    parser.add_argument("--project", help="只稽核指定專案")
    parser.add_argument("--dry-run", action="store_true", help="只顯示，不寫入")
    args = parser.parse_args()

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"📋 Task Audit Report — {now}"]

    # 找出要稽核的專案
    if args.project:
        project_dirs = [TASKS_DIR / args.project]
        if not project_dirs[0].exists():
            print(f"❌ 專案不存在: {project_dirs[0]}")
            sys.exit(1)
    else:
        project_dirs = sorted(
            d for d in TASKS_DIR.iterdir()
            if d.is_dir() and not d.name.startswith("_") and not d.name.startswith(".")
        )

    total_consistent = 0
    total_inconsistent = 0
    total_warnings = 0

    for project_dir in project_dirs:
        project_name = project_dir.name
        consistent, inconsistent, warnings = audit_project(project_dir)

        if not consistent and not inconsistent and not warnings:
            continue  # 跳過空專案

        lines.append(f"\n{'='*50}")
        lines.append(f"📁 {project_name}")

        for w in warnings:
            lines.append(w)
            total_warnings += 1

        for c in consistent:
            lines.append(c)
            total_consistent += 1

        for i in inconsistent:
            lines.append(i)
            total_inconsistent += 1

        if not inconsistent:
            lines.append(f"  ✅ 全部一致 ({len(consistent)} 項)")
        else:
            lines.append(f"  ❌ {len(inconsistent)//2} 項不一致，請確認")

    # 摘要
    lines.append(f"\n{'='*50}")
    lines.append(
        f"📊 總計  ✅ 一致: {total_consistent}  |  "
        f"❌ 不一致: {total_inconsistent}  |  ⚠️ 警告: {total_warnings}"
    )

    report = "\n".join(lines)
    print(report)

    if total_inconsistent > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()