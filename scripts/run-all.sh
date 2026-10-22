#!/usr/bin/env bash
# Start the complete local demo: MCP API, integrated edge process, and web UI.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -x venv/bin/python ]]; then
  echo "[Libero] Virtualenv not found. Run scripts/setup.sh first."
  exit 1
fi
if ! command -v tmux >/dev/null 2>&1; then
  echo "[Libero] tmux is required. Install it or start the 3 services from README.md."
  exit 1
fi

start_service() {
  local session="$1"
  local command="$2"
  if tmux has-session -t "$session" 2>/dev/null; then
    echo "[Libero] Session $session is already running."
  else
    tmux new-session -d -s "$session" "cd '$ROOT' && source venv/bin/activate && exec $command"
    echo "[Libero] Started $session."
  fi
}

start_service libero-mcp "python cloud/mcp_server/server.py"
start_service libero-edge "python edge/main.py"
start_service libero-web "python -m http.server 3000 --directory interface/web"

echo "[Libero] Dashboard: http://localhost:3000/dashboard.html"
echo "[Libero] MCP endpoint: http://localhost:8080/mcp"
echo "[Libero] Edge status: http://localhost:8081/status"
echo "[Libero] Attach with: tmux attach -t libero-mcp (or libero-edge/libero-web)"
echo "[Libero] Stop with: tmux kill-session -t libero-mcp; repeat for libero-edge and libero-web."
