"""Authentication, authorization, and short-lived sessions for Libero."""

import hashlib
import hmac
import json
import os
import re
import secrets
import threading
import time
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

load_dotenv()

AMBIENTE = os.getenv("LIBERO_ENV", "production").strip().lower()
if AMBIENTE not in {"development", "production"}:
    raise RuntimeError("LIBERO_ENV deve ser 'development' ou 'production'.")

TOKEN_DEV = os.getenv("LIBERO_TOKEN")
TOKEN_ADMIN = os.getenv("LIBERO_ADMIN_TOKEN")
if AMBIENTE == "development":
    TOKEN_DEV = TOKEN_DEV or "libero-dev-token"
    TOKEN_ADMIN = TOKEN_ADMIN or "libero-admin-token"

_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SCRYPT_LENGTH = 32
_DUMMY_SALT = os.urandom(16)
_DUMMY_HASH = hashlib.scrypt(
    b"senha-invalida", salt=_DUMMY_SALT, n=_SCRYPT_N,
    r=_SCRYPT_R, p=_SCRYPT_P, dklen=_SCRYPT_LENGTH,
)


def _criar_usuario(email, senha, nome, role, idoso_id):
    salt = os.urandom(16)
    senha_hash = hashlib.scrypt(
        senha.encode("utf-8"), salt=salt, n=_SCRYPT_N,
        r=_SCRYPT_R, p=_SCRYPT_P, dklen=_SCRYPT_LENGTH,
    )
    return {
        "senha_hash": senha_hash,
        "salt": salt,
        "nome": nome,
        "idoso_id": idoso_id,
        "role": role,
    }


def _carregar_usuarios():
    configuracao = os.getenv("LIBERO_USERS_JSON")
    if not configuracao and AMBIENTE == "development":
        return {
            "ana@libero.com": _criar_usuario(
                "ana@libero.com", "libero123", "Ana (Filha)", "familia", "dona-maria"
            ),
            "medico@libero.com": _criar_usuario(
                "medico@libero.com", "medico123", "Dr. Carlos", "medico", "dona-maria"
            ),
            "admin@libero.com": _criar_usuario(
                "admin@libero.com", "admin123", "Admin", "admin", "*"
            ),
        }
    if not configuracao:
        return {}

    try:
        usuarios = json.loads(configuracao)
    except json.JSONDecodeError as e:
        raise RuntimeError("LIBERO_USERS_JSON precisa conter JSON válido.") from e
    if not isinstance(usuarios, list):
        raise RuntimeError("LIBERO_USERS_JSON precisa ser uma lista de usuários.")

    resultado = {}
    for usuario in usuarios:
        if not isinstance(usuario, dict):
            raise RuntimeError("Cada usuário em LIBERO_USERS_JSON precisa ser um objeto.")
        email = str(usuario.get("email", "")).strip().lower()
        senha = usuario.get("senha")
        nome = str(usuario.get("nome", "")).strip()
        role = usuario.get("role")
        idoso_id = str(usuario.get("idoso_id", "")).strip()
        if (not email or not nome or not idoso_id or not isinstance(senha, str)
                or len(senha) < 14 or role not in {"familia", "medico", "admin"}):
            raise RuntimeError(
                "Cada usuário precisa de email, nome, idoso_id, role válida e senha com ao menos 14 caracteres."
            )
        if email in resultado:
            raise RuntimeError(f"Email duplicado em LIBERO_USERS_JSON: {email}")
        if role == "admin" and idoso_id != "*":
            raise RuntimeError("Usuários admin precisam ter idoso_id='*'.")
        if role != "admin" and idoso_id == "*":
            raise RuntimeError("Somente usuários admin podem usar idoso_id='*'.")
        resultado[email] = _criar_usuario(email, senha, nome, role, idoso_id)
    return resultado


USUARIOS = _carregar_usuarios()
SESSOES = {}
_session_lock = threading.RLock()
_camera_tickets = {}
_ticket_lock = threading.Lock()


class AuthError(Exception):
    """Erro de autenticação ou autorização."""


class RateLimiter:
    """Limitador em memória para reduzir abuso em login e endpoints."""

    def __init__(self, max_requests=100, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
        self.lock = threading.Lock()
        self.max_keys = 10000

    def check(self, key):
        agora = time.monotonic()
        janela = agora - self.window_seconds
        with self.lock:
            if key not in self.requests and len(self.requests) >= self.max_keys:
                self.requests = {
                    k: [t for t in historico if t > janela]
                    for k, historico in self.requests.items()
                    if any(t > janela for t in historico)
                }
                if len(self.requests) >= self.max_keys:
                    return False
            historico = [t for t in self.requests.get(key, []) if t > janela]
            self.requests[key] = historico
            if len(historico) >= self.max_requests:
                return False
            historico.append(agora)
            return True


_rate_limiter = RateLimiter()
_login_ip_limiter = RateLimiter(max_requests=20, window_seconds=900)
_login_account_limiter = RateLimiter(max_requests=10, window_seconds=900)

FERRAMENTAS_ADMIN = [
    "chamar_emergencia", "ativar_camera", "verificar_vies", "verificar_compliance"
]
FERRAMENTAS_MEDICO = ["analisar_saude", "obter_protocolo_crise", "obter_estagio"]
FERRAMENTAS_FAMILIA = [
    "iniciar_conversa", "verificar_seguranca", "gravar_memoria",
    "notificar_familia", "gerar_mensagem_cuidado", "relatorio_diario",
    "sugerir_terapia", "verificar_lembretes"
]
FERRAMENTAS_CUIDADOR = [
    "gerenciar_tasks", "controlar_audio", "ver_camera", "controlar_camera",
    "conectar_websocket"
]
FERRAMENTAS_PUBLICAS = ["health", "listar_ferramentas"]
FERRAMENTAS_POR_IDOSO = {
    "iniciar_conversa", "verificar_seguranca", "gravar_memoria",
    "gerar_mensagem_cuidado", "notificar_familia", "relatorio_diario",
    "analisar_saude",
}


def validar_configuracao():
    """Fail closed if the server is about to run without production credentials."""
    if AMBIENTE == "development":
        return
    if not USUARIOS or not any(u["role"] == "admin" for u in USUARIOS.values()):
        raise RuntimeError(
            "Configure LIBERO_USERS_JSON com ao menos um usuário admin antes de expor o servidor."
        )
    for nome, token in (("LIBERO_TOKEN", TOKEN_DEV), ("LIBERO_ADMIN_TOKEN", TOKEN_ADMIN)):
        if token and (len(token) < 32 or token in {"libero-dev-token", "libero-admin-token"}):
            raise RuntimeError(f"{nome} deve ter ao menos 32 caracteres aleatórios.")


def login(email, senha, client_key="desconhecido"):
    """Valida credenciais e cria uma sessão aleatória com validade limitada."""
    email_normalizado = str(email).strip().lower()
    if not _login_ip_limiter.check(client_key) or not _login_account_limiter.check(email_normalizado):
        raise AuthError("Muitas tentativas de login. Aguarde antes de tentar novamente.")

    usuario = USUARIOS.get(email_normalizado)
    salt = usuario["salt"] if usuario else _DUMMY_SALT
    esperado = usuario["senha_hash"] if usuario else _DUMMY_HASH
    recebido = hashlib.scrypt(
        str(senha).encode("utf-8"), salt=salt, n=_SCRYPT_N,
        r=_SCRYPT_R, p=_SCRYPT_P, dklen=_SCRYPT_LENGTH,
    )
    if not usuario or not hmac.compare_digest(recebido, esperado):
        raise AuthError("Email ou senha inválidos")

    token = secrets.token_urlsafe(32)
    expira_em = datetime.now(timezone.utc) + timedelta(hours=12)
    sessao = {
        "email": email_normalizado,
        "nome": usuario["nome"],
        "role": usuario["role"],
        "idoso_id": usuario["idoso_id"],
        "expira_em": expira_em.isoformat(),
    }
    with _session_lock:
        expirados = [
            chave for chave, atual in SESSOES.items()
            if datetime.now(timezone.utc) > datetime.fromisoformat(atual["expira_em"])
        ]
        for chave in expirados:
            SESSOES.pop(chave, None)
        SESSOES[token] = sessao
    return {"token": token, **sessao}


def logout(token):
    if not token:
        return False
    with _session_lock:
        return SESSOES.pop(token, None) is not None


def verificar_sessao(token):
    if not token:
        return None
    with _session_lock:
        sessao = SESSOES.get(token)
        if not sessao:
            return None
        if datetime.now(timezone.utc) > datetime.fromisoformat(sessao["expira_em"]):
            SESSOES.pop(token, None)
            return None
        return dict(sessao)


def verificar_token(token):
    if not token:
        return None
    if TOKEN_ADMIN and hmac.compare_digest(token, TOKEN_ADMIN):
        return {"role": "admin", "idoso_id": "*", "nome": "Admin"}
    if TOKEN_DEV and hmac.compare_digest(token, TOKEN_DEV):
        return {"role": "familia", "idoso_id": "default", "nome": "Dev"}
    return verificar_sessao(token)


def autorizar(ferramenta, token):
    if ferramenta in FERRAMENTAS_PUBLICAS:
        return {"role": "public", "idoso_id": None}
    sessao = verificar_token(token)
    if not sessao:
        raise AuthError("Token inválido ou ausente")
    if not _rate_limiter.check(token):
        raise AuthError("Rate limit excedido")

    role = sessao["role"]
    permitido = (
        role == "admin"
        or (ferramenta in FERRAMENTAS_MEDICO and role == "medico")
        or (ferramenta in FERRAMENTAS_FAMILIA and role == "familia")
        or (ferramenta in FERRAMENTAS_CUIDADOR and role == "familia")
    )
    if not permitido:
        raise AuthError(f"Role '{role}' não pode executar '{ferramenta}'")
    return sessao


def autorizar_idoso(ferramenta, token, idoso_id):
    if not isinstance(idoso_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", idoso_id):
        raise AuthError("idoso_id inválido")
    sessao = autorizar(ferramenta, token)
    if sessao["idoso_id"] not in ("*", idoso_id):
        raise AuthError("Acesso não autorizado")
    return sessao


def autorizar_argumentos(ferramenta, token, argumentos):
    if ferramenta in FERRAMENTAS_POR_IDOSO:
        idoso_id = argumentos.get("idoso_id") if isinstance(argumentos, dict) else None
        if not isinstance(idoso_id, str) or not idoso_id.strip():
            raise AuthError("idoso_id é obrigatório")
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", idoso_id):
            raise AuthError("idoso_id inválido")
        sessao = verificar_token(token)
        if not sessao or sessao["idoso_id"] not in ("*", idoso_id):
            raise AuthError("Acesso não autorizado")
        return sessao
    return verificar_token(token)


def criar_ticket_camera(token):
    sessao = autorizar("ver_camera", token)
    ticket = secrets.token_urlsafe(32)
    with _ticket_lock:
        agora = time.monotonic()
        expirados = [
            chave for chave, (_, expira_em) in _camera_tickets.items()
            if expira_em <= agora
        ]
        for chave in expirados:
            _camera_tickets.pop(chave, None)
        _camera_tickets[ticket] = (
            sessao["idoso_id"], time.monotonic() + 30,
            hashlib.sha256(token.encode("utf-8")).digest(),
        )
    return ticket


def consumir_ticket_camera(ticket, token=None):
    if not ticket:
        return False
    with _ticket_lock:
        registro = _camera_tickets.get(ticket)
        if not registro:
            return False
        if registro[1] <= time.monotonic():
            _camera_tickets.pop(ticket, None)
            return False
        if AMBIENTE == "production":
            if not token:
                return False
            token_hash = hashlib.sha256(token.encode("utf-8")).digest()
            if not hmac.compare_digest(registro[2], token_hash):
                return False
        _camera_tickets.pop(ticket, None)
        return True


def extrair_token(request):
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    token = request.headers.get("X-Libero-Token")
    if token:
        return token
    return request.cookies.get("libero_session")
