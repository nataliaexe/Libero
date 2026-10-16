from cloud.agents import safety
from cloud.mcp_server import tools


class GovernancaFake:
    def auditar(self, *args, **kwargs):
        return None


def test_ferramenta_mcp_nao_confirma_queda_com_audio_isolado(monkeypatch):
    resultado = tools.verificar_seguranca(
        "dona-maria",
        features_audio={"energia_max": 0.9, "duracao": 0.5},
    )

    assert resultado["evento"] is None
    assert resultado["nivel"] == 0


def test_ferramenta_mcp_encaminha_audio_e_visao_ao_detector(monkeypatch):
    monkeypatch.setattr(safety, "_get_bedrock", lambda: False)
    monkeypatch.setattr(tools.governance, "Governanca", lambda: GovernancaFake())

    resultado = tools.verificar_seguranca(
        "dona-maria",
        features_audio={"energia_max": 0.9, "duracao": 0.5},
        features_visao={"angulo_corpo": 80, "velocidade_queda": 0.8},
    )

    assert resultado["evento"]["tipo"] == "queda"
    assert resultado["evento"]["score_nao_calibrado"] is True
    assert resultado["acoes_externas_executadas"] is False
    assert all(
        acao.get("status") != "executada"
        for acao in resultado["acoes"]
        if acao["tipo"] != "voz"
    )


def test_verificar_seguranca_marca_chamada_textual_sem_fingir_execucao(monkeypatch):
    monkeypatch.setattr(safety, "_get_bedrock", lambda: False)
    monkeypatch.setattr(tools.governance, "Governanca", lambda: GovernancaFake())

    resultado = tools.verificar_seguranca("dona-maria", texto="Socorro, caí!")

    assert resultado["evento"]["tipo"] == "emergencia_texto"
    assert resultado["acoes_externas_executadas"] is False
    samu = next(a for a in resultado["acoes"] if a["tipo"] == "chamar_emergencia")
    assert samu["status"] == "proposta_nao_executada"
