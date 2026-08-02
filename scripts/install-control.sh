#!/usr/bin/env bash
set -Eeuo pipefail
[[ $EUID -eq 0 ]] || { echo "Run with sudo"; exit 1; }
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
rm -rf /opt/old-iron-ai
install -d -m 0755 /opt/old-iron-ai
tar -C "$ROOT" --exclude=.git --exclude=.env --exclude=results --exclude=__pycache__ --exclude='*.pyc' -cf - . | tar -C /opt/old-iron-ai -xf -
install -m 0755 /opt/old-iron-ai/scripts/control.sh /usr/local/sbin/old-iron-control
install -d -m 0755 /var/lib/old-iron-ai
printf '%s\n' 'RESULT=OLD_IRON_CONTROL_INSTALLED' 'Use with sudo:' '  sudo old-iron-control start /absolute/path/.env /absolute/path/matrix.json'
