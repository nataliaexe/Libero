"""
Libero - Captura de Áudio
Captura áudio contínuo do microfone e salva em arquivo.
"""

import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import os

SAMPLE_RATE = 16000
CHANNELS = 1
DURATION = 5  # segundos
OUTPUT_DIR = "data/audio"


def garantir_diretorio():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def capturar_audio(duracao=DURATION, arquivo="captura.wav"):
    """Captura áudio do microfone e salva em arquivo."""
    garantir_diretorio()
    caminho = os.path.join(OUTPUT_DIR, arquivo)
    
    print(f"[Libero] Capturando áudio por {duracao}s...")
    audio = sd.rec(
        int(duracao * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype='int16'
    )
    sd.wait()
    write(caminho, SAMPLE_RATE, audio)
    print(f"[Libero] Áudio capturado: {caminho}")
    return caminho


if __name__ == "__main__":
    capturar_audio()
