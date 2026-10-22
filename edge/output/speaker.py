"""
Libero - Voz do Libero
Prioridade: Polly > Piper > espeak > silêncio
"""

import os
import sys
import subprocess
import tempfile
from datetime import datetime, timezone

try:
    import boto3
    from dotenv import load_dotenv
    load_dotenv()
    POLLY_DISPONIVEL = True
except ImportError:
    POLLY_DISPONIVEL = False

REGION = os.getenv("AWS_REGION", "us-east-1") if POLLY_DISPONIVEL else None
DEFAULT_LANGUAGE = os.getenv("LIBERO_DEFAULT_LANGUAGE", "en").lower()
VOICE_PT = os.getenv("POLLY_VOICE_PT", os.getenv("POLLY_VOICE", "Camila"))
VOICE_EN = os.getenv("POLLY_VOICE_EN", "Joanna")
PIPER_MODEL_PT = os.path.expanduser(os.getenv(
    "PIPER_MODEL_PT", "~/libero/models/piper/pt_BR-faber-medium.onnx"
))
PIPER_MODEL_EN = os.path.expanduser(os.getenv(
    "PIPER_MODEL_EN", "~/libero/models/piper/en_US-lessac-medium.onnx"
))
PIPER_MODEL = PIPER_MODEL_PT  # backward-compatible alias

_polly = None


def _get_polly():
    global _polly
    if _polly is None and POLLY_DISPONIVEL:
        try:
            _polly = boto3.client("polly", region_name=REGION)
        except Exception:
            _polly = False
    return _polly


def falar(texto, voz=None, language=None):
    """Speak in the same language as the current turn, with verified fallback status."""
    if not texto:
        return {"status": "vazio", "metodo": "none"}

    language = (language or DEFAULT_LANGUAGE).lower()
    is_english = language.startswith("en") or language == "english"
    locale = "en-US" if is_english else "pt-BR"
    voz = voz or (VOICE_EN if is_english else VOICE_PT)
    piper_model = PIPER_MODEL_EN if is_english else PIPER_MODEL_PT
    espeak_voice = "en-us" if is_english else "pt-br"
    
    # 1. Polly
    polly = _get_polly()
    if polly:
        try:
            response = polly.synthesize_speech(
                Text=texto, OutputFormat="mp3", VoiceId=voz, LanguageCode=locale
            )
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                f.write(response["AudioStream"].read())
                tmp_path = f.name
            tocou = _tocar_arquivo(tmp_path)
            try:
                os.remove(tmp_path)
            except Exception:
                pass
            if tocou:
                return {"status": "ok", "metodo": "polly", "texto": texto}
            print("[Libero Voz] Polly gerou áudio, mas não há player compatível.")
        except Exception as e:
            print(f"[Libero Voz] Polly falhou: {e}")
    
    # 2. Piper (voz natural offline)
    if os.path.exists(piper_model) and _tem_piper():
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                tmp_path = f.name
            
            # Piper gera WAV
            proc = subprocess.run(
                ["piper", "--model", piper_model, "--output_file", tmp_path],
                input=texto.encode(),
                capture_output=True,
                timeout=30
            )
            
            if proc.returncode == 0:
                tocou = _tocar_arquivo(tmp_path)
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
                if tocou:
                    return {"status": "ok", "metodo": "piper", "texto": texto}
        except Exception as e:
            print(f"[Libero Voz] Piper falhou: {e}")
    
    # 3. espeak (fallback)
    if _tem_espeak():
        try:
            proc = subprocess.Popen(
                ["espeak-ng", "-v", espeak_voice, "-s", "140", texto],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            proc.wait(timeout=30)
            if proc.returncode == 0:
                return {"status": "ok", "metodo": "espeak", "texto": texto}
        except Exception as e:
            print(f"[Libero Voz] espeak falhou: {e}")
    
    print(f"[Libero Voz] (sem áudio) {texto}")
    return {"status": "sem_tts", "metodo": "none", "texto": texto}


def _tocar_arquivo(path):
    players = [
        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path],
        ["aplay", "-q", path],
        ["paplay", path],
        ["mpg123", "-q", path],
    ]
    for cmd in players:
        try:
            subprocess.run(cmd, check=True, timeout=60, capture_output=True)
            return True
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
            continue
    return False


def _tem_piper():
    try:
        subprocess.run(["which", "piper"], check=True, capture_output=True)
        return True
    except Exception:
        return False


def _tem_espeak():
    try:
        subprocess.run(["which", "espeak-ng"], check=True, capture_output=True)
        return True
    except Exception:
        return False


def listar_vozes():
    polly = _get_polly()
    if not polly:
        return []
    try:
        response = polly.describe_voices(LanguageCode="en-US")
        return [v["Id"] for v in response["Voices"]]
    except Exception:
        return []


if __name__ == "__main__":
    vozes = listar_vozes()
    if vozes:
        print(f"[Libero Voz] Vozes Polly: {vozes}")
    
    if os.path.exists(PIPER_MODEL):
        print(f"[Libero Voz] Piper: {PIPER_MODEL}")
    else:
        print(f"[Libero Voz] Piper não configurado")
    
    testes = [
        "Olá, Dona Maria. Bom dia!",
        "Está na hora do remédio da pressão.",
    ]
    
    for texto in testes:
        print(f"\n[Falando] {texto}")
        r = falar(texto)
        print(f"[Resultado] {r['status']} ({r['metodo']})")
