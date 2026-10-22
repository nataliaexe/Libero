import stat
import asyncio

import pytest

from cloud.mcp_server import chat, server


def test_chat_store_protege_arquivos_e_valida_id(tmp_path, monkeypatch):
    monkeypatch.setattr(chat, "DATA_DIR", tmp_path)
    store = chat.ChatStore()
    store.adicionar_mensagem("dona-maria", "idoso", "Olá")

    arquivo = tmp_path / "dona-maria.json"
    assert stat.S_IMODE(arquivo.stat().st_mode) == 0o600
    with pytest.raises(ValueError, match="idoso_id inválido"):
        store.adicionar_mensagem("../fora", "idoso", "Olá")


def test_processos_separados_enxergam_historico_atualizado(tmp_path, monkeypatch):
    monkeypatch.setattr(chat, "DATA_DIR", tmp_path)
    edge_store = chat.ChatStore()
    api_store = chat.ChatStore()

    edge_store.adicionar_mensagem("dona-maria", "idoso", "Hello", metadata={"language": "en"})
    assert api_store.listar_mensagens("dona-maria")[0]["texto"] == "Hello"

    api_store.adicionar_mensagem("dona-maria", "libero", "I hear you.", metadata={"language": "en"})
    assert [m["texto"] for m in edge_store.listar_mensagens("dona-maria")] == [
        "I hear you.", "Hello"
    ]


def test_mensagem_enviada_pela_familia_tem_autor_cuidador(monkeypatch):
    class RequestFake:
        headers = {}
        cookies = {}

        async def json(self):
            return {"texto": "Estou pensando em você."}

    class StoreFake:
        def __init__(self):
            self.mensagens = []

        def adicionar_mensagem(self, *args, **kwargs):
            self.mensagens.append(args)

    store = StoreFake()
    mensagem_recebida = []
    monkeypatch.setattr(server.auth, "extrair_token", lambda request: "sessao")
    monkeypatch.setattr(server.auth, "autorizar_idoso", lambda *args: None)
    monkeypatch.setattr(server, "get_store", lambda: store)
    monkeypatch.setattr(
        "cloud.agents.companion.conversar",
        lambda texto, contexto: mensagem_recebida.append(texto) or "Que carinho bonito.",
    )

    asyncio.run(server.enviar_mensagem("dona-maria", RequestFake()))

    assert store.mensagens[0][1:3] == ("cuidador", "Estou pensando em você.")
    assert mensagem_recebida[0].startswith("[Mensagem do cuidador]")
