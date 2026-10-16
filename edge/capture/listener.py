"""
Libero - Listener de Áudio Contínuo
Com filtro robusto contra falsos positivos.
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

try:
    from groq import Groq
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    _groq = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
except ImportError:
    _groq = None

try:
    import whisper
    WHISPER_DISPONIVEL = True
except ImportError:
    WHISPER_DISPONIVEL = False

# Configurações — mais rigorosas
SAMPLE_RATE = 16000
CHANNELS = 1
BLOCK_SIZE = 1024
SILENCIO_MAX = 1.5

# Filtros contra falso positivo
DURACAO_MIN_FRASE = 1.2        # era 0.4-0.8, agora 1.2s
ENERGIA_MIN_MEDIA = 0.06       # era 0.04, agora 0.06
ENERGIA_MIN_MAX = 0.20         # pico mínimo
BLOCOS_VOZ_MIN = 12            # era 8, agora 12 (~0.75s de fala contínua)
SNR_MIN = 3.0                  # sinal/ruído mínimo


class Listener:
    def __init__(self, callback=None, modelo_whisper="tiny", threshold=None, dispositivo=None):
        self.callback = callback
        self.modelo_whisper = modelo_whisper
        self.modelo = None
        self.dispositivo = dispositivo
        
        self.threshold = threshold
        self.threshold_calibrado = False
        self.ruido_base = 0.01
        
        self.buffer_audio = []
        self.tempo_ultima_voz = None
        self.blocos_voz = 0
        self.energia_max_buffer = 0.0
        
        self.rodando = False
        self.pausado = False
        self.thread = None
        
        self.frases_processadas = 0
        self.ultima_frase = None
        self.ultimo_timestamp = None
        self.nivel_atual = 0.0
        self.mostrar_nivel = False
        self.metodo_transcricao = "groq" if _groq else "whisper_local"
    
    def calibrar(self, duracao=3):
        """Calibra com threshold mais alto."""
        print(f"[Libero Listener] Calibrando por {duracao}s. FIQUE EM SILÊNCIO...")
        
        amostras = []
        
        def cb(indata, frames, time_info, status):
            amostras.append(float(np.sqrt(np.mean(indata**2))))
        
        try:
            with sd.InputStream(
                samplerate=SAMPLE_RATE, channels=CHANNELS,
                blocksize=BLOCK_SIZE, dtype='float32',
                callback=cb, device=self.dispositivo
            ):
                time.sleep(duracao)
        except Exception as e:
            print(f"[Libero Listener] Erro calibração: {e}")
            self.threshold = 0.10
            self.ruido_base = 0.02
            self.threshold_calibrado = True
            return
        
        if not amostras:
            self.threshold = 0.10
            self.ruido_base = 0.02
            self.threshold_calibrado = True
            return
        
        self.ruido_base = float(np.mean(amostras))
        ruido_std = float(np.std(amostras))
        pico_ruido = float(np.percentile(amostras, 99))
        
        # Threshold = max(ruído + 5σ, pico ruído × 2, mínimo absoluto)
        threshold_calculado = max(
            self.ruido_base + 5 * ruido_std,
            pico_ruido * 2,
            0.08   # mínimo absoluto alto
        )
        
        self.threshold = threshold_calculado
        
        print(f"[Libero Listener] Ruído base: {self.ruido_base:.5f}")
        print(f"[Libero Listener] Pico ruído: {pico_ruido:.5f}")
        print(f"[Libero Listener] Threshold: {self.threshold:.5f}")
        
        self.threshold_calibrado = True
    
    def iniciar(self):
        if not self.threshold_calibrado:
            self.calibrar(duracao=3)
        
        self.rodando = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        print("[Libero Listener] Iniciado. Ouvindo microfone...")
    
    def parar(self):
        self.rodando = False
        if self.thread:
            self.thread.join(timeout=2)
        print("[Libero Listener] Parado")
    
    def pausar(self):
        """Pausa durante a fala do Libero."""
        self.pausado = True
        self.buffer_audio = []
        self.tempo_ultima_voz = None
        self.blocos_voz = 0
        self.energia_max_buffer = 0.0
    
    def retomar(self):
        self.pausado = False
    
    def _loop(self):
        def cb(indata, frames, time_info, status):
            self._processar_bloco(indata.copy())
        
        try:
            with sd.InputStream(
                samplerate=SAMPLE_RATE, channels=CHANNELS,
                blocksize=BLOCK_SIZE, dtype='float32',
                callback=cb, device=self.dispositivo
            ):
                while self.rodando:
                    time.sleep(0.1)
        except Exception as e:
            print(f"[Libero Listener] Erro: {e}")
            self.rodando = False
    
    def _processar_bloco(self, bloco):
        if self.pausado:
            return
        
        energia = float(np.sqrt(np.mean(bloco**2)))
        self.nivel_atual = energia
        
        if self.mostrar_nivel:
            barra = "█" * min(int(energia * 500), 50)
            print(f"\r[Nível] {energia:.5f} {barra}", end="")
        
        agora = time.time()
        
        if energia > self.threshold:
            self.buffer_audio.append(bloco)
            self.tempo_ultima_voz = agora
            self.blocos_voz += 1
            self.energia_max_buffer = max(self.energia_max_buffer, energia)
        else:
            if self.buffer_audio and self.tempo_ultima_voz:
                if (agora - self.tempo_ultima_voz) > SILENCIO_MAX:
                    self._fechar_frase()
    
    def _fechar_frase(self):
        """Fecha frase APENAS se passa pelos filtros."""
        # FILTRO 1: blocos mínimos
        if self.blocos_voz < BLOCOS_VOZ_MIN:
            print(f"[Libero Listener] Ignorado: só {self.blocos_voz} blocos")
            self._reset()
            return
        
        if not self.buffer_audio:
            self._reset()
            return
        
        audio = np.concatenate(self.buffer_audio)
        duracao = len(audio) / SAMPLE_RATE
        
        # FILTRO 2: duração mínima
        if duracao < DURACAO_MIN_FRASE:
            print(f"[Libero Listener] Ignorado: {duracao:.1f}s < {DURACAO_MIN_FRASE}s")
            self._reset()
            return
        
        # FILTRO 3: energia média
        energia_media = float(np.sqrt(np.mean(audio**2)))
        if energia_media < ENERGIA_MIN_MEDIA:
            print(f"[Libero Listener] Ignorado: energia média {energia_media:.4f}")
            self._reset()
            return
        
        # FILTRO 4: pico mínimo
        energia_max = float(np.max(np.abs(audio)))
        if energia_max < ENERGIA_MIN_MAX:
            print(f"[Libero Listener] Ignorado: pico {energia_max:.4f}")
            self._reset()
            return
        
        # FILTRO 5: SNR (sinal vs ruído)
        snr = energia_media / max(self.ruido_base, 0.001)
        if snr < SNR_MIN:
            print(f"[Libero Listener] Ignorado: SNR {snr:.1f}")
            self._reset()
            return
        
        # PASSOU POR TODOS OS FILTROS
        self._reset()
        
        threading.Thread(
            target=self._transcrever_e_emitir,
            args=(audio, duracao),
            daemon=True
        ).start()
    
    def _reset(self):
        self.buffer_audio = []
        self.tempo_ultima_voz = None
        self.blocos_voz = 0
        self.energia_max_buffer = 0.0
    
    def _transcrever_e_emitir(self, audio, duracao):
        try:
            texto = self._transcrever(audio)
            
            if not texto or len(texto.strip()) < 3:
                return
            
            # FILTRO 6: bloquear alucinações conhecidas do Whisper
            alucinacoes = [
                "e aí", "tchau", "obrigado", "obrigada",
                "legenda", "amara.org", "www.", ".com",
                "inscreva", "curta", "compartilhe"
            ]
            texto_lower = texto.lower().strip()
            
            # Se for apenas uma alucinação curta, ignora
            if len(texto) < 8 and any(a in texto_lower for a in alucinacoes):
                print(f"[Libero Listener] Alucinação bloqueada: '{texto}'")
                return
            
            timestamp = datetime.now(timezone.utc).isoformat()
            self.frases_processadas += 1
            self.ultima_frase = texto
            self.ultimo_timestamp = timestamp
            
            print(f"\n[Libero Listener] 🎤 '{texto}' ({duracao:.1f}s, SNR ok)")
            
            if self.callback:
                self.callback({
                    "tipo": "voz",
                    "texto": texto,
                    "duracao": duracao,
                    "timestamp": timestamp,
                    "metodo": self.metodo_transcricao
                })
        except Exception as e:
            print(f"[Libero Listener] Erro: {e}")
    
    def _transcrever(self, audio):
        tmp_path = "/tmp/libero_audio.wav"
        write(tmp_path, SAMPLE_RATE, (audio * 32767).astype(np.int16))
        
        try:
            if _groq:
                try:
                    with open(tmp_path, "rb") as f:
                        t = _groq.audio.transcriptions.create(
                            file=("audio.wav", f.read()),
                            model="whisper-large-v3-turbo",
                            language="pt",
                            response_format="text",
                            temperature=0.0  # menos alucinação
                        )
                    texto = t.strip() if isinstance(t, str) else t.text.strip()
                    if texto:
                        return texto
                except Exception as e:
                    print(f"[Libero Listener] Groq falhou: {e}")
            
            if WHISPER_DISPONIVEL:
                if self.modelo is None:
                    self.modelo = whisper.load_model(self.modelo_whisper)
                r = self.modelo.transcribe(tmp_path, language="pt", fp16=False)
                return r["text"].strip()
            
            return ""
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass
    
    def status(self):
        return {
            "rodando": self.rodando,
            "threshold": self.threshold,
            "ruido_base": self.ruido_base,
            "nivel_atual": self.nivel_atual,
            "frases_processadas": self.frases_processadas,
            "ultima_frase": self.ultima_frase,
            "ultimo_timestamp": self.ultimo_timestamp,
            "metodo": self.metodo_transcricao
        }


if __name__ == "__main__":
    def on_frase(e):
        print(f"\n[Callback] '{e['texto']}'\n")
    
    l = Listener(callback=on_frase)
    l.mostrar_nivel = True
    
    try:
        l.iniciar()
        print("\n[Libero] Fique em silêncio 30s. Nada deve aparecer.")
        print("[Libero] Depois fale algo. Ctrl+C para parar.\n")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Libero] Parando...")
    finally:
        l.parar()
