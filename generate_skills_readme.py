#!/usr/bin/env python3
"""generate_skills_readme.py - Auto-generate README.md (v8)"""
import sys, subprocess
from pathlib import Path
from datetime import datetime

SKILLS_DIR = Path.home() / "skills"
OUTPUT_FILE = SKILLS_DIR / "README.md"
REPO_URL = "https://github.com/gentoobreaking/ai-skills"

ORIGINAL_EXTRA = {"scrum-task-tracker", "github-issues", "github-projects", "prompt-injection-filter"}

def is_original_dir(name):
    return name.startswith("clw-") or name in ORIGINAL_EXTRA

def parse_frontmatter(text):
    import re, yaml
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m: return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except Exception:
        return {}

def scan_skills(sd):
    skills = []
    for d in sorted(sd.iterdir()):
        if not d.is_dir() or d.name.startswith("_"): continue
        smd = d / "SKILL.md"
        if not smd.exists(): continue
        text = smd.read_text(encoding="utf-8", errors="replace")
        fm = parse_frontmatter(text)
        desc = fm.get("description", "")
        if not desc and isinstance(fm.get("metadata"), dict):
            desc = fm["metadata"].get("description", "")
        desc = desc.replace("\n", " ").strip()
        emoji = ""
        if isinstance(fm.get("metadata"), dict):
            emoji = fm["metadata"].get("emoji", "")
        skills.append({
            "dir": d.name, "name": fm.get("name", d.name),
            "desc": desc, "emoji": emoji, "original": is_original_dir(d.name),
        })
    return skills

def build_tree(skills):
    ss = sorted(skills, key=lambda x: x["dir"].lower())
    max_w = max(len("├── " + s["dir"]) for s in ss)
    lines = ["```", "ai-skills/"]
    for s in ss:
        prefix = ("├── " + s["dir"])
        em = (s["emoji"] + " ") if s["emoji"] else ""
        tag = "原創" if s["original"] else "第三方"
        desc = s["desc"][:40]
        lines.append(prefix.ljust(max_w) + "  # " + em + tag + "：" + desc)
    lines.append("```")
    return "\n".join(lines)

def generate_markdown(skills):
    now = datetime.now().strftime("%Y-%m-%d")
    orig = [s for s in skills if s["original"]]
    third = [s for s in skills if not s["original"]]
    def row(s):
        em = (s["emoji"] + " ") if s["emoji"] else ""
        return "| " + em + "`" + s["name"] + "` | " + s["name"].replace("-", " ").title() + " | " + s["desc"][:80] + " |"
    parts = ["# ai-skills", "", "> 豪的 AI Skills 備份倉庫", ""]
    parts += ["[![OpenClaw](https://img.shields.io/badge/AI-Skills-blue)](" + REPO_URL + ")",
             "[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)", ""]
    parts += ["<!-- TOC -->", "- [原創技能](#原創技能--original-skills)"]
    if third: parts[-1] += "\n- [第三方技能](#第三方技能--third-party-skills)"
    parts += ["", "---", "", "## 目錄結構 | Directory Structure", "", build_tree(skills), "", "---", ""]
    if orig:
        parts += ["## 原創技能 | Original Skills", "", "| Skill | 名稱 | 說明 |", "|-------|------|------|"]
        parts += [row(s) for s in orig]
        parts += ["", "---", ""]
    if third:
        parts += ["## 第三方技能 | Third-Party Skills", "", "| Skill | 名稱 | 說明 |", "|-------|------|------|"]
        parts += [row(s) for s in third]
        parts += ["", "---", ""]
    parts += ["## 安裝方式 | Installation", "", "每個 Skill 都有獨立的 SKILL.md 說明文件。", "",
             "```bash", "# ClawHub", "skillhub install <skill-name>", "", "# OpenClaw CLI", "openclaw skills install <skill-name>", "```", "",
             "---", "", "*最後更新：" + now + "*", ""]
    return "\n".join(parts)

def main():
    try:
        import yaml
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyyaml", "-q", "--break-system-packages"])
        import yaml
    skills = scan_skills(SKILLS_DIR)
    print("[掃描] 找到", len(skills), "個 skill")
    for s in skills:
        tag = "原創" if s["original"] else "第三方"
        print("  ", s["emoji"] or "?", "[" + tag + "]", s["dir"])
    OUTPUT_FILE.write_text(generate_markdown(skills), encoding="utf-8")
    print("[輸出] 已寫入", OUTPUT_FILE)

if __name__ == "__main__":
    main()
