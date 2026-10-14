#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${STOCK_WATCH_ENV_FILE:-$ROOT_DIR/.env}"
ACTION="${1:-preview}"

case "$ACTION" in
  schema|preview|migrate|bootstrap) ;;
  *)
    echo "usage: $0 [schema|preview|migrate|bootstrap]" >&2
    exit 2
    ;;
esac

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "$ENV_FILE"
  set +a
fi

BACKEND_PORT="${STOCK_WATCH_PORT:-${BACKEND_PORT:-8117}}"
BRIDGE_PORT="${DEEPSEEK_WEB_BRIDGE_PORT:-8790}"
BRIDGE_CURL_AUTH_ARGS=()
if [[ -n "${DEEPSEEK_OPENAI_FACADE_API_KEY:-}" ]]; then
  BRIDGE_CURL_AUTH_ARGS=(-H "Authorization: Bearer ${DEEPSEEK_OPENAI_FACADE_API_KEY}")
fi

if [[ "$ACTION" == "migrate" || "$ACTION" == "bootstrap" ]]; then
  if lsof -nP -iTCP:"$BACKEND_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "refusing migration: backend port $BACKEND_PORT is still listening" >&2
    exit 1
  fi
  health="$(curl -fsS --max-time 5 "${BRIDGE_CURL_AUTH_ARGS[@]}" "http://127.0.0.1:${BRIDGE_PORT}/health")"
  printf '%s' "$health" | python3 -c '
import json, sys
payload = json.load(sys.stdin)
if not payload.get("ok") or payload.get("busy") or payload.get("activeRequest"):
    raise SystemExit("refusing migration: bridge is not idle")
'
fi

cd "$ROOT_DIR"
exec mvn -q org.codehaus.mojo:exec-maven-plugin:3.1.0:java \
  -Dexec.mainClass=com.aimeeting.room.StockWatchV6MigrationApplication \
  -Dexec.args="--spring.main.web-application-type=none --stock-watch.technical-analysis.v6-mode=migration --stock-watch.technical-analysis.v6-migration-action=${ACTION} --stock-watch.monitor.enabled=false --stock-watch.technical-analysis.enabled=false --stock-watch.delivery.enabled=false --stock-watch.prediction.evaluation-enabled=false --stock-watch.price-failure-research.enabled=false --ai.scheduling.enabled=false"
