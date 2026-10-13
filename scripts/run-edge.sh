#!/bin/bash
# Libero - Roda o Edge (captura)

set -e
source venv/bin/activate

echo "[Libero] Iniciando captura de áudio..."
python edge/capture/audio.py

echo "[Libero] Iniciando detecção de voz..."
python edge/capture/vad.py
