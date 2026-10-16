"""
Libero - Testes do Agente de Memória
"""

import sys
import json
import stat
import pytest
sys.path.insert(0, ".")

from cloud.agents import memory


def test_detectar_historia_curta():
    resultado = memory.detectar_historia("Bom dia")
    assert resultado["detectado"] is False


def test_detectar_historia_longa():
    texto = "Quando eu era jovem, eu dançava toda sexta com meu marido no clube da cidade."
    resultado = memory.detectar_historia(texto)
    assert resultado["detectado"] is True
    assert resultado["confianca"] > 0.4


def test_detectar_historia_marcadores():
    texto = "Meu pai me ensinou a trabalhar. Ele era muito bom."
    resultado = memory.detectar_historia(texto)
    assert resultado["detectado"] is True


def test_nao_detectar_historia():
    texto = "Oi, tudo bem?"
    resultado = memory.detectar_historia(texto)
    assert resultado["detectado"] is False


def test_gravar_memoria_persiste_localmente(tmp_path, monkeypatch):
    monkeypatch.setattr(memory, "MEMORY_DIR", tmp_path)
    monkeypatch.setattr(memory, "BUCKET", "")
    monkeypatch.setattr(memory, "_get_s3", lambda: False)
    monkeypatch.setattr(
        memory,
        "organizar_historia",
        lambda *_args: {"titulo": "Uma lembrança", "resumo": "Resumo"},
    )

    resultado = memory.gravar_memoria(
        "dona-maria", "Quando eu era jovem, eu morava perto dos meus pais.", {}
    )

    caminho = tmp_path / "dona-maria.json"
    assert resultado["gravado"] is True
    assert json.loads(caminho.read_text(encoding="utf-8"))[0]["titulo"] == "Uma lembrança"
    assert stat.S_IMODE(caminho.stat().st_mode) == 0o600


def test_gravar_memoria_rejeita_id_invalido(tmp_path, monkeypatch):
    monkeypatch.setattr(memory, "MEMORY_DIR", tmp_path)

    with pytest.raises(ValueError, match="idoso_id inválido"):
        memory.gravar_memoria("../fora", "Quando eu era jovem e trabalhava muito.", {})
