#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
chmod +x cron.sh setup.sh deploy.sh scripts/*.sh bot/fetch.py

"$DIR/scripts/install-cron.sh"
"$DIR/scripts/start-web.sh"

echo "Deploy concluído."
