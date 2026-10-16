import stat

import pytest

from cloud.mcp_server import chat


def test_chat_store_protege_arquivos_e_valida_id(tmp_path, monkeypatch):
    monkeypatch.setattr(chat, "DATA_DIR", tmp_path)
    store = chat.ChatStore()
    store.adicionar_mensagem("dona-maria", "idoso", "Olá")

    arquivo = tmp_path / "dona-maria.json"
    assert stat.S_IMODE(arquivo.stat().st_mode) == 0o600
    with pytest.raises(ValueError, match="idoso_id inválido"):
        store.adicionar_mensagem("../fora", "idoso", "Olá")
