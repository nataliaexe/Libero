"""
Libero - Câmera placeholder
O server NUNCA abre câmera real. O edge é o único dono do /dev/video0.
"""

import cv2
import time
import threading
import numpy as np
from datetime import datetime


class CameraStream:
    """Placeholder puro. Nunca chama cv2.VideoCapture."""

    def __init__(self, camera_id=-1):
        self.camera_id = camera_id
        self.frame_atual = None
        self.rodando = False
        self.thread = None
        self.lock = threading.Lock()
        self.fps = 15

    def iniciar(self):
        if self.rodando:
            return True
        self.rodando = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        print("[Libero Câmera] Placeholder ativo (câmera é do edge)")
        return True

    def _loop(self):
        while self.rodando:
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            frame[:] = (17, 17, 27)
            agora = datetime.now().strftime("%H:%M:%S")
            cv2.putText(frame, "CAMERA EM USO PELO EDGE", (80, 220),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (88, 166, 255), 2)
            cv2.putText(frame, "http://localhost:8081/stream", (140, 260),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (139, 148, 158), 1)
            cv2.putText(frame, agora, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            _, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            with self.lock:
                self.frame_atual = jpeg.tobytes()
            time.sleep(1 / self.fps)

    def parar(self):
        self.rodando = False
        if self.thread:
            self.thread.join(timeout=2)

    def get_frame(self):
        with self.lock:
            return self.frame_atual

    def gerar_mjpeg(self):
        if not self.rodando:
            self.iniciar()
        while self.rodando:
            frame = self.get_frame()
            if frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(1 / self.fps)


_stream = None
_lock = threading.Lock()


def get_camera(camera_id=-1):
    global _stream
    with _lock:
        if _stream is None:
            _stream = CameraStream(camera_id=camera_id)
        return _stream
