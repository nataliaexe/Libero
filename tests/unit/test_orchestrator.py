from cloud.agents import orchestrator


class StoreFake:
    def __init__(self):
        self.mensagens = []

    def adicionar_mensagem(self, *args, **kwargs):
        self.mensagens.append((args, kwargs))

    def listar_mensagens(self, _idoso_id, limite=50):
        itens = [
            {"autor": args[1], "texto": args[2], "metadata": kwargs.get("metadata", {})}
            for args, kwargs in self.mensagens
        ]
        return list(reversed(itens))[:limite]


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
    assert store.mensagens[0][1]["tipo"] == "normal"
    assert store.mensagens[1][1]["tipo"] == "emergencia"


def test_contexto_do_orquestrador_desativa_camera_por_padrao():
    orq = orchestrator.Orquestrador("dona-maria")

    assert orq.contexto["camera_autorizada"] is False


def test_memoria_so_marca_resposta_no_chat(monkeypatch):
    store = StoreFake()
    monkeypatch.setattr(orchestrator, "get_store", lambda: store)
    monkeypatch.setattr(
        orchestrator.memory,
        "detectar_historia",
        lambda _texto: {"detectado": True, "confianca": 0.8},
    )
    monkeypatch.setattr(
        orchestrator.memory,
        "gravar_memoria",
        lambda *_args: {"gravado": True, "memoria": {"id": "mem-1", "titulo": "História"}},
    )
    monkeypatch.setattr(
        orchestrator.companion,
        "conversar_com_provedor",
        lambda *_args: {"resposta": "Que lembrança bonita.", "provedor": "offline"},
    )

    orchestrator.Orquestrador("dona-maria").processar(
        "Quando eu era jovem, dançava com meu marido."
    )

    assert store.mensagens[0][1]["tipo"] == "normal"
    assert store.mensagens[1][1]["tipo"] == "memoria"


def test_conversa_seguinte_recebe_historico_persistido(monkeypatch):
    store = StoreFake()
    contextos = []
    monkeypatch.setattr(orchestrator, "get_store", lambda: store)
    monkeypatch.setattr(orchestrator.memory, "listar_memorias", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(orchestrator.memory, "detectar_historia", lambda _texto: {"detectado": False})
    monkeypatch.setattr(
        orchestrator.companion,
        "conversar_com_provedor",
        lambda texto, contexto: contextos.append(contexto) or {
            "resposta": f"I heard: {texto}", "provedor": "offline"
        },
    )
    orq = orchestrator.Orquestrador("dona-maria", {"nome": "Maria", "language": "en"})

    orq.processar("My dog was named Lucky.")
    orq.processar("What was my dog's name?")

    assert [item["content"] for item in contextos[1]["historico"]] == [
        "My dog was named Lucky.", "I heard: My dog was named Lucky."
    ]
