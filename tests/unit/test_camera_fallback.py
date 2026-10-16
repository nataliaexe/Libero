import sys
from unittest.mock import patch

sys.path.insert(0, ".")

from cloud.mcp_server.camera import CameraStream
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


def test_camera_stream_tenta_camera_alternativa_e_placeholder():
    capturas = {1: FakeCapture(False), 0: FakeCapture(False)}
    with patch("cloud.mcp_server.camera.cv2.VideoCapture", side_effect=capturas.get) as abrir:
        camera = CameraStream(camera_id=1)
        quadro_mjpeg = next(camera.gerar_mjpeg())

    assert [chamada.args[0] for chamada in abrir.call_args_list] == [1, 0]
    assert camera.rodando is False
    assert quadro_mjpeg.startswith(b"--frame\r\nContent-Type: image/jpeg\r\n\r\n")
    assert b"\xff\xd8" in quadro_mjpeg


def test_camera_stream_usa_camera_secundaria_disponivel():
    capturas = {1: FakeCapture(False), 0: FakeCapture(True)}
    with patch("cloud.mcp_server.camera.cv2.VideoCapture", side_effect=capturas.get):
        camera = CameraStream(camera_id=1)
        assert camera.iniciar() is True
        camera.parar()

    assert camera.camera_id == 0


def test_camera_edge_tenta_camera_secundaria_disponivel():
    capturas = {0: FakeCapture(False), 1: FakeCapture(True)}
    with patch("edge.capture.stream.cv2.VideoCapture", side_effect=capturas.get):
        camera = CameraLibero(camera_id=0)
        camera.iniciar()
        camera.parar()

    assert camera.camera_id == 1
