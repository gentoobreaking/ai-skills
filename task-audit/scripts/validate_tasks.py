#!/usr/bin/env python3
"""任務書驗證腳本（task-audit 步驟 1 / spec-to-tasks 步驟 6 共用）。

用法：
    python3 validate_tasks.py <專案名> [更多專案名...]

檢查：frontmatter 九欄位、status 合法值、assignee、日期格式、
depends_on 格式與引用存在性、無循環、目標/驗收標準章節與非空勾選項。

離開碼：0 = 全部通過；1 = 有問題；2 = 用法錯誤
"""
from pathlib import Path
import re
import sys


def validate(project, home="/Users/david"):
    root = Path(home) / "tasks" / project / "tasks"
    if not root.is_dir():
        return 0, [f"{root} 不存在"]
    files = sorted(root.glob("T*.md"))
    issues = []
    ids = {}
    for f in files:
        s = f.read_text()
        tid = f.stem.split("-")[0]
        if not s.startswith("---"):
            issues.append(f"{f.name}: 缺 frontmatter")
            continue
        fm_end = s.find("---", 3)
        fm = s[3:fm_end]
        body = s[fm_end:]
        for key in ["github_issue:", "title:", "type:", "priority:", "status:",
                    "depends_on:", "assignee:", "created:", "updated:"]:
            if key not in fm:
                issues.append(f"{f.name}: frontmatter 缺 {key}")
        m = re.search(r"^status: (.+)$", fm, re.M)
        if m and m.group(1).strip() not in ("pending", "done", "in-progress"):
            issues.append(f"{f.name}: 非法 status {m.group(1)!r}")
        m = re.search(r'^assignee: "?([^"\n]+)"?$', fm, re.M)
        if not m or "pi with opencode" not in m.group(1):
            issues.append(f"{f.name}: assignee 異常")
        for k in ("created", "updated"):
            if not re.search(rf"^{k}: (\d{{4}}-\d{{2}}-\d{{2}})$", fm, re.M):
                issues.append(f"{f.name}: {k} 格式錯誤")
        m = re.search(r"^depends_on:\s*(\[\])?$", fm, re.M)
        mlist = re.search(r"^depends_on:\n((?:- .+\n)+)", fm, re.M)
        if not m and not mlist:
            issues.append(f"{f.name}: depends_on 格式錯誤（應為 [] 單行或列表）")
        dep_ids = []
        if mlist:
            for line in mlist.group(1).splitlines():
                d = line.strip("- ").strip()
                dep_ids.append(d)
                if not re.match(r"^T\d{3}$", d):
                    issues.append(f"{f.name}: 依賴格式異常 {d!r}")
        ids[tid] = dep_ids
        for sec in ["## 目標", "## 驗收標準"]:
            if sec not in body:
                issues.append(f"{f.name}: 缺章節 {sec}")
        acc = re.search(r"## 驗收標準\n(.*?)(\n## |\Z)", body, re.S)
        if acc and not re.findall(r"- \[.\]", acc.group(1)):
            issues.append(f"{f.name}: 驗收標準無勾選項")
    for tid, deps in ids.items():
        for d in deps:
            if d not in ids:
                issues.append(f"{tid}: 依賴不存在的任務 {d}")
    visiting, visited = set(), set()

    def dfs(node, chain):
        if node in visiting:
            issues.append(f"循環依賴：{' → '.join(chain + [node])}")
            return
        if node in visited:
            return
        visiting.add(node)
        for d in ids.get(node, []):
            dfs(d, chain + [node])
        visiting.remove(node)
        visited.add(node)

    for n in ids:
        dfs(n, [])
    return len(files), issues


if __name__ == "__main__":
    projects = sys.argv[1:]
    if not projects:
        print("用法：python3 validate_tasks.py <專案名> [更多專案名...]")
        sys.exit(2)
    all_issues = []
    for proj in projects:
        n, issues = validate(proj)
        print(f"== {proj}: {n} 張任務書，{len(issues)} 個問題 ==")
        for i in issues:
            print("  ❌", i)
            all_issues.append(i)
    print()
    print("總結：", "✅ 全數通過" if not all_issues else f"❌ 共 {len(all_issues)} 個問題需修正")
    sys.exit(1 if all_issues else 0)
