"""
Libero - Voice Activity Detection
Detecta quando há voz no áudio contínuo.
"""

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
CHANNELS = 1
BLOCK_SIZE = 1024
THRESHOLD = 0.01


def detectar_voz(threshold=THRESHOLD):
    """Detecta voz em tempo real."""
    print(f"[Libero] Detectando voz... (threshold={threshold})")
    print("[Libero] Ctrl+C para parar.")
    
    try:
        while True:
            audio = sd.rec(
                BLOCK_SIZE,
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype='float32'
            )
            sd.wait()
            energia = np.sqrt(np.mean(audio**2))
            
            if energia > threshold:
                print(f"[Libero] Voz detectada! Energia: {energia:.4f}")
            else:
                print(f"[Libero] Silêncio. Energia: {energia:.4f}", end='\r')
    except KeyboardInterrupt:
        print("\n[Libero] Parando detecção.")


if __name__ == "__main__":
    detectar_voz()
