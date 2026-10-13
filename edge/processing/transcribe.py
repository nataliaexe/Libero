"""
Libero - Transcrição
Transcreve áudio usando Whisper (local, privado).
"""

import whisper
import os

MODEL_NAME = os.getenv("WHISPER_MODEL", "tiny")
_model = None


def carregar_modelo():
    """Carrega o modelo Whisper (lazy)."""
    global _model
    if _model is None:
        print(f"[Libero] Carregando modelo Whisper: {MODEL_NAME}")
        _model = whisper.load_model(MODEL_NAME)
    return _model


def transcrever(arquivo):
    """Transcreve um arquivo de áudio."""
    if not os.path.exists(arquivo):
        raise FileNotFoundError(f"Arquivo não encontrado: {arquivo}")
    
    modelo = carregar_modelo()
    print(f"[Libero] Transcrevendo: {arquivo}")
    resultado = modelo.transcribe(arquivo, language="pt")
    texto = resultado["text"].strip()
    print(f"[Libero] Texto: {texto}")
    return texto


if __name__ == "__main__":
    import sys
    arquivo = sys.argv[1] if len(sys.argv) > 1 else "data/audio/captura.wav"
    transcrever(arquivo)
