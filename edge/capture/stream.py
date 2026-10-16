"""
Libero - Stream de Câmera
Compatível com MediaPipe novo (1.1+) e OpenCV 5.
Fallback universal para OpenCV puro.
"""

import cv2
import numpy as np
from datetime import datetime, timezone
import threading
import time
import os

# Tentar MediaPipe novo (tasks)
MEDIAPIPE_DISPONIVEL = False
POSE_LANDMARKER = None

try:
    import mediapipe as mp
    
    if hasattr(mp, "tasks"):
        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python import vision as mp_vision
        from mediapipe.framework.formats import landmark_pb2
        
        modelo_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "models", "pose_landmarker_lite.task"
        )
        
        if os.path.exists(modelo_path):
            base_options = mp_python.BaseOptions(model_asset_path=modelo_path)
            options = mp_vision.PoseLandmarkerOptions(
                base_options=base_options,
                running_mode=mp_vision.RunningMode.IMAGE,
                min_pose_detection_confidence=0.5,
                min_pose_presence_confidence=0.5,
                min_tracking_confidence=0.5
            )
            POSE_LANDMARKER = mp_vision.PoseLandmarker.create_from_options(options)
            MEDIAPIPE_DISPONIVEL = True
            print("[Libero] MediaPipe 1.x (tasks) OK")
        else:
            print(f"[Libero] Modelo não encontrado: {modelo_path}")
            print("[Libero] Usando OpenCV puro")
    elif hasattr(mp, "solutions"):
        MEDIAPIPE_DISPONIVEL = False
        print("[Libero] MediaPipe solutions — não usado")
    else:
        print("[Libero] MediaPipe desconhecido — usando OpenCV puro")
except ImportError:
    print("[Libero] MediaPipe não instalado — usando OpenCV puro")
except Exception as e:
    print(f"[Libero] MediaPipe erro: {e} — usando OpenCV puro")


class CameraLibero:
    """
    Câmera contínua com detecção local.
    
    Detecta:
    - Movimento (frame differencing)
    - Presença (contorno)
    - Queda (heurística de bounding box + MediaPipe se disponível)
    """
    
    def __init__(self, camera_id=0, callback=None):
        self.camera_id = camera_id
        self.callback = callback
        
        self.cap = None
        self.rodando = False
        self.thread = None
        
        # Buffer
        self.historico_angulos = []
        self.max_historico = 30
        self.fundo = None
        
        # Estado
        self.ultimo_evento = None
        self.timestamp_ultimo_evento = None
    
    def iniciar(self):
        """Inicia câmera e thread."""
        self.cap = cv2.VideoCapture(self.camera_id)
        
        if not self.cap.isOpened():
            raise RuntimeError(
                f"Não foi possível abrir câmera {self.camera_id}.\n\n"
                "No Linux:\n"
                "  1. Verificar permissão: ls -la /dev/video*\n"
                "  2. Adicionar usuário ao grupo: sudo usermod -a -G video $USER\n"
                "  3. Logout/login\n"
                "  4. Testar: guvcview\n\n"
                "No Windows: verificar se a câmera está em uso\n"
                "No Mac: dar permissão em Preferências do Sistema"
            )
        
        self.rodando = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        print(f"[Libero Câmera] Iniciada (camera_id={self.camera_id})")
        print(f"[Libero Câmera] MediaPipe: {'ATIVO' if MEDIAPIPE_DISPONIVEL else 'OpenCV puro'}")
    
    def parar(self):
        self.rodando = False
        if self.thread:
            self.thread.join(timeout=2)
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        print("[Libero Câmera] Parada")
    
    def _loop(self):
        """Loop principal."""
        while self.rodando:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    time.sleep(0.1)
                    continue
                
                evento = self._processar_frame(frame)
                
                if evento and self.callback:
                    try:
                        self.callback(evento)
                    except Exception as e:
                        print(f"[Libero Câmera] Erro no callback: {e}")
                
                time.sleep(0.033)
            except Exception as e:
                print(f"[Libero Câmera] Erro no loop: {e}")
                time.sleep(0.5)
    
    def _processar_frame(self, frame):
        """Processa frame e retorna evento."""
        altura, largura = frame.shape[:2]
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Movimento
        movimento = self._detectar_movimento(frame)
        
        # Pose
        if MEDIAPIPE_DISPONIVEL:
            pose_info = self._detectar_pose_mediapipe(frame, largura, altura)
        else:
            pose_info = self._detectar_pose_opencv(frame, largura, altura)
        
        # Queda
        queda = self._detectar_queda(pose_info)
        
        # Montar evento
        if queda["detectado"]:
            return {
                "tipo": "queda",
                "confianca": queda["confianca"],
                "dados": {
                    "angulo_corpo": queda.get("angulo"),
                    "variacao": queda.get("variacao")
                },
                "timestamp": timestamp
            }
        
        if movimento["detectado"]:
            return {
                "tipo": "movimento",
                "confianca": movimento["confianca"],
                "dados": {"area": movimento["area"]},
                "timestamp": timestamp
            }
        
        if pose_info.get("detectado"):
            return {
                "tipo": "presenca",
                "confianca": 0.5,
                "dados": {},
                "timestamp": timestamp
            }
        
        return None
    
    def _detectar_movimento(self, frame):
        """Detecção de movimento (compatível com OpenCV 5)."""
        cinza = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cinza = cv2.GaussianBlur(cinza, (21, 21), 0)
        
        if self.fundo is None:
            self.fundo = cinza.astype(np.float32)
            return {"detectado": False, "area": 0, "confianca": 0.0}
        
        # Converter para float32 (compatível com OpenCV 5)
        cinza_f = cinza.astype(np.float32)
        fundo_f = self.fundo.astype(np.float32)
        
        # Atualizar fundo manualmente (sem accumulateWeighted)
        alpha = 0.01
        self.fundo = (1 - alpha) * fundo_f + alpha * cinza_f
        
        # Diferença
        diff = cv2.absdiff(self.fundo.astype(np.uint8), cinza)
        _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
        thresh = cv2.dilate(thresh, None, iterations=2)
        
        contornos, _ = cv2.findContours(
            thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        
        area_total = sum(
            cv2.contourArea(c) for c in contornos if cv2.contourArea(c) > 1000
        )
        
        detectado = area_total > 5000
        confianca = min(area_total / 20000, 1.0) if detectado else 0.0
        
        return {"detectado": detectado, "area": int(area_total), "confianca": confianca}
    
    def _detectar_pose_mediapipe(self, frame, largura, altura):
        """Pose via MediaPipe 1.x (tasks)."""
        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            
            resultado = POSE_LANDMARKER.detect(mp_image)
            
            if not resultado.pose_landmarks or len(resultado.pose_landmarks) == 0:
                return {"detectado": False}
            
            landmarks = resultado.pose_landmarks[0]
            
            ombro_esq = landmarks[11]
            ombro_dir = landmarks[12]
            quadril_esq = landmarks[23]
            quadril_dir = landmarks[24]
            
            visibilidade = min(
                getattr(ombro_esq, 'visibility', 1.0),
                getattr(ombro_dir, 'visibility', 1.0),
                getattr(quadril_esq, 'visibility', 1.0),
                getattr(quadril_dir, 'visibility', 1.0)
            )
            
            if visibilidade < 0.5:
                return {"detectado": False}
            
            ombro_x = (ombro_esq.x + ombro_dir.x) / 2 * largura
            ombro_y = (ombro_esq.y + ombro_dir.y) / 2 * altura
            quadril_x = (quadril_esq.x + quadril_dir.x) / 2 * largura
            quadril_y = (quadril_esq.y + quadril_dir.y) / 2 * altura
            
            dx = quadril_x - ombro_x
            dy = quadril_y - ombro_y
            angulo = abs(np.degrees(np.arctan2(dx, dy)))
            
            return {
                "detectado": True,
                "angulo": angulo,
                "metodo": "mediapipe"
            }
        except Exception as e:
            print(f"[Libero] Erro MediaPipe: {e}")
            return {"detectado": False}
    
    def _detectar_pose_opencv(self, frame, largura, altura):
        """Fallback: detecta pessoa por contorno."""
        cinza = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cinza = cv2.GaussianBlur(cinza, (21, 21), 0)
        
        if self.fundo is None:
            return {"detectado": False}
        
        diff = cv2.absdiff(self.fundo.astype(np.uint8), cinza)
        _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
        thresh = cv2.dilate(thresh, None, iterations=2)
        
        contornos, _ = cv2.findContours(
            thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        
        if not contornos:
            return {"detectado": False}
        
        maior = max(contornos, key=cv2.contourArea)
        area = cv2.contourArea(maior)
        
        if area < 5000:
            return {"detectado": False}
        
        x, y, w, h = cv2.boundingRect(maior)
        
        if h == 0:
            return {"detectado": False}
        
        razao = w / h
        
        if razao > 1.5:
            angulo = 80
        elif razao < 0.5:
            angulo = 10
        else:
            angulo = 45
        
        return {
            "detectado": True,
            "angulo": angulo,
            "metodo": "opencv",
            "razao": razao,
            "area": int(area)
        }
    
    def _detectar_queda(self, pose_info):
        """Detecta queda APENAS com múltiplos sinais fortes."""
        if not pose_info.get("detectado"):
            return {"detectado": False, "confianca": 0.0}
        
        angulo = pose_info.get("angulo", 0)
        
        self.historico_angulos.append(angulo)
        if len(self.historico_angulos) > self.max_historico:
            self.historico_angulos.pop(0)
        
        if len(self.historico_angulos) < 10:
            return {"detectado": False, "confianca": 0.0}
        
        atual = self.historico_angulos[-1]
        anterior = self.historico_angulos[0]
        variacao = atual - anterior
        
        # REGRA RIGOROSA: precisa de ângulo MUITO alto E variação MUITO rápida
        queda = False
        confianca = 0.0
        
        if atual > 75 and variacao > 40:
            queda = True
            confianca = min((atual / 90) * 0.5 + (variacao / 60) * 0.5, 1.0)
        
        return {
            "detectado": queda,
            "confianca": confianca,
            "angulo": atual,
            "variacao": variacao
        }


# ============================================================
# TESTE
# ============================================================

if __name__ == "__main__":
    def on_evento(evento):
        print(f"[Evento] {evento['tipo']} (confiança: {evento['confianca']:.2f})")
    
    print(f"[Libero] Sistema: Linux")
    print(f"[Libero] OpenCV: {cv2.__version__}")
    
    try:
        camera = CameraLibero(camera_id=0, callback=on_evento)
        camera.iniciar()
        print("[Libero] Câmera rodando. Ctrl+C para parar.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Libero] Parando...")
    except Exception as e:
        print(f"[Libero] Erro: {e}")
    finally:
        try:
            camera.parar()
        except Exception:
            pass
