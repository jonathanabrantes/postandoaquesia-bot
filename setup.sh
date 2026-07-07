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
chmod +x cron.sh bot/fetch.py web/app.py setup.sh

echo "Setup concluído."
echo ""
echo "Para instalar o cron (a cada minuto):"
echo "  (crontab -l 2>/dev/null; echo '* * * * * $DIR/cron.sh') | crontab -"
echo ""
echo "Para iniciar o frontend:"
echo "  $DIR/.venv/bin/python3 $DIR/web/app.py"
echo ""
echo "Para testar o bot manualmente:"
echo "  $DIR/cron.sh"
