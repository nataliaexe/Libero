"""
Libero - Listener de Áudio Contínuo
Com filtro robusto contra falsos positivos.
"""

import os
import sys
import time
import threading
import re
import tempfile
import unicodedata
from math import gcd
import numpy as np
from scipy.signal import resample_poly
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
SILENCIO_MAX = 3.0
JANELA_MERGE_VOZ = 0.8
LIMIAR_SOM_ALTO = 0.99  # energia para considerar som alto
LIMIAR_GRITO = 0.99     # energia + zcr alto = grito    # era 1.5, agora 3.0 (Linux com PipeWire tem latência)
MAX_THRESHOLD = 0.08   # cap to avoid requiring an unusually loud voice

# Filtros contra falso positivo
DURACAO_MIN_FRASE = 0.18
ENERGIA_MIN_MEDIA = 0.008
ENERGIA_MIN_MAX = 0.025
# Palavras críticas que ignoram filtros (emergência)
PALAVRAS_CRITICAS = [
    "socorro", "ajuda", "ajudar", "cai", "caiu", "caí",
    "me ajuda", "me ajudem", "dor", "machuquei", "sangue",
    "quebrei", "nao consigo"
]

BLOCOS_VOZ_MIN = 2
SNR_MIN = 1.5
SPEECH_LANGUAGE = os.getenv("LIBERO_SPEECH_LANGUAGE", "auto").strip().lower()
DEFAULT_LANGUAGE = os.getenv("LIBERO_DEFAULT_LANGUAGE", "en").strip().lower()
AUDIO_INPUT_DEVICE = os.getenv("LIBERO_AUDIO_INPUT_DEVICE", "").strip()

# PortAudio initialization can block on hosts with an unavailable audio backend.
# Keep it out of module import and perform it on the listener's daemon thread.
sd = None
_sounddevice_lock = threading.Lock()


def _get_sounddevice():
    global sd
    if sd is None:
        with _sounddevice_lock:
            if sd is None:
                import sounddevice
                sd = sounddevice
    return sd


def _parse_audio_device(value):
    """Accept a PortAudio index or a device name from the local environment."""
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return value


def _supported_input_rate(device):
    """Use 16 kHz when supported, otherwise capture at the device's native rate."""
    sounddevice = _get_sounddevice()
    try:
        sounddevice.check_input_settings(
            device=device, channels=CHANNELS, samplerate=SAMPLE_RATE, dtype="float32"
        )
        return SAMPLE_RATE
    except Exception:
        info = sounddevice.query_devices(device, "input")
        native_rate = round(float(info["default_samplerate"]))
        sounddevice.check_input_settings(
            device=device, channels=CHANNELS, samplerate=native_rate, dtype="float32"
        )
        print(
            f"[Libero Listener] O dispositivo não aceita {SAMPLE_RATE} Hz; "
            f"capturando a {native_rate} Hz e convertendo para {SAMPLE_RATE} Hz."
        )
        return native_rate


def _normalizar_idioma(language, fallback=None):
    language = (language or "").strip().lower().replace("_", "-")
    if language.startswith("en") or language in {"english", "inglês", "ingles"}:
        return "en"
    if language.startswith("pt") or language in {"portuguese", "portugues", "português"}:
        return "pt-BR"
    if language:
        return None
    fallback = (fallback or DEFAULT_LANGUAGE).lower()
    return "pt-BR" if fallback.startswith("pt") else "en"


def _transcricao_plausivel(texto, duracao):
    """Reject ASR hallucinations that contain far more words than the clip can hold."""
    palavras = re.findall(r"[\w]+(?:['’][\w]+)*", texto, flags=re.UNICODE)
    limite = max(5, int(max(duracao, 0) * 6) + 2)
    return len(palavras) <= limite


class Listener:
    def __init__(self, callback=None, modelo_whisper="tiny", threshold=None, dispositivo=None):
        self.callback = callback
        self.modelo_whisper = modelo_whisper
        self.modelo = None
        self.dispositivo = dispositivo if dispositivo is not None else _parse_audio_device(AUDIO_INPUT_DEVICE)
        self.input_sample_rate = SAMPLE_RATE
        
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
        self.metodo_transcricao = (
            "groq" if _groq else "whisper_local" if WHISPER_DISPONIVEL else "indisponivel"
        )
        self.ultimo_idioma = _normalizar_idioma(None)
        self.ultimo_erro_transcricao = None
        self._transcription_lock = threading.Lock()
        self.estado_microfone = "parado"
    
    def calibrar(self, duracao=3):
        """Calibra com threshold mais alto."""
        print(f"[Libero Listener] Calibrando por {duracao}s. FIQUE EM SILÊNCIO...")
        
        amostras = []
        
        def cb(indata, frames, time_info, status):
            amostras.append(float(np.sqrt(np.mean(indata**2))))
        
        try:
            with _get_sounddevice().InputStream(
                samplerate=self.input_sample_rate, channels=CHANNELS,
                blocksize=BLOCK_SIZE, dtype='float32',
                callback=cb, device=self.dispositivo
            ):
                time.sleep(duracao)
        except Exception as e:
            print(f"[Libero Listener] Erro calibração: {e}")
            self.threshold = 0.02
            self.ruido_base = 0.02
            self.threshold_calibrado = True
            return
        
        if not amostras:
            self.threshold = 0.02
            self.ruido_base = 0.02
            self.threshold_calibrado = True
            return
        
        self.ruido_base = float(np.mean(amostras))
        ruido_std = float(np.std(amostras))
        pico_ruido = float(np.percentile(amostras, 99))
        
        # Use an adaptive low floor so ordinary speech isn't lost at normal mic levels.
        threshold_calculado = max(
            self.ruido_base + 3 * ruido_std,
            pico_ruido * 1.4,
            0.008,
        )
        
        self.threshold = min(threshold_calculado, MAX_THRESHOLD)
        
        print(f"[Libero Listener] Ruído base: {self.ruido_base:.5f}")
        print(f"[Libero Listener] Pico ruído: {pico_ruido:.5f}")
        print(f"[Libero Listener] Threshold: {self.threshold:.5f}")
        
        self.threshold_calibrado = True
    
    def iniciar(self):
        if self.rodando:
            return
        if self.thread and self.thread.is_alive():
            print("[Libero Listener] Inicialização anterior ainda está bloqueada; reinicie o processo edge após corrigir o dispositivo.")
            return
        self.rodando = True
        self.estado_microfone = "inicializando"
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        threading.Thread(target=self._vigiar_inicializacao, daemon=True).start()
        print("[Libero Listener] Inicializando microfone em segundo plano...")

    def _vigiar_inicializacao(self):
        time.sleep(15)
        if self.rodando and self.estado_microfone == "inicializando":
            self.estado_microfone = "travado"
            self.rodando = False
            self.ultimo_erro_transcricao = (
                "Inicialização do PortAudio excedeu 15s; verifique o dispositivo "
                "e o backend de áudio do sistema."
            )
            print(f"[Libero Listener] {self.ultimo_erro_transcricao}")
    
    def parar(self):
        self.rodando = False
        self.estado_microfone = "parado"
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
            bloco = indata[:, 0]
            if self.input_sample_rate != SAMPLE_RATE:
                divisor = gcd(self.input_sample_rate, SAMPLE_RATE)
                bloco = resample_poly(
                    bloco, SAMPLE_RATE // divisor, self.input_sample_rate // divisor
                ).astype(np.float32, copy=False)
            else:
                bloco = bloco.copy()
            self._processar_bloco(bloco)
        
        try:
            _get_sounddevice()
            if not self.rodando:
                return
            self.input_sample_rate = _supported_input_rate(self.dispositivo)
            if not self.threshold_calibrado:
                self.calibrar(duracao=3)
            if not self.rodando:
                return
            with _get_sounddevice().InputStream(
                samplerate=self.input_sample_rate, channels=CHANNELS,
                blocksize=BLOCK_SIZE, dtype='float32',
                callback=cb, device=self.dispositivo
            ):
                self.estado_microfone = "ouvindo"
                while self.rodando:
                    time.sleep(0.1)
        except Exception as e:
            self.estado_microfone = "erro"
            self.ultimo_erro_transcricao = f"Microfone indisponível: {e}"
            print(f"[Libero Listener] Erro: {e}")
            self.rodando = False
        finally:
            if self.estado_microfone == "ouvindo":
                self.estado_microfone = "parado"
    
    def _processar_bloco(self, bloco):
        if self.pausado:
            return
        
        energia = float(np.sqrt(np.mean(bloco**2)))
        self.nivel_atual = energia
        
        if self.mostrar_nivel:
            barra = "█" * min(int(energia * 500), 50)
            print(f"\r[Nível] {energia:.5f} {barra}", end="")
        
        agora = time.time()
        
        # Detectar som alto (mesmo sem fala)
        if energia > LIMIAR_SOM_ALTO:
            self._detectar_som_alto(energia)
        
        if energia > self.threshold:
            # Fecha somente depois da janela de união para preservar pausas curtas.
            if self.buffer_audio and self.tempo_ultima_voz:
                if (agora - self.tempo_ultima_voz) > JANELA_MERGE_VOZ:
                    self._fechar_frase()
            
            self.buffer_audio.append(bloco)
            self.tempo_ultima_voz = agora
            self.blocos_voz += 1
            self.energia_max_buffer = max(self.energia_max_buffer, energia)
        else:
            # Blocos silenciosos mantêm a frase aberta durante a janela de união.
            if self.buffer_audio and self.tempo_ultima_voz:
                if (agora - self.tempo_ultima_voz) > JANELA_MERGE_VOZ:
                    self._fechar_frase()
    
    def _tem_palavra_critica(self, texto):
        """Verifica se o texto tem palavra crítica."""
        if not texto:
            return False
        normalizado = unicodedata.normalize("NFKD", texto.lower())
        normalizado = "".join(c for c in normalizado if not unicodedata.combining(c))
        return any(
            re.search(rf"(?<!\w){re.escape(p)}(?!\w)", normalizado)
            for p in PALAVRAS_CRITICAS
        )
    
    def _detectar_som_alto(self, energia):
        """Detecta som alto e chama callback."""
        if energia > LIMIAR_SOM_ALTO:
            # Detectar se é grito (energia + frequência alta)
            tipo = "grito" if energia > LIMIAR_GRITO else "som_alto"
            
            if self.callback:
                self.callback({
                    "tipo": "som_anomalo",
                    "subtipo": tipo,
                    "energia": energia,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
    
    def _fechar_frase(self):
        """Transcreve fala energética antes de aplicar filtros de duração/blocos."""
        if not self.buffer_audio:
            self._reset()
            return

        audio = np.concatenate(self.buffer_audio)
        duracao = len(audio) / SAMPLE_RATE
        blocos = self.blocos_voz
        self._reset()

        energia_media = float(np.sqrt(np.mean(audio**2)))
        if energia_media <= 0.15 and not self._passa_filtros(audio, duracao, blocos):
            return

        self._reset()
        threading.Thread(
            target=self._transcrever_e_emitir,
            args=(audio, duracao, energia_media > 0.15, blocos),
            daemon=True
        ).start()

    def _passa_filtros(self, audio, duracao, blocos):
        if blocos < BLOCOS_VOZ_MIN:
            print(f"[Libero Listener] Ignorado: só {blocos} blocos")
            return False
        if duracao < DURACAO_MIN_FRASE:
            print(f"[Libero Listener] Ignorado: {duracao:.1f}s < {DURACAO_MIN_FRASE}s")
            return False
        energia_media = float(np.sqrt(np.mean(audio**2)))
        if energia_media < ENERGIA_MIN_MEDIA:
            print(f"[Libero Listener] Ignorado: energia média {energia_media:.4f}")
            return False
        energia_max = float(np.max(np.abs(audio)))
        if energia_max < ENERGIA_MIN_MAX:
            print(f"[Libero Listener] Ignorado: pico {energia_max:.4f}")
            return False
        snr = energia_media / max(self.ruido_base, 0.001)
        if snr < SNR_MIN:
            print(f"[Libero Listener] Ignorado: SNR {snr:.1f}")
            return False
        return True
    
    def _reset(self):
        self.buffer_audio = []
        self.tempo_ultima_voz = None
        self.blocos_voz = 0
        self.energia_max_buffer = 0.0
    
    def _transcrever_e_emitir(self, audio, duracao, validar_emergencia=False, blocos=0):
        with self._transcription_lock:
            self._transcrever_e_emitir_serial(audio, duracao, validar_emergencia, blocos)

    def _transcrever_e_emitir_serial(self, audio, duracao, validar_emergencia=False, blocos=0):
        try:
            self.ultimo_erro_transcricao = None
            self.ultimo_idioma = _normalizar_idioma(None)
            texto = self._transcrever(audio)
            
            if not texto or len(texto.strip()) < 2:
                return

            if not _transcricao_plausivel(texto, duracao):
                self.ultimo_erro_transcricao = (
                    "Transcrição descartada: texto longo demais para a duração do áudio."
                )
                print(f"[Libero Listener] {self.ultimo_erro_transcricao}")
                return

            palavra_critica = self._tem_palavra_critica(texto)
            if validar_emergencia and not palavra_critica:
                if not self._passa_filtros(audio, duracao, blocos):
                    return
            
            # FILTRO 6: bloquear alucinações e fragmentos de áudio
            texto_lower = texto.lower().strip()

            alucinacoes = [
                "e aí", "tchau", "obrigado", "obrigada", "bye", "thank you",
                "legenda", "amara.org", "www.", ".com",
                "inscreva", "curta", "compartilhe"
            ]
            
            # Se for apenas fragmento (1 a 2 palavras) ou alucinação curta
            palavras = texto.split()
            if len(palavras) <= 2 and any(a in texto_lower for a in alucinacoes):
                print(f"[Libero Listener] Fragmento/Alucinação bloqueado: '{texto}'")
                return


            
            timestamp = datetime.now(timezone.utc).isoformat()
            self.frases_processadas += 1
            self.ultima_frase = texto
            self.ultimo_timestamp = timestamp
            
            print(
                f"\n[Libero Listener] 🎤 '{texto}' ({duracao:.1f}s, "
                f"language={self.ultimo_idioma}, method={self.metodo_transcricao})"
            )

            energia_media = float(np.sqrt(np.mean(audio**2)))
            energia_max = float(np.max(np.abs(audio)))
            zcr = float(np.mean(np.abs(np.diff(np.sign(audio)))) / 2)
            
            if self.callback:
                self.callback({
                    "tipo": "voz",
                    "texto": texto,
                    "duracao": duracao,
                    "timestamp": timestamp,
                    "metodo": self.metodo_transcricao,
                    "language": self.ultimo_idioma,
                    "energia_media": energia_media,
                    "energia_max": energia_max,
                    "zcr": zcr,
                })
        except Exception as e:
            print(f"[Libero Listener] Erro: {e}")
    
    def _transcrever(self, audio):
        audio_int16 = (audio * 32767).astype(np.int16)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as arquivo:
            tmp_path = arquivo.name

        try:
            write(tmp_path, SAMPLE_RATE, audio_int16)
            language_hint = None if SPEECH_LANGUAGE in {"", "auto"} else SPEECH_LANGUAGE
            if _groq:
                try:
                    with open(tmp_path, "rb") as f:
                        t = _groq.audio.transcriptions.create(
                            file=("audio.wav", f.read()),
                            model="whisper-large-v3-turbo",
                            response_format="verbose_json",
                            temperature=0.0,
                            **({"language": language_hint} if language_hint else {}),
                        )
                    texto = t.strip() if isinstance(t, str) else (t.text or "").strip()
                    idioma_detectado = getattr(t, "language", None)
                    idioma = _normalizar_idioma(idioma_detectado, fallback=None)
                    if idioma_detectado and idioma is None:
                        self.ultimo_erro_transcricao = (
                            f"Idioma de transcrição não suportado: {idioma_detectado}"
                        )
                        print(f"[Libero Listener] {self.ultimo_erro_transcricao}")
                        return ""
                    self.ultimo_idioma = idioma or _normalizar_idioma(None)
                    if texto:
                        self.metodo_transcricao = "groq"
                        return texto
                except Exception as e:
                    self.ultimo_erro_transcricao = str(e)
                    print(f"[Libero Listener] Groq falhou: {e}")
            
            if WHISPER_DISPONIVEL:
                if self.modelo is None:
                    self.modelo = whisper.load_model(self.modelo_whisper)
                r = self.modelo.transcribe(
                    tmp_path, language=language_hint, fp16=False
                )
                idioma_detectado = r.get("language")
                idioma = _normalizar_idioma(idioma_detectado, fallback=None)
                if idioma_detectado and idioma is None:
                    self.ultimo_erro_transcricao = (
                        f"Idioma de transcrição não suportado: {idioma_detectado}"
                    )
                    print(f"[Libero Listener] {self.ultimo_erro_transcricao}")
                    return ""
                self.ultimo_idioma = idioma or _normalizar_idioma(None)
                self.metodo_transcricao = "whisper_local"
                return r["text"].strip()
            
            self.ultimo_erro_transcricao = self.ultimo_erro_transcricao or (
                "Nenhum provedor de transcrição disponível"
            )
            return ""
        except Exception as e:
            self.ultimo_erro_transcricao = str(e)
            print(f"[Libero Listener] Erro de transcrição: {e}")
            return ""
        finally:
            try:
                os.remove(tmp_path)
            except FileNotFoundError:
                pass
    
    def status(self):
        return {
            "rodando": self.rodando,
            "estado_microfone": self.estado_microfone,
            "dispositivo": self.dispositivo,
            "taxa_captura": self.input_sample_rate,
            "threshold": self.threshold,
            "ruido_base": self.ruido_base,
            "nivel_atual": self.nivel_atual,
            "frases_processadas": self.frases_processadas,
            "ultima_frase": self.ultima_frase,
            "ultimo_timestamp": self.ultimo_timestamp,
            "metodo": self.metodo_transcricao,
            "idioma": self.ultimo_idioma,
            "ultimo_erro": self.ultimo_erro_transcricao,
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
