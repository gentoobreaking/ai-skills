#!/usr/bin/env python3
"""
ideas2tasks config.py
配置管理：支援 .env 檔案 + 環境變數覆蓋 + 預設值

優先順序（從低到高）：
1. 硬編碼預設值
2. .env 檔案
3. 環境變數（最高優先）
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

_SCRIPT_DIR = Path(__file__).parent.resolve()
_DEFAULT_ENV_FILE = _SCRIPT_DIR.parent / ".env"

_config: dict[str, str] = {}


def _load_env_file(env_file: Path) -> dict[str, str]:
    """載入 .env 檔案，回傳 key-value dict。"""
    result = {}
    if not env_file.exists():
        return result
    try:
        content = env_file.read_text(encoding="utf-8")
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                result[key.strip()] = val.strip()
    except Exception:
        pass
    return result


def init(env_file: Optional[Path] = None):
    """初始化配置。呼叫一次即可。"""
    global _config

    env_path = env_file or _DEFAULT_ENV_FILE
    file_config = _load_env_file(env_path)

    _config = {}
    for key, default_val in _DEFAULTS.items():
        env_val = os.environ.get(key)
        file_val = file_config.get(key)
        if env_val is not None:
            _config[key] = env_val
        elif file_val is not None:
            _config[key] = file_val
        else:
            _config[key] = default_val


_DEFAULTS = {
    "IDEAS2TASKS_TASKS_DIR": "~/Tasks",
    "IDEAS2TASKS_IDEAS_DIR": "~/Ideas",
    "IDEAS2TASKS_GITHUB_REPO": "",
    "IDEAS2TASKS_GITHUB_TOKEN": "",
}


def get(key: str, default: Optional[str] = None) -> str:
    """取得配置值。"""
    if not _config:
        init()
    return _config.get(key, default or _DEFAULTS.get(key, ""))


def get_tasks_dir() -> Path:
    """取得 Tasks 目錄路徑。"""
    return Path(os.path.expanduser(get("IDEAS2TASKS_TASKS_DIR"))).resolve()


def get_ideas_dir() -> Path:
    """取得 Ideas 目錄路徑。"""
    return Path(os.path.expanduser(get("IDEAS2TASKS_IDEAS_DIR"))).resolve()


def get_github_repo() -> str:
    """取得 GitHub 倉庫。"""
    return get("IDEAS2TASKS_GITHUB_REPO")


def get_github_token() -> str:
    """取得 GitHub Token。"""
    return get("IDEAS2TASKS_GITHUB_TOKEN")


if __name__ == "__main__":
    init()
    print("IDEAS2TASKS_TASKS_DIR:", get("IDEAS2TASKS_TASKS_DIR"))
    print("IDEAS2TASKS_IDEAS_DIR:", get("IDEAS2TASKS_IDEAS_DIR"))
    print("IDEAS2TASKS_GITHUB_REPO:", get("IDEAS2TASKS_GITHUB_REPO"))