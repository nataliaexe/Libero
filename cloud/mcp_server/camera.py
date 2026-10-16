"""
Libero - Câmera ao Vivo
Endpoint MJPEG para streaming no dashboard.
"""

import cv2
import time
import threading
from datetime import datetime, timezone


class CameraStream:
    def __init__(self, camera_id=0):
        self.camera_id = camera_id
        self.cap = None
        self.frame_atual = None
        self.rodando = False
        self.thread = None
        self.lock = threading.Lock()
        self.fps = 15
        self.qualidade_jpeg = 70
    
    def iniciar(self):
        if self.rodando:
            return True
        
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            print(f"[Libero Câmera] Não foi possível abrir câmera {self.camera_id}")
            return False
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        self.rodando = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        print(f"[Libero Câmera] Stream iniciado")
        return True
    
    def parar(self):
        self.rodando = False
        if self.thread:
            self.thread.join(timeout=2)
        if self.cap:
            self.cap.release()
        print("[Libero Câmera] Stream parado")
    
    def _loop(self):
        while self.rodando:
            ret, frame = self.cap.read()
            if ret:
                agora = datetime.now().strftime("%H:%M:%S")
                cv2.putText(
                    frame, agora, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2
                )
                _, jpeg = cv2.imencode(
                    '.jpg', frame,
                    [cv2.IMWRITE_JPEG_QUALITY, self.qualidade_jpeg]
                )
                with self.lock:
                    self.frame_atual = jpeg.tobytes()
            time.sleep(1 / self.fps)
    
    def get_frame(self):
        with self.lock:
            return self.frame_atual
    
    def gerar_mjpeg(self):
        """Generator MJPEG. Se câmera não iniciou, gera placeholder."""
        self.iniciar()
        
        # Se câmera não abriu, gerar placeholder
        if not self.rodando:
            import numpy as np
            placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(
                placeholder, "Camera indisponivel",
                (150, 240), cv2.FONT_HERSHEY_SIMPLEX,
                1, (100, 100, 100), 2
            )
            _, jpeg = cv2.imencode('.jpg', placeholder)
            frame_placeholder = jpeg.tobytes()
            
            while True:
                yield (
                    b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame_placeholder + b'\r\n'
                )
                time.sleep(1)
            return
        
        while self.rodando:
            frame = self.get_frame()
            if frame:
                yield (
                    b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n'
                )
            time.sleep(1 / self.fps)


_camera_stream = None
_camera_lock = threading.Lock()


def get_camera():
    global _camera_stream
    with _camera_lock:
        if _camera_stream is None:
            _camera_stream = CameraStream(camera_id=0)
        return _camera_stream
