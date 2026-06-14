"""
sinotrade_scraper/config.py - 配置管理模組
支援環境變數 + 預設值
"""

import os
from pathlib import Path

# 預設值
DEFAULT_CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
DEFAULT_HISTORY_FILE = "~/.sinotrade_history.json"
DEFAULT_BASE_URL = "https://scm.sinotrade.com.tw/"


def get_chrome_path():
    """取得 Chrome 可執行檔路徑"""
    return os.environ.get("SINOTRADE_CHROME_PATH", DEFAULT_CHROME_PATH)


def get_history_file():
    """取得歷史記錄檔路徑"""
    env = os.environ.get("SINOTRADE_HISTORY_FILE")
    return env if env else str(Path(DEFAULT_HISTORY_FILE).expanduser())


def get_base_url():
    """取得基礎 URL"""
    return os.environ.get("SINOTRADE_BASE_URL", DEFAULT_BASE_URL)


def get_config():
    """取得完整配置"""
    return {
        "chrome_path": get_chrome_path(),
        "history_file": get_history_file(),
        "base_url": get_base_url(),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(get_config(), indent=2, ensure_ascii=False))
