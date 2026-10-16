"""
Libero - Sistema Principal
Com cooldown e debounce para evitar spam de eventos.
"""

import os
import sys
import time
import threading
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from edge.capture.listener import Listener
from edge.capture.stream import CameraLibero, MEDIAPIPE_DISPONIVEL
from edge.output.speaker import falar
from cloud.agents.orchestrator import Orquestrador
from cloud.mcp_server import audio


# ============================================================
# COOLDOWN (evitar spam)
# ============================================================

class Cooldown:
    """Evita que eventos idênticos disparem muitas vezes."""
    
    def __init__(self, segundos=10):
        self.segundos = segundos
        self.ultimos = {}  # chave -> timestamp
    
    def pode_disparar(self, chave):
        agora = datetime.now(timezone.utc)
        ultimo = self.ultimos.get(chave)
        
        if ultimo:
            delta = (agora - ultimo).total_seconds()
            if delta < self.segundos:
                return False
        
        self.ultimos[chave] = agora
        return True
    
    def resetar(self, chave=None):
        if chave:
            self.ultimos.pop(chave, None)
        else:
            self.ultimos.clear()


class Libero:
    """
    Sistema completo com cooldown e debounce.
    """
    
    def __init__(self, idoso_id="dona-maria", nome="Dona Maria"):
        self.idoso_id = idoso_id
        self.contexto = {
            "nome": nome,
            "local": "casa",
            "camera_autorizada": True
        }
        
        self.orquestrador = Orquestrador(idoso_id, self.contexto)
        self.listener = Listener(callback=self._on_audio)
        self.camera = None
        
        # Cooldowns
        self.cooldown_camera = Cooldown(segundos=30)  # movimento
        self.cooldown_fala = Cooldown(segundos=5)     # fala
        self.cooldown_processamento = Cooldown(segundos=3)
        
        # Estado
        self.rodando = False
        self.eventos = []
        self.ultima_resposta = None
        self.falando = False  # lock para não falar ao mesmo tempo
    
    def iniciar(self):
        print("[Libero] Iniciando sistema...")
        
        # Listener
        self.listener.iniciar()
        audio.registrar_listener(self.listener)
        
        # Câmera
        try:
            self.camera = CameraLibero(camera_id=0, callback=self._on_camera)
            self.camera.iniciar()
        except Exception as e:
            print(f"[Libero] Câmera indisponível: {e}")
            self.camera = None
        
        self.rodando = True
        print("\n[Libero] ✓ Sistema rodando")
        print("[Libero] Cooldowns ativos: câmera=30s, fala=5s\n")
    
    def parar(self):
        print("\n[Libero] Parando...")
        self.rodando = False
        if self.listener:
            self.listener.parar()
        if self.camera:
            self.camera.parar()
        print("[Libero] Sistema parado")
    
    def _on_audio(self, evento):
        """Callback quando listener detecta fala."""
        texto = evento.get("texto", "")
        
        if not texto or len(texto.strip()) < 2:
            return
        
        # Cooldown de fala (evita transcrever a mesma coisa)
        if not self.cooldown_fala.pode_disparar("fala"):
            return
        
        print(f"\n[Áudio] {texto}")
        
        # Lock: se está falando, não processa
        if self.falando:
            print("[Libero] (ocupado falando, ignorando)")
            return
        
        threading.Thread(
            target=self._processar,
            args=(texto, {}, {}),
            daemon=True
        ).start()
    
    def _on_camera(self, evento):
        """Callback quando câmera detecta evento."""
        tipo = evento.get("tipo")
        confianca = evento.get("confianca", 0)
        
        # Só processar quedas com confiança alta
        if tipo == "queda":
            if not self.cooldown_camera.pode_disparar("queda"):
                return
            chave = "queda"
        elif tipo == "movimento":
            # Movimento só processa se confiança alta E se não houve fala recente
            if confianca < 0.7:
                return
            if not self.cooldown_camera.pode_disparar("movimento"):
                return
            chave = "movimento"
        else:
            return
        
        print(f"\n[Câmera] {tipo} (confiança: {confianca:.2f})")
        
        # Lock: se está falando, ignora
        if self.falando:
            return
        
        features_visao = evento.get("dados", {})
        
        threading.Thread(
            target=self._processar,
            args=("", {}, features_visao),
            daemon=True
        ).start()
    
    def _processar(self, texto, features_audio, features_visao):
        """Processa uma entrada."""
        # Cooldown de processamento
        if not self.cooldown_processamento.pode_disparar("proc"):
            return
        
        try:
            resultado = self.orquestrador.processar(
                texto,
                features_audio=features_audio,
                features_visao=features_visao,
                movimento=features_visao.get("angulo_corpo", 0) > 0
            )
            
            nivel = resultado.get("nivel", 0)
            resposta = resultado.get("resposta")
            
            self.eventos.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "texto": texto,
                "nivel": nivel,
                "resposta": resposta,
                "acoes": [a["tipo"] for a in resultado.get("acoes", [])]
            })
            
            # Falar (com lock)
            if resposta:
                self._falar_uma_vez(resposta)
            
            acoes = [a["tipo"] for a in resultado.get("acoes", [])]
            if acoes:
                print(f"[Ações] {acoes}")
        except Exception as e:
            print(f"[Libero] Erro: {e}")
    
    def _falar_uma_vez(self, texto):
        """Fala um texto, evitando múltiplas falas simultâneas."""
        if self.falando:
            return
        
        self.falando = True
        try:
            print(f"[Libero] 🔊 {texto}")
            falar(texto)
            self.ultima_resposta = texto
        finally:
            self.falando = False
    
    def status(self):
        return {
            "rodando": self.rodando,
            "idoso_id": self.idoso_id,
            "eventos": len(self.eventos),
            "ultimos_eventos": self.eventos[-5:],
            "listener": self.listener.status() if self.listener else None,
            "camera": "ativa" if self.camera else "inativa",
            "mediapipe": MEDIAPIPE_DISPONIVEL,
            "cooldowns": {
                "camera": self.cooldown_camera.segundos,
                "fala": self.cooldown_fala.segundos,
                "proc": self.cooldown_processamento.segundos
            }
        }


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    libero = Libero(idoso_id="dona-maria", nome="Dona Maria")
    
    try:
        libero.iniciar()
        
        while True:
            time.sleep(10)
            status = libero.status()
            print(f"\r[Status] {status['eventos']} eventos | "
                  f"Câmera: {status['camera']} | "
                  f"Frases: {status['listener']['frases_processadas']}", end="")
    except KeyboardInterrupt:
        print("\n")
    finally:
        libero.parar()
