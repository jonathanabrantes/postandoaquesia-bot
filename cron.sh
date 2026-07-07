#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

LOG_DIR="$DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/fetch.log"

export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin"
export CHROME_BIN="/usr/bin/chromium-browser"
export CHROMEDRIVER="/usr/bin/chromedriver"

if [ -d "$DIR/.venv" ]; then
  PYTHON="$DIR/.venv/bin/python3"
else
  PYTHON="python3"
fi

log() { echo "[$(date -Iseconds)] $*" >> "$LOG_FILE"; }

if ! "$PYTHON" "$DIR/bot/fetch.py" >> "$LOG_FILE" 2>&1; then
  log "ERRO: fetch falhou"
  exit 1
fi

if ! git diff --quiet data/followers.csv 2>/dev/null; then
  git add data/followers.csv
  git commit -m "chore(bot): atualiza followers.csv" >> "$LOG_FILE" 2>&1
  git push origin main >> "$LOG_FILE" 2>&1
  log "CSV commitado e enviado"
else
  log "CSV sem alterações"
fi
