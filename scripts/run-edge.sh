#!/usr/bin/env bash
# Run the integrated edge process (microphone, optional camera, and speech output).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
if [[ ! -x venv/bin/python ]]; then
  echo "[Libero] Virtualenv not found. Run scripts/setup.sh first."
  exit 1
fi
exec venv/bin/python edge/main.py
