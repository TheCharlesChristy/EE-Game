#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_DIR="${EE_GAME_INSTALL_DIR:-/opt/ee-game}"

sudo mkdir -p "$INSTALL_DIR"
sudo rsync -a --delete "$ROOT_DIR/" "$INSTALL_DIR/"
sudo install -m 0644 "$ROOT_DIR/docs/deployment/ee-game.service" /etc/systemd/system/ee-game.service
sudo systemctl daemon-reload
sudo systemctl enable ee-game.service

echo "Installed EE-Game to $INSTALL_DIR. Start with: sudo systemctl start ee-game"
