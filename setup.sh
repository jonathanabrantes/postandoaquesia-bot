#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

if ! command -v chromium-browser &>/dev/null && ! command -v chromium &>/dev/null; then
  echo "Instalando Chromium..."
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y chromium-browser chromium-chromedriver
fi

python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
chmod +x cron.sh bot/fetch.py setup.sh

CRON_LINE="* * * * * $DIR/cron.sh"
(crontab -l 2>/dev/null | grep -v "$DIR/cron.sh"; echo "$CRON_LINE") | crontab -

echo "Setup concluído. Cron: $CRON_LINE"
