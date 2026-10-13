"""
Libero - Extração de Features
Extrai features do áudio: tom, ritmo, volume.
"""

import numpy as np


def extrair_features(audio, sample_rate=16000):
    """
    Extrai features do áudio.
    
    Retorna:
        dict com:
        - energia_media: volume médio
        - energia_max: volume máximo
        - zcr: zero crossing rate (ritmo)
        - duracao: duração em segundos
    """
    if len(audio.shape) > 1:
        audio = audio.mean(axis=1)
    
    energia = np.sqrt(np.mean(audio**2))
    energia_max = np.max(np.abs(audio))
    zcr = np.mean(np.abs(np.diff(np.sign(audio)))) / 2
    duracao = len(audio) / sample_rate
    
    return {
        "energia_media": float(energia),
        "energia_max": float(energia_max),
        "zcr": float(zcr),
        "duracao": float(duracao),
    }


def classificar_tom(features):
    """Classifica o tom da voz."""
    energia = features["energia_media"]
    zcr = features["zcr"]
    
    if energia > 0.1 and zcr > 0.1:
        return "agitado"
    elif energia < 0.01:
        return "sussurro"
    elif zcr > 0.15:
        return "acelerado"
    else:
        return "calmo"


if __name__ == "__main__":
    import sounddevice as sd
    audio = sd.rec(16000, samplerate=16000, channels=1, dtype='float32')
    sd.wait()
    features = extrair_features(audio)
    print(f"[Libero] Features: {features}")
    print(f"[Libero] Tom: {classificar_tom(features)}")
