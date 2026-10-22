"""
Libero - Servidor de Câmera do Edge
Expõe /dev/video0 em http://localhost:8081/stream (MJPEG).
"""

import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_ultimo_frame = None
_ultimo_frame_em = None
_lock = threading.Lock()
_status_provider = None

EDGE_HOST = os.getenv("LIBERO_EDGE_HOST", "127.0.0.1")
EDGE_ALLOWED_ORIGINS = {
    origin.strip().rstrip("/")
    for origin in os.getenv(
        "LIBERO_EDGE_ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5500,http://127.0.0.1:5500",
    ).split(",")
    if origin.strip()
}


def set_frame(frame_bytes):
    global _ultimo_frame, _ultimo_frame_em
    with _lock:
        _ultimo_frame = frame_bytes
        _ultimo_frame_em = time.time()


def _get_frame():
    with _lock:
        return _ultimo_frame


def _frame_age_seconds():
    with _lock:
        if _ultimo_frame_em is None:
            return None
        return max(0.0, time.time() - _ultimo_frame_em)


def set_status_provider(provider):
    """Register the edge runtime status snapshot for the local status endpoint."""
    global _status_provider
    _status_provider = provider


def _allowed_origin(origin):
    return not origin or origin.rstrip("/") in EDGE_ALLOWED_ORIGINS


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        origin = self.headers.get("Origin", "")
        if not _allowed_origin(origin):
            self.send_response(403)
            self.end_headers()
            return
        if self.path.startswith('/stream'):
            self.send_response(200)
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
            if origin:
                self.send_header('Access-Control-Allow-Origin', origin.rstrip('/'))
                self.send_header('Vary', 'Origin')
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
            self.send_header('Cache-Control', 'no-store')
            if origin:
                self.send_header('Access-Control-Allow-Origin', origin.rstrip('/'))
                self.send_header('Vary', 'Origin')
            self.end_headers()
            try:
                status = _status_provider() if _status_provider else {}
            except Exception:
                status = {}
            age = _frame_age_seconds()
            status["camera_frame_atual"] = age is not None and age < 2.0
            status["camera_frame_age_seconds"] = round(age, 2) if age is not None else None
            self.wfile.write(json.dumps(status, ensure_ascii=False).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        origin = self.headers.get("Origin", "")
        if not _allowed_origin(origin):
            self.send_response(403)
            self.end_headers()
            return
        self.send_response(204)
        if origin:
            self.send_header('Access-Control-Allow-Origin', origin.rstrip('/'))
            self.send_header('Vary', 'Origin')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()


def iniciar_camera_server(porta=8081, host=None):
    def rodar():
        try:
            bind_host = host or EDGE_HOST
            server = ThreadingHTTPServer((bind_host, porta), Handler)
            print(f"[Libero Câmera] Stream do edge em http://{bind_host}:{porta}/stream")
            server.serve_forever()
        except Exception as e:
            print(f"[Libero Câmera] Erro: {e}")
    
    t = threading.Thread(target=rodar, daemon=True)
    t.start()
    return t
