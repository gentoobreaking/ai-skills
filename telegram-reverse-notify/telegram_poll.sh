#!/usr/bin/env bash
#
# telegram_poll.sh - Shell wrapper for telegram_poll.py
#
# Usage:
#   ./telegram_poll.sh check    # 單次輪詢，輸出新訊息（供 Agent 讀取）
#   ./telegram_poll.sh poll     # 持續輪詢（背景監聽）
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python3}"

exec "$PYTHON" "$SCRIPT_DIR/telegram_poll.py" "$@"
