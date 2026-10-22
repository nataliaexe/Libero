import sys

import pytest

sys.path.insert(0, ".")

from edge import main


class FakeListener:
    def __init__(self):
        self.calls = []

    def pausar(self):
        self.calls.append("pausar")

    def retomar(self):
        self.calls.append("retomar")


def test_falar_pausa_e_retorna_listener(monkeypatch):
    libero = main.Libero.__new__(main.Libero)
    libero.listener = FakeListener()
    libero.falando = False
    monkeypatch.setattr(main, "falar", lambda _texto, language=None: {
        "metodo": "fake", "status": "ok"
    })
    monkeypatch.setattr(main.time, "sleep", lambda _duracao: None)

    libero._falar_uma_vez("Estou aqui.")

    assert libero.listener.calls == ["pausar", "retomar"]
    assert libero.falando is False


def test_falar_retorna_listener_se_tts_falhar(monkeypatch):
    libero = main.Libero.__new__(main.Libero)
    libero.listener = FakeListener()
    libero.falando = False

    def falhar(_texto, language=None):
        raise RuntimeError("TTS indisponível")

    monkeypatch.setattr(main, "falar", falhar)
    monkeypatch.setattr(main.time, "sleep", lambda _duracao: None)

    with pytest.raises(RuntimeError, match="TTS indisponível"):
        libero._falar_uma_vez("Estou aqui.")

    assert libero.listener.calls == ["pausar", "retomar"]
    assert libero.falando is False


def test_iniciar_nao_abre_camera_sem_consentimento(monkeypatch):
    class ListenerFake:
        def __init__(self, callback):
            self.rodando = False

        def iniciar(self):
            self.rodando = True

        def parar(self):
            self.rodando = False

        def status(self):
            return {"frases_processadas": 0}

    monkeypatch.setattr(main, "CONSENTIMENTO_CAMERA", False)
    monkeypatch.setattr(main, "Listener", ListenerFake)

    libero = main.Libero()
    libero.iniciar()

    assert libero.camera is None
    assert libero.contexto["camera_autorizada"] is False
    libero.parar()
