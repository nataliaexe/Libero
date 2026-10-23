import sys
import io
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pytest
from types import SimpleNamespace

sys.path.insert(0, ".")

from edge.capture.listener import JANELA_MERGE_VOZ, Listener, _transcricao_plausivel
from scripts.diagnostico_audio import _capturar_isolado, calcular_snr
from edge import main


def test_transcricao_groq_detecta_idioma_sem_forcar_ingles(monkeypatch):
    chamadas = []

    class FakeTranscriptions:
        def create(self, **kwargs):
            chamadas.append(kwargs)
            return SimpleNamespace(text="hello", language="english")

    fake_groq = SimpleNamespace(audio=SimpleNamespace(transcriptions=FakeTranscriptions()))
    monkeypatch.setattr("edge.capture.listener._groq", fake_groq)
    monkeypatch.setattr("edge.capture.listener.WHISPER_DISPONIVEL", False)
    monkeypatch.setattr("edge.capture.listener.SPEECH_LANGUAGE", "auto")
    listener = Listener()

    texto = listener._transcrever(np.full(1600, 0.1, dtype=np.float32))

    assert texto == "hello"
    assert "language" not in chamadas[0]
    assert chamadas[0]["response_format"] == "verbose_json"
    assert listener.ultimo_idioma == "en"


def test_transcricao_groq_usa_idioma_padrao_quando_deteccao_nao_e_suportada(monkeypatch):
    class FakeTranscriptions:
        def create(self, **kwargs):
            return SimpleNamespace(text="Olá.", language="spanish")

    fake_groq = SimpleNamespace(audio=SimpleNamespace(transcriptions=FakeTranscriptions()))
    monkeypatch.setattr("edge.capture.listener._groq", fake_groq)
    monkeypatch.setattr("edge.capture.listener.WHISPER_DISPONIVEL", False)
    monkeypatch.setattr("edge.capture.listener.DEFAULT_LANGUAGE", "pt-BR")
    listener = Listener()

    texto = listener._transcrever(np.full(1600, 0.1, dtype=np.float32))

    assert texto == "Olá."
    assert listener.ultimo_idioma == "pt-BR"
    assert listener.ultimo_erro_transcricao is None


def test_transcricao_longa_demais_para_audio_curto_e_improvavel():
    alucinacao = "Hãy subscribe cho kênh Ghiền Mì Gõ Để không bỏ lỡ những video hấp dẫn"

    assert not _transcricao_plausivel(alucinacao, 0.3)
    assert _transcricao_plausivel("No.", 0.3)


def test_blocos_de_voz_dentro_da_janela_sao_unidos(monkeypatch):
    listener = Listener(threshold=0.1)
    blocos_fechados = []

    def fechar_frase():
        blocos_fechados.append(len(listener.buffer_audio))
        listener._reset()

    listener._fechar_frase = fechar_frase
    instantes = iter((100.0, 100.7, 100.75, 101.56))
    monkeypatch.setattr("edge.capture.listener.time.time", lambda: next(instantes))
    voz = np.full(1024, 0.2, dtype=np.float32)
    silencio = np.zeros(1024, dtype=np.float32)

    listener._processar_bloco(voz)
    listener._processar_bloco(silencio)
    listener._processar_bloco(voz)
    assert blocos_fechados == []
    assert len(listener.buffer_audio) == 2

    listener._processar_bloco(silencio)
    assert blocos_fechados == [2]
    assert JANELA_MERGE_VOZ == 0.8


def test_diagnostico_calcula_snr_com_silencio_e_fala():
    audio = np.concatenate((np.full(16000, 0.01), np.full(32000, 0.1)))

    assert calcular_snr(audio, 16000) == 20.0


def test_diagnostico_carrega_captura_serializada():
    esperado = np.array([0.1, 0.2], dtype=np.float32)
    buffer = io.BytesIO()
    np.save(buffer, esperado)
    processo = SimpleNamespace(returncode=0, stdout=buffer.getvalue(), stderr=b"")

    with patch("scripts.diagnostico_audio.subprocess.run", return_value=processo):
        capturado = _capturar_isolado(0, 16000)

    np.testing.assert_array_equal(capturado, esperado)


def test_emergencia_curta_e_transcrita_antes_dos_filtros(monkeypatch):
    listener = Listener(threshold=0.1, callback=lambda evento: eventos.append(evento))
    eventos = []
    voz = np.full(1024, 0.2, dtype=np.float32)
    listener.buffer_audio = [voz]
    listener.blocos_voz = 1

    class ThreadFake:
        def __init__(self, target, args, daemon):
            self.target = target
            self.args = args

        def start(self):
            self.target(*self.args)

    monkeypatch.setattr("edge.capture.listener.threading.Thread", ThreadFake)
    monkeypatch.setattr(listener, "_transcrever", lambda _audio: "Socorro!")

    listener._fechar_frase()

    assert len(eventos) == 1
    assert eventos[0]["texto"] == "Socorro!"
    assert eventos[0]["energia_media"] == pytest.approx(0.2)
    assert eventos[0]["energia_max"] == pytest.approx(0.2)
    assert "zcr" in eventos[0]


def test_features_de_audio_chegam_ao_orquestrador(monkeypatch):
    libero = main.Libero.__new__(main.Libero)
    libero.cooldown_fala = main.Cooldown(segundos=0)
    libero.falando = False
    chamadas = []

    class ThreadFake:
        def __init__(self, target, args, daemon):
            chamadas.append(args)

        def start(self):
            pass

    monkeypatch.setattr(main.threading, "Thread", ThreadFake)
    evento = {
        "tipo": "voz", "texto": "Estou agitada", "energia_media": 0.2,
        "energia_max": 0.6, "zcr": 0.25, "duracao": 1.0,
    }

    libero._on_audio(evento)

    features = chamadas[0][1]
    assert features["energia_media"] == 0.2
    assert features["energia_max"] == 0.6
    assert features["zcr"] == 0.25
