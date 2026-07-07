#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CRON_LINE="* * * * * $DIR/cron.sh"

(crontab -l 2>/dev/null | grep -v "$DIR/cron.sh"; echo "$CRON_LINE") | crontab -
echo "Cron instalado: $CRON_LINE"
