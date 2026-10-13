#!/bin/bash
set -e
source venv/bin/activate
echo "[Libero] Testes unitários..."
pytest tests/unit/ -v
echo ""
echo "[Libero] Testes de integração..."
pytest tests/integration/ -v
echo ""
echo "[Libero] Todos os testes passaram."
