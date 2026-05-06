#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR/host/frontend"
npm run build

cd "$ROOT_DIR/host/backend"
python -m compileall ee_game_backend

echo "Release build complete. Frontend assets are in host/frontend/dist."
