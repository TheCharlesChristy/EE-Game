#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${EE_GAME_URL:-http://127.0.0.1:8000}"

curl -fsS "$BASE_URL/health" >/dev/null
curl -fsS "$BASE_URL/api/diagnostics" >/dev/null
curl -fsS "$BASE_URL/api/games" >/dev/null

SESSION_JSON="$(curl -sS -X POST "$BASE_URL/api/sessions")"
if [[ "$SESSION_JSON" != *"session_id"* && "$SESSION_JSON" != *"already exists"* ]]; then
  echo "Session create/resume smoke check did not return expected payload." >&2
  exit 1
fi

echo "Smoke test passed for $BASE_URL"
