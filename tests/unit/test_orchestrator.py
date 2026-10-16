from cloud.agents import orchestrator


class StoreFake:
    def __init__(self):
        self.mensagens = []

    def adicionar_mensagem(self, *args, **kwargs):
        self.mensagens.append((args, kwargs))


def test_orquestrador_persiste_evento_de_seguranca(monkeypatch):
    store = StoreFake()
    monkeypatch.setattr(orchestrator, "get_store", lambda: store)
    monkeypatch.setattr(
        orchestrator.safety,
        "agir",
        lambda evento, contexto: {
            "nivel": 3,
            "confianca": 0.9,
            "acoes": [{"tipo": "voz", "conteudo": "Estou aqui com você."}],
        },
    )

    resultado = orchestrator.Orquestrador("dona-maria").processar("Socorro, caí!")

    assert resultado["acoes_externas_executadas"] is False
    assert len(store.mensagens) == 2
    assert store.mensagens[0][0][1:3] == ("idoso", "Socorro, caí!")
    assert store.mensagens[1][0][1:3] == ("libero", "Estou aqui com você.")
    assert store.mensagens[0][1]["tipo"] == "emergencia"
