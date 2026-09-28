#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
ENV_FILE="${STOCK_WATCH_ENV_FILE:-$ROOT/.env}"
if [[ -f "$ENV_FILE" ]]; then set -a; source "$ENV_FILE"; set +a; fi
node -e 'if (Number(process.versions.node.split(".")[0]) < 22) { console.error("Node.js 22+ is required (native fetch/WebSocket)"); process.exit(1) }'
export DEEPSEEK_WEB_BRIDGE_PORT="${DEEPSEEK_WEB_BRIDGE_PORT:-8790}"
export DEEPSEEK_WEB_DEBUG_PORT="${DEEPSEEK_WEB_DEBUG_PORT:-9334}"
export DEEPSEEK_WEB_PROFILE_ROOT="${DEEPSEEK_WEB_PROFILE_ROOT:-$HOME/.stock-watch/deepseek-web-profile}"
export DEEPSEEK_WEB_SESSION_STORE="${DEEPSEEK_WEB_SESSION_STORE:-$HOME/.stock-watch/deepseek-web-sessions.json}"
export DEEPSEEK_WEB_CHROME_LOG="${DEEPSEEK_WEB_CHROME_LOG:-$HOME/.stock-watch/deepseek-web-chrome.log}"
mkdir -p "$HOME/.stock-watch"
exec node scripts/deepseek-web-bridge.js
