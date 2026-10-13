#!/bin/bash
# Libero - Roda tudo (MCP + Edge)

set -e
source venv/bin/activate

echo "[Libero] Iniciando sistema completo..."

tmux new-session -d -s libero-mcp "source venv/bin/activate && python cloud/mcp_server/server.py"
tmux new-session -d -s libero-edge "source venv/bin/activate && python edge/capture/vad.py"

echo "[Libero] Rodando. Anexe com:"
echo "  tmux attach -t libero-mcp"
echo "  tmux attach -t libero-edge"
