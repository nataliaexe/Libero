#!/bin/bash
# Libero - Setup do ambiente

set -e

echo "[Libero] Configurando ambiente..."

# Sistema
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git curl wget tmux portaudio19-dev ffmpeg espeak-ng

# Virtualenv
python3 -m venv venv
source venv/bin/activate

# Dependências
pip install --upgrade pip
pip install boto3 fastapi 'uvicorn[standard]' python-dotenv pydantic groq
pip install openai-whisper sounddevice numpy scipy
pip install opencv-python mediapipe
pip install mcp
pip install pytest pytest-asyncio

echo "[Libero] Ambiente configurado."
echo "[Libero] Ative com: source venv/bin/activate"
