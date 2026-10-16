"""
Libero - Servidor de Câmera do Edge
Expõe /dev/video0 em http://localhost:8081/stream (MJPEG).
"""

import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

_ultimo_frame = None
_lock = threading.Lock()


def set_frame(frame_bytes):
    global _ultimo_frame
    with _lock:
        _ultimo_frame = frame_bytes


def _get_frame():
    with _lock:
        return _ultimo_frame


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path.startswith('/stream'):
            self.send_response(200)
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            try:
                while True:
                    frame = _get_frame()
                    if frame:
                        self.wfile.write(b'--frame\r\n')
                        self.wfile.write(b'Content-Type: image/jpeg\r\n\r\n')
                        self.wfile.write(frame)
                        self.wfile.write(b'\r\n')
                    time.sleep(0.05)
            except (BrokenPipeError, ConnectionResetError):
                pass
        elif self.path == '/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            ativo = _get_frame() is not None
            self.wfile.write(b'{"camera":"edge","ativo":' + 
                           (b'true' if ativo else b'false') + b'}')
        else:
            self.send_response(404)
            self.end_headers()


def iniciar_camera_server(porta=8081):
    def rodar():
        try:
            server = HTTPServer(('0.0.0.0', porta), Handler)
            print(f"[Libero Câmera] Stream do edge em http://localhost:{porta}/stream")
            server.serve_forever()
        except Exception as e:
            print(f"[Libero Câmera] Erro: {e}")
    
    t = threading.Thread(target=rodar, daemon=True)
    t.start()
    return t
