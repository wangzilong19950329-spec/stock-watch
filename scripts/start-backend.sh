#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
ENV_FILE="${STOCK_WATCH_ENV_FILE:-$ROOT/.env}"
if [[ -f "$ENV_FILE" ]]; then set -a; source "$ENV_FILE"; set +a; fi
command -v java >/dev/null || { echo "Install Java 11+" >&2; exit 1; }
command -v mvn >/dev/null || { echo "Install Maven 3.8+" >&2; exit 1; }
mkdir -p "${STOCK_WATCH_DATA_DIR:-./data}"
exec mvn spring-boot:run
