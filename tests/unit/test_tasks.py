import pytest

from cloud.mcp_server import tasks
import stat


def test_task_store_criar_listar_atualizar_remover(tmp_path, monkeypatch):
    monkeypatch.setattr(tasks, "DATA_DIR", tmp_path)
    store = tasks.TaskStore()

    criada = store.criar("idosa-teste", "Tomar remédio", "08:00")
    assert criada["status"] == "pendente"
    assert store.listar("idosa-teste") == [criada]

    atualizada = store.atualizar("idosa-teste", criada["id"], "feito")
    assert atualizada["status"] == "feito"
    assert store.remover("idosa-teste", criada["id"]) is True
    assert store.listar("idosa-teste") == []


def test_task_store_persiste_e_recarrega(tmp_path, monkeypatch):
    monkeypatch.setattr(tasks, "DATA_DIR", tmp_path)
    store = tasks.TaskStore()
    criada = store.criar("idosa-teste", "Almoço", "12:00", "refeicao")

    recarregada = tasks.TaskStore()
    assert recarregada.listar("idosa-teste") == [criada]
    assert stat.S_IMODE((tmp_path / "idosa-teste.json").stat().st_mode) == 0o600


def test_task_store_rejeita_idoso_invalido(tmp_path, monkeypatch):
    monkeypatch.setattr(tasks, "DATA_DIR", tmp_path)
    store = tasks.TaskStore()
    with pytest.raises(ValueError, match="idoso_id inválido"):
        store.listar("../fora")
