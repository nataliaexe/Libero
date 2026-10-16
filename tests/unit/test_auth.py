import pytest

from cloud.mcp_server import auth


@pytest.fixture(autouse=True)
def contas_teste(monkeypatch):
    monkeypatch.setattr(auth, "USUARIOS", {
        "ana@libero.com": auth._criar_usuario(
            "ana@libero.com", "senha-teste-cuidador-14", "Ana", "familia", "dona-maria"
        ),
        "medico@libero.com": auth._criar_usuario(
            "medico@libero.com", "senha-teste-medico-14", "Carlos", "medico", "dona-maria"
        ),
    })


def test_autorizar_idoso_respeita_vinculo_da_sessao():
    sessao = auth.login("ana@libero.com", "senha-teste-cuidador-14")
    token = sessao["token"]
    try:
        assert auth.autorizar_idoso("gerenciar_tasks", token, "dona-maria")["idoso_id"] == "dona-maria"
        with pytest.raises(auth.AuthError):
            auth.autorizar_idoso("gerenciar_tasks", token, "outro-idoso")
    finally:
        auth.logout(token)


def test_autorizar_idoso_exige_permissao_especifica():
    sessao = auth.login("medico@libero.com", "senha-teste-medico-14")
    token = sessao["token"]
    try:
        with pytest.raises(auth.AuthError):
            auth.autorizar_idoso("gerenciar_tasks", token, "dona-maria")
    finally:
        auth.logout(token)


def test_argumentos_mcp_nao_podem_mudar_de_idoso():
    sessao = auth.login("ana@libero.com", "senha-teste-cuidador-14")
    token = sessao["token"]
    try:
        auth.autorizar("iniciar_conversa", token)
        with pytest.raises(auth.AuthError):
            auth.autorizar_argumentos(
                "iniciar_conversa", token,
                {"idoso_id": "outro-idoso", "mensagem": "oi"},
            )
        with pytest.raises(auth.AuthError, match="obrigatório"):
            auth.autorizar_argumentos("iniciar_conversa", token, {"mensagem": "oi"})
    finally:
        auth.logout(token)


def test_producao_sem_conta_admin_falha_fechado(monkeypatch):
    monkeypatch.setattr(auth, "AMBIENTE", "production")
    monkeypatch.setattr(auth, "USUARIOS", {})
    with pytest.raises(RuntimeError, match="LIBERO_USERS_JSON"):
        auth.validar_configuracao()


def test_producao_nao_aceita_tokens_demonstrativos(monkeypatch):
    monkeypatch.setattr(auth, "AMBIENTE", "production")
    monkeypatch.setattr(auth, "TOKEN_DEV", None)
    monkeypatch.setattr(auth, "TOKEN_ADMIN", None)
    assert auth.verificar_token("libero-dev-token") is None
    assert auth.verificar_token("libero-admin-token") is None


def test_usuarios_de_producao_exigem_senhas_fortes(monkeypatch):
    monkeypatch.setenv("LIBERO_USERS_JSON", '[{"email":"admin@example.com","senha":"123","nome":"Admin","role":"admin","idoso_id":"*"}]')
    with pytest.raises(RuntimeError, match="14 caracteres"):
        auth._carregar_usuarios()


def test_ticket_camera_expira_e_so_pode_ser_usado_uma_vez(monkeypatch):
    monkeypatch.setattr(auth, "USUARIOS", {
        "ana@libero.com": auth._criar_usuario(
            "ana@libero.com", "senha-teste-cuidador-14", "Ana", "familia", "dona-maria"
        ),
    })
    sessao = auth.login("ana@libero.com", "senha-teste-cuidador-14")
    try:
        ticket = auth.criar_ticket_camera(sessao["token"])
        if auth.AMBIENTE == "production":
            assert auth.consumir_ticket_camera(ticket, "wrong-token") is False
        assert auth.consumir_ticket_camera(ticket, sessao["token"]) is True
        assert auth.consumir_ticket_camera(ticket) is False
    finally:
        auth.logout(sessao["token"])


def test_token_na_url_nao_autentica():
    class RequisicaoFake:
        headers = {}
        cookies = {}
        query_params = {"token": "token-na-url"}

    assert auth.extrair_token(RequisicaoFake()) is None
