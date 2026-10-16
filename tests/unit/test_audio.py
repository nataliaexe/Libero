import sys
sys.path.insert(0, ".")
from cloud.mcp_server import audio


def test_audio_status_sem_listener():
    audio._listener = None
    status = audio.status()
    assert status["registrado"] is False


def test_audio_status_com_listener():
    class FakeListener:
        rodando = True
        frases_processadas = 5
        ultima_frase = "teste"
        nivel_atual = 0.1
        threshold = 0.05
        metodo_transcricao = "groq"
    
    audio.registrar_listener(FakeListener())
    status = audio.status()
    assert status["registrado"] is True
    assert status["rodando"] is True
    assert status["frases_processadas"] == 5
