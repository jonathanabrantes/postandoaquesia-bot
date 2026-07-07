#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

mkdir -p logs

if [ -d "$DIR/.venv" ]; then
  PYTHON="$DIR/.venv/bin/python3"
else
  PYTHON="python3"
fi

pkill -f "$DIR/web/app.py" 2>/dev/null || true
nohup "$PYTHON" "$DIR/web/app.py" >> "$DIR/logs/web.log" 2>&1 &
echo "Web iniciado em http://localhost:8787 (pid $!)"
