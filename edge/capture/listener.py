"""
Libero - Listener de Áudio Contínuo
Transcrição via Groq Whisper (rápido e preciso) ou Whisper local (fallback).
"""

import os
import sys
import time
import threading
import numpy as np
import sounddevice as sd
from datetime import datetime, timezone
from scipy.io.wavfile import write
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Groq (preferido)
try:
    from groq import Groq
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_DISPONIVEL = bool(GROQ_API_KEY)
    _groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_DISPONIVEL else None
except ImportError:
    GROQ_DISPONIVEL = False
    _groq_client = None

# Whisper local (fallback)
try:
    import whisper
    WHISPER_DISPONIVEL = True
except ImportError:
    WHISPER_DISPONIVEL = False

# Configurações
SAMPLE_RATE = 16000
CHANNELS = 1
BLOCK_SIZE = 1024
SILENCIO_MAX = 1.2
DURACAO_MIN_FRASE = 0.4


class Listener:
    """
    Ouve microfone continuamente.
    Transcrição: Groq Whisper (rápido) > Whisper local (fallback).
    """
    
    def __init__(self, callback=None, modelo_whisper="tiny", threshold=None, dispositivo=None):
        self.callback = callback
        self.modelo_whisper = modelo_whisper
        self.modelo = None
        self.dispositivo = dispositivo
        
        self.threshold = threshold
        self.threshold_calibrado = False
        
        self.buffer_audio = []
        self.tempo_ultima_voz = None
        
        self.rodando = False
        self.thread = None
        
        self.frases_processadas = 0
        self.ultima_frase = None
        self.ultimo_timestamp = None
        self.nivel_atual = 0.0
        self.mostrar_nivel = False
        self.metodo_transcricao = "groq" if GROQ_DISPONIVEL else "whisper_local"
        
        if GROQ_DISPONIVEL:
            print(f"[Libero Listener] Groq Whisper ativo (modelo: whisper-large-v3-turbo)")
        elif WHISPER_DISPONIVEL:
            print(f"[Libero Listener] Groq não configurado — usando Whisper local '{modelo_whisper}'")
        else:
            print(f"[Libero Listener] AVISO: Nenhum método de transcrição disponível")
    
    def calibrar(self, duracao=2):
        """Calibra o threshold ouvindo o ruído ambiente."""
        print(f"[Libero Listener] Calibrando por {duracao}s. FIQUE EM SILÊNCIO...")
        
        amostras = []
        
        def callback_calibracao(indata, frames, time_info, status):
            energia = float(np.sqrt(np.mean(indata**2)))
            amostras.append(energia)
        
        try:
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                blocksize=BLOCK_SIZE,
                dtype='float32',
                callback=callback_calibracao,
                device=self.dispositivo
            ):
                time.sleep(duracao)
        except Exception as e:
            print(f"[Libero Listener] Erro na calibração: {e}")
            self.threshold = 0.02
            self.threshold_calibrado = True
            return
        
        if not amostras:
            self.threshold = 0.02
            self.threshold_calibrado = True
            return
        
        ruido_medio = float(np.mean(amostras))
        
        # Threshold 1.5x o ruído médio (sensível)
        self.threshold = max(ruido_medio * 1.5, 0.008)
        
        print(f"[Libero Listener] Ruído médio: {ruido_medio:.5f}")
        print(f"[Libero Listener] Threshold: {self.threshold:.5f}")
        print(f"[Libero Listener] Calibração OK")
        
        self.threshold_calibrado = True
    
    def _carregar_modelo_local(self):
        if not WHISPER_DISPONIVEL:
            return None
        if self.modelo is None:
            print(f"[Libero Listener] Carregando Whisper local '{self.modelo_whisper}'...")
            self.modelo = whisper.load_model(self.modelo_whisper)
            print("[Libero Listener] Whisper local carregado")
        return self.modelo
    
    def iniciar(self):
        if not self.threshold_calibrado:
            self.calibrar(duracao=2)
        
        self.rodando = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        print("[Libero Listener] Iniciado. Ouvindo microfone...")
    
    def parar(self):
        self.rodando = False
        if self.thread:
            self.thread.join(timeout=2)
        print("[Libero Listener] Parado")
    
    def _loop(self):
        def callback_audio(indata, frames, time_info, status):
            self._processar_bloco(indata.copy())
        
        try:
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                blocksize=BLOCK_SIZE,
                dtype='float32',
                callback=callback_audio,
                device=self.dispositivo
            ):
                while self.rodando:
                    time.sleep(0.1)
        except Exception as e:
            print(f"[Libero Listener] Erro: {e}")
            self.rodando = False
    
    def _processar_bloco(self, bloco):
        energia = float(np.sqrt(np.mean(bloco**2)))
        self.nivel_atual = energia
        
        if self.mostrar_nivel:
            barra = "█" * min(int(energia * 1000), 50)
            print(f"\r[Nível] {energia:.5f} {barra}", end="")
        
        agora = time.time()
        
        if energia > self.threshold:
            self.buffer_audio.append(bloco)
            self.tempo_ultima_voz = agora
        else:
            if self.buffer_audio and self.tempo_ultima_voz:
                silencio = agora - self.tempo_ultima_voz
                if silencio > SILENCIO_MAX:
                    self._fechar_frase()
    
    def _fechar_frase(self):
        if not self.buffer_audio:
            return
        
        audio = np.concatenate(self.buffer_audio)
        self.buffer_audio = []
        self.tempo_ultima_voz = None
        
        duracao = len(audio) / SAMPLE_RATE
        if duracao < DURACAO_MIN_FRASE:
            return
        
        threading.Thread(
            target=self._transcrever_e_emitir,
            args=(audio, duracao),
            daemon=True
        ).start()
    
    def _transcrever_e_emitir(self, audio, duracao):
        try:
            texto = self._transcrever(audio)
            
            if not texto or len(texto.strip()) < 2:
                return
            
            timestamp = datetime.now(timezone.utc).isoformat()
            self.frases_processadas += 1
            self.ultima_frase = texto
            self.ultimo_timestamp = timestamp
            
            print(f"\n[Libero Listener] 🎤 '{texto}' ({duracao:.1f}s)")
            
            if self.callback:
                self.callback({
                    "tipo": "voz",
                    "texto": texto,
                    "duracao": duracao,
                    "timestamp": timestamp,
                    "energia": float(np.sqrt(np.mean(audio**2))),
                    "metodo": self.metodo_transcricao
                })
        except Exception as e:
            print(f"[Libero Listener] Erro: {e}")
    
    def _transcrever(self, audio):
        """Transcreve áudio. Groq primeiro, Whisper local como fallback."""
        # Salvar WAV
        tmp_path = "/tmp/libero_audio.wav"
        write(tmp_path, SAMPLE_RATE, (audio * 32767).astype(np.int16))
        
        try:
            # 1. Tentar Groq
            if GROQ_DISPONIVEL and _groq_client:
                try:
                    with open(tmp_path, "rb") as f:
                        transcricao = _groq_client.audio.transcriptions.create(
                            file=("audio.wav", f.read()),
                            model="whisper-large-v3-turbo",
                            language="pt",
                            response_format="text"
                        )
                    
                    texto = transcricao.strip() if isinstance(transcricao, str) else transcricao.text.strip()
                    if texto:
                        return texto
                except Exception as e:
                    print(f"[Libero Listener] Groq falhou: {e}. Tentando Whisper local...")
            
            # 2. Fallback: Whisper local
            modelo = self._carregar_modelo_local()
            if modelo:
                resultado = modelo.transcribe(tmp_path, language="pt", fp16=False)
                return resultado["text"].strip()
            
            return f"[áudio: {len(audio)/SAMPLE_RATE:.1f}s]"
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass
    
    def status(self):
        return {
            "rodando": self.rodando,
            "threshold": self.threshold,
            "nivel_atual": self.nivel_atual,
            "frases_processadas": self.frases_processadas,
            "ultima_frase": self.ultima_frase,
            "ultimo_timestamp": self.ultimo_timestamp,
            "metodo": self.metodo_transcricao
        }


# ============================================================
# TESTE
# ============================================================

if __name__ == "__main__":
    def on_frase(evento):
        print(f"\n[Callback] '{evento['texto']}' (método: {evento.get('metodo')})\n")
    
    listener = Listener(callback=on_frase)
    listener.mostrar_nivel = True
    
    try:
        listener.iniciar()
        print("\n[Libero] Fale algo. Ctrl+C para parar.\n")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n[Libero] Parando...")
    finally:
        listener.parar()
