#!/usr/bin/env python3
"""
ideas2tasks clw_idea.py
快速建立 Idea 檔的 CLI 工具

用法：
  clw_idea "今天突然想做個語音助手"
  clw_idea "優化登入流程" --description "需要檢查 OAuth 流程"
"""
import os
import sys
import re
import argparse
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent.resolve()
SKILL_DIR = SCRIPT_DIR.parent

try:
    sys.path.insert(0, str(SCRIPT_DIR))
    from config import get_ideas_dir
except Exception:
    IDEAS_DIR = Path(os.environ.get("IDEAS2TASKS_IDEAS_DIR", "~/Tasks/Ideas"))
    if not IDEAS_DIR.is_absolute():
        IDEAS_DIR = Path(os.path.expanduser(str(IDEAS_DIR)))


def _slugify(text: str, max_len: int = 30) -> str:
    """將文字轉換為 URL-friendly slug"""
    text = text.strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text[:max_len].strip('-')


def _generate_filename(base: str) -> Path:
    """生成不衝突的檔案名"""
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    slug = _slugify(base)
    filename = f"{timestamp}-{slug}.txt"

    ideas_dir = get_ideas_dir()
    ideas_dir.mkdir(parents=True, exist_ok=True)

    filepath = ideas_dir / filename
    if filepath.exists():
        for i in range(1, 100):
            new_name = f"{timestamp}-{slug}-{i:02d}.txt"
            new_path = ideas_dir / new_name
            if not new_path.exists():
                return new_path
    return filepath


def main():
    parser = argparse.ArgumentParser(
        description="快速建立 Idea 檔",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例：
  clw_idea "今天突然想做個語音助手"
  clw_idea "優化登入流程" --desc "檢查 OAuth"
  clw_idea "新功能" --open      # 建立後用預設編輯器開啟
        """
    )
    parser.add_argument("idea", nargs="?", help="想法標題或內容")
    parser.add_argument("-d", "--desc", "--description", help="額外描述")
    parser.add_argument("-o", "--open", action="store_true", help="建立後用編輯器開啟")
    parser.add_argument("--ideas-dir", help="指定 Ideas 目錄（覆寫配置）")

    args = parser.parse_args()

    if not args.idea:
        parser.print_help()
        sys.exit(1)

    if args.ideas_dir:
        global get_ideas_dir
        ideas_dir = Path(args.ideas_dir).expanduser().resolve()
    else:
        ideas_dir = get_ideas_dir()

    ideas_dir.mkdir(parents=True, exist_ok=True)

    content = args.idea
    if args.desc:
        content = f"{args.idea}\n\n{args.desc}"

    filepath = _generate_filename(args.idea)
    filepath.write_text(content, encoding="utf-8")

    print(f"✅ 已建立: {filepath}")

    if args.open:
        editor = os.environ.get("EDITOR", "vim")
        os.system(f'{editor} "{filepath}"')


if __name__ == "__main__":
    main()