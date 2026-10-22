#!/usr/bin/env bash
# Backward-compatible entry point for the complete local demo.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/run-all.sh" "$@"
