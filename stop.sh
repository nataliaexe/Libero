#!/bin/bash

# Script para parar todos os serviços do Libero

echo "🛑 Parando serviços do Libero..."

pkill -f "cloud/mcp_server/server.py"
echo "✅ Backend MCP Server parado"

pkill -f "edge/main.py"
echo "✅ Edge Service parado"

pkill -f "python3 -m http.server 3000"
echo "✅ Frontend HTTP server parado"

echo ""
echo "🎉 Todos os serviços parados!"
