#!/bin/bash

# Script para iniciar o projeto Libero
# Uso: ./start.sh [backend|frontend|edge|all]

MODE=${1:-all}

echo "🚀 Iniciando Libero..."

if [ "$MODE" = "backend" ] || [ "$MODE" = "all" ]; then
    echo "📡 Iniciando Backend MCP Server..."
    cd ~/libero
    source venv/bin/activate
    pkill -f "cloud/mcp_server/server.py"
    sleep 1
    python cloud/mcp_server/server.py &
    BACKEND_PID=$!
    echo "✅ Backend rodando na porta 8080 (PID: $BACKEND_PID)"
fi

if [ "$MODE" = "frontend" ] || [ "$MODE" = "all" ]; then
    echo "🎨 Iniciando Frontend React..."
    cd ~/libero/frontend
    npm run dev &
    FRONTEND_PID=$!
    echo "✅ Frontend rodando na porta 3000 (PID: $FRONTEND_PID)"
fi

if [ "$MODE" = "edge" ] || [ "$MODE" = "all" ]; then
    echo "🎥 Iniciando Edge Service..."
    cd ~/libero
    source venv/bin/activate
    pkill -f "edge/main.py"
    sleep 1
    python edge/main.py &
    EDGE_PID=$!
    echo "✅ Edge Service rodando na porta 8081 (PID: $EDGE_PID)"
fi

if [ "$MODE" = "all" ]; then
    echo ""
    echo "🎉 Todos os serviços iniciados!"
    echo ""
    echo "📡 Backend: http://127.0.0.1:8080"
    echo "🎨 Frontend: http://localhost:3000/react-app.html"
    echo "🎥 Edge: http://127.0.0.1:8081"
    echo ""
    echo "Pressione Ctrl+C para parar todos os serviços"
    wait
fi
