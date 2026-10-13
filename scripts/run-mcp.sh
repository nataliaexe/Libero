#!/bin/bash
set -e
source venv/bin/activate
echo "[Libero] Iniciando MCP Server..."
python cloud/mcp_server/server.py
