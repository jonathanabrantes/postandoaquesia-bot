#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

LOG_DIR="$DIR/logs"
mkdir -p "$LOG_DIR"

LOG_FILE="$LOG_DIR/fetch.log"

if [ -d "$DIR/.venv" ]; then
  PYTHON="$DIR/.venv/bin/python3"
else
  PYTHON="python3"
fi

"$PYTHON" "$DIR/bot/fetch.py" >> "$LOG_FILE" 2>&1
