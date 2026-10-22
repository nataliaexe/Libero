import sys
from unittest.mock import patch

sys.path.insert(0, ".")

from cloud.mcp_server.camera import CameraStream
from edge import main
from edge.capture.stream import CameraLibero


class FakeCapture:
    def __init__(self, opened):
        self.opened = opened

    def isOpened(self):
        return self.opened

    def set(self, *_args):
        return True

    def read(self):
        return False, None

    def release(self):
        pass


def test_camera_stream_placeholder_nao_abre_camera_fisica():
    with patch("cloud.mcp_server.camera.cv2.VideoCapture") as abrir:
        camera = CameraStream(camera_id=1)
        quadro_mjpeg = next(camera.gerar_mjpeg())
        camera.parar()

    abrir.assert_not_called()
    assert quadro_mjpeg.startswith(b"--frame\r\nContent-Type: image/jpeg\r\n\r\n")
    assert b"\xff\xd8" in quadro_mjpeg


def test_camera_stream_inicia_placeholder_sem_camera_fisica():
    with patch("cloud.mcp_server.camera.cv2.VideoCapture") as abrir:
        camera = CameraStream(camera_id=1)
        assert camera.iniciar() is True
        camera.parar()

    abrir.assert_not_called()


def test_camera_edge_tenta_camera_secundaria_disponivel():
    capturas = {0: FakeCapture(False), 1: FakeCapture(True)}
    with patch("edge.capture.stream.cv2.VideoCapture", side_effect=capturas.get):
        with patch("edge.capture.stream._agendar_inicializacao_mediapipe") as agendar:
            camera = CameraLibero(camera_id=0)
            camera.iniciar()
            camera.parar()
            agendar.assert_called_once()

    assert camera.camera_id == 1


def test_fallback_opencv_nao_confirma_queda():
    camera = CameraLibero()

    for _ in range(10):
        resultado = camera._detectar_queda({
            "detectado": True,
            "angulo": 80,
            "metodo": "opencv",
        })

    assert resultado["detectado"] is False
    assert resultado["confianca"] == 0.0


def test_callback_ignora_queda_sem_pose_mediapipe():
    libero = main.Libero.__new__(main.Libero)

    libero._on_camera({
        "tipo": "queda",
        "confianca": 1.0,
        "dados": {"metodo": "opencv"},
    })
