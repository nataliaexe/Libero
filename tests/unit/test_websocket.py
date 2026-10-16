import asyncio

from cloud.mcp_server.websocket import GerenciadorWebSocket


class FakeWebSocket:
    def __init__(self):
        self.recebidos = []

    async def accept(self):
        pass

    async def send_json(self, evento):
        self.recebidos.append(evento)


def test_broadcast_limita_eventos_ao_idoso_da_conexao():
    async def executar():
        gerenciador = GerenciadorWebSocket()
        maria = FakeWebSocket()
        joao = FakeWebSocket()
        await gerenciador.conectar(maria, idoso_id="dona-maria")
        await gerenciador.conectar(joao, idoso_id="seu-joao")

        await gerenciador.broadcast({"tipo": "alerta"}, idoso_id="dona-maria")

        assert [e["tipo"] for e in maria.recebidos] == ["alerta"]
        assert joao.recebidos == []

    asyncio.run(executar())


def test_replay_recente_respeita_escopo():
    async def executar():
        gerenciador = GerenciadorWebSocket()
        await gerenciador.broadcast({"tipo": "maria"}, idoso_id="dona-maria")
        await gerenciador.broadcast({"tipo": "joao"}, idoso_id="seu-joao")

        maria = FakeWebSocket()
        await gerenciador.conectar(maria, idoso_id="dona-maria")

        assert [e["tipo"] for e in maria.recebidos] == ["maria"]

    asyncio.run(executar())


def test_conexoes_websocket_tem_limites():
    async def executar():
        gerenciador = GerenciadorWebSocket()
        gerenciador.max_conexoes_por_idoso = 1
        primeira = FakeWebSocket()
        segunda = FakeWebSocket()

        assert await gerenciador.conectar(primeira, idoso_id="dona-maria") is True
        assert await gerenciador.conectar(segunda, idoso_id="dona-maria") is False

    asyncio.run(executar())
