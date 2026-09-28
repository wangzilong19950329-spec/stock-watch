#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/frontend"
command -v npm >/dev/null || { echo "Install Node.js 22+" >&2; exit 1; }
if [[ ! -d node_modules ]]; then npm ci; fi
exec npm run dev
