#!/bin/bash
# Libero - Roda o caminho crítico

set -e

source venv/bin/activate

echo "[Libero] Iniciando caminho crítico..."

# Terminal 1: MCP Server
tmux new-session -d -s libero-mcp "python cloud/mcp_server/server.py"

# Terminal 2: Captura
tmux new-session -d -s libero-capture "python edge/capture/audio.py"

# Terminal 3: VAD
tmux new-session -d -s libero-vad "python edge/capture/vad.py"

echo "[Libero] Rodando. Anexe com: tmux attach -t libero-mcp"
