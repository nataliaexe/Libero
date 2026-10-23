"""
Libero - MCP Server com login
"""

import os
import json
import secrets
from contextlib import asynccontextmanager
from urllib.parse import urlparse
from datetime import datetime, timezone
from fastapi import FastAPI, Request, Query, Response
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from cloud.mcp_server import tools
from cloud.mcp_server import auth
from cloud.agents import memory as memory_agent

load_dotenv()

if auth.AMBIENTE == "development":
    ALLOWED_ORIGINS = [
        "http://localhost:8080", "http://127.0.0.1:8080",
        "http://localhost:3000", "http://127.0.0.1:3000",
        "http://localhost:5500", "http://127.0.0.1:5500", "null",
    ]
else:
    ALLOWED_ORIGINS = [
        origin.strip().rstrip("/")
        for origin in os.getenv("LIBERO_ALLOWED_ORIGINS", "").split(",")
        if origin.strip()
    ]


@asynccontextmanager
async def lifespan(app):
    auth.validar_configuracao()
    if auth.AMBIENTE == "development" and MCP_HOST not in {"127.0.0.1", "localhost", "::1"}:
        raise RuntimeError("O modo development só pode escutar em loopback.")
    if auth.AMBIENTE == "production" and not ALLOWED_ORIGINS:
        raise RuntimeError(
            "Configure LIBERO_ALLOWED_ORIGINS com a origem HTTPS do dashboard."
        )
    if auth.AMBIENTE == "production" and any(
        urlparse(origin).scheme != "https"
        or not urlparse(origin).hostname
        or urlparse(origin).path not in {"", "/"}
        or "*" in origin
        for origin in ALLOWED_ORIGINS
    ):
        raise RuntimeError("LIBERO_ALLOWED_ORIGINS aceita somente origens HTTPS explícitas.")
    yield


LIBERO_VERSION = "1.5.0"
MCP_PROTOCOL_VERSION = "2025-11-25"

app = FastAPI(title="Libero MCP Server", version=LIBERO_VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization", "Content-Type", "X-Libero-Token",
        "MCP-Protocol-Version", "Last-Event-ID",
    ],
)

MCP_PORT = int(os.getenv("MCP_PORT", "8080"))
MCP_HOST = os.getenv("MCP_HOST", "127.0.0.1")


@app.middleware("http")
async def security_headers(request, call_next):
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > 1_048_576:
                return JSONResponse({"error": "Requisição muito grande"}, status_code=413)
        except ValueError:
            return JSONResponse({"error": "Content-Length inválido"}, status_code=400)

    if (auth.AMBIENTE == "production"
            and request.method in {"POST", "PUT", "PATCH", "DELETE"}
            and request.cookies.get("libero_session")
            and not request.headers.get("Authorization", "").startswith("Bearer ")
            and not request.headers.get("X-Libero-Token")):
        origin = request.headers.get("Origin", "").rstrip("/")
        if origin not in ALLOWED_ORIGINS:
            return JSONResponse({"error": "Origem não autorizada"}, status_code=403)

    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    return response


# ============================================================
# MODELOS
# ============================================================

class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    senha: str = Field(min_length=1, max_length=256)


# ============================================================
# LOGIN
# ============================================================

@app.post("/auth/login")
async def login_endpoint(req: LoginRequest, request: Request):
    """Login do usuário."""
    try:
        sessao = auth.login(
            req.email, req.senha, request.client.host if request.client else "desconhecido"
        )
        token = sessao.pop("token")
        resposta = {"status": "success", **sessao}
        if auth.AMBIENTE == "development":
            resposta["token"] = token
        response = JSONResponse(resposta)
        response.set_cookie(
            "libero_session", token, max_age=12 * 60 * 60,
            httponly=True, secure=auth.AMBIENTE == "production",
            samesite="strict", path="/",
        )
        return response
    except auth.AuthError as e:
        return JSONResponse(
            {"status": "error", "error": str(e)},
            status_code=401
        )


@app.post("/auth/logout")
async def logout_endpoint(request: Request):
    """Logout."""
    token = auth.extrair_token(request)
    encerrada = auth.logout(token)
    response = JSONResponse({"status": "success", "session_encerrada": encerrada})
    response.delete_cookie(
        "libero_session", path="/", secure=auth.AMBIENTE == "production",
        httponly=True, samesite="strict",
    )
    return response


@app.get("/auth/me")
async def me_endpoint(request: Request):
    """Retorna dados da sessão atual."""
    token = auth.extrair_token(request)
    sessao = auth.verificar_sessao(token)
    if not sessao:
        return JSONResponse({"error": "Não autenticado"}, status_code=401)
    return {"status": "success", **sessao}


# ============================================================
# ENDPOINTS PÚBLICOS
# ============================================================

@app.get("/")
async def root():
    return {
        "name": "Libero MCP Server",
        "version": LIBERO_VERSION,
        "protocol_version": MCP_PROTOCOL_VERSION,
        "transport": "streamable-http-json",
        "ferramentas": len(tools.FERRAMENTAS)
    }


@app.get("/health")
async def health():
    return {"status": "ok", "ferramentas": len(tools.FERRAMENTAS)}


# ============================================================
# ENDPOINTS AUTENTICADOS
# ============================================================

@app.get("/mcp/tools")
async def listar_tools(request: Request):
    token = auth.extrair_token(request)
    try:
        auth.autorizar("listar_ferramentas", token)
    except auth.AuthError as e:
        return JSONResponse({"error": str(e)}, status_code=401)
    
    return {"tools": tools.listar_ferramentas()}


@app.post("/mcp/tools/{tool_name}")
async def executar_tool(tool_name: str, request: Request):
    token = auth.extrair_token(request)
    
    try:
        auth_info = auth.autorizar(tool_name, token)
    except auth.AuthError as e:
        return JSONResponse({"error": str(e)}, status_code=401)
    
    try:
        body = await request.json()
    except Exception:
        body = {}

    try:
        auth_info = auth.autorizar_argumentos(tool_name, token, body)
    except auth.AuthError as e:
        return JSONResponse({"error": str(e)}, status_code=403)
    
    print(f"[Libero MCP] [{auth_info['role']}] {tool_name}")
    
    resultado = tools.executar(tool_name, body)
    
    return JSONResponse({
        "status": "success" if "erro" not in resultado else "error",
        "tool": tool_name,
        "role": auth_info["role"],
        "result": resultado
    })


def _mcp_jsonrpc_error(request_id, code, message, status_code=200):
    return JSONResponse(
        {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}},
        status_code=status_code,
    )


def _mcp_origin_allowed(request: Request):
    origin = request.headers.get("origin")
    return not origin or origin.rstrip("/") in ALLOWED_ORIGINS


@app.get("/mcp")
async def mcp_get(request: Request):
    """This server uses JSON responses and does not open a server SSE stream."""
    if not _mcp_origin_allowed(request):
        return Response(status_code=403)
    return Response(status_code=405, headers={"Allow": "POST"})


@app.post("/mcp")
async def mcp_handler(request: Request):
    """MCP Streamable HTTP endpoint using JSON responses (no SSE stream)."""
    if not _mcp_origin_allowed(request):
        return _mcp_jsonrpc_error(None, -32000, "Origin não autorizado", 403)

    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if content_type != "application/json":
        return JSONResponse({"error": "Content-Type deve ser application/json"}, status_code=415)
    accepted_types = {
        item.split(";", 1)[0].strip().lower()
        for item in request.headers.get("accept", "").split(",")
    }
    if not {"application/json", "text/event-stream"}.issubset(accepted_types):
        return JSONResponse({"error": "Accept deve incluir application/json e text/event-stream"}, status_code=406)

    try:
        body = await request.json()
    except Exception:
        return _mcp_jsonrpc_error(None, -32700, "Parse error", 400)

    if not isinstance(body, dict) or body.get("jsonrpc") != "2.0":
        return _mcp_jsonrpc_error(None, -32600, "Invalid Request", 400)

    metodo = body.get("method")
    params = body.get("params", {})
    request_id = body.get("id")
    if not isinstance(metodo, str) or not isinstance(params, dict):
        return _mcp_jsonrpc_error(request_id, -32600, "Invalid Request", 400)

    if metodo != "initialize" and request.headers.get("mcp-protocol-version") != MCP_PROTOCOL_VERSION:
        return _mcp_jsonrpc_error(request_id, -32600, "MCP-Protocol-Version ausente ou não suportada", 400)

    # JSON-RPC notifications never receive a JSON-RPC response. MCP requires
    # 202 with an empty body when the server accepts a notification.
    if "id" not in body:
        if metodo in {
            "notifications/initialized",
            "notifications/cancelled",
            "notifications/progress",
        } or metodo.startswith("notifications/"):
            return Response(status_code=202)
        return _mcp_jsonrpc_error(None, -32600, "Invalid Request", 400)

    if request_id is None or isinstance(request_id, (dict, list, bool)):
        return _mcp_jsonrpc_error(None, -32600, "Invalid Request", 400)

    if metodo == "initialize":
        client_version = params.get("protocolVersion")
        client_info = params.get("clientInfo")
        if (not isinstance(client_version, str)
                or not isinstance(params.get("capabilities"), dict)
                or not isinstance(client_info, dict)
                or not isinstance(client_info.get("name"), str)
                or not isinstance(client_info.get("version"), str)):
            return _mcp_jsonrpc_error(request_id, -32602, "Parâmetros de initialize inválidos")
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "libero", "version": LIBERO_VERSION},
                "instructions": (
                    "Libero is a research prototype for home-care support. "
                    "Safety signals are experimental and do not contact emergency services."
                ),
            },
        }

    token = auth.extrair_token(request)
    if metodo == "ping":
        return {"jsonrpc": "2.0", "id": request_id, "result": {}}

    if metodo == "tools/list":
        try:
            auth.autorizar("listar_ferramentas", token)
        except auth.AuthError as e:
            return _mcp_jsonrpc_error(request_id, -32001, str(e))
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"tools": tools.listar_ferramentas()},
        }

    if metodo == "tools/call":
        nome = params.get("name")
        argumentos = params.get("arguments", {})
        if not isinstance(nome, str) or not isinstance(argumentos, dict):
            return _mcp_jsonrpc_error(request_id, -32602, "Parâmetros de tools/call inválidos")
        try:
            auth.autorizar(nome, token)
            auth.autorizar_argumentos(nome, token, argumentos)
        except auth.AuthError as e:
            return _mcp_jsonrpc_error(request_id, -32001, str(e))

        resultado = tools.executar(nome, argumentos)
        falhou = isinstance(resultado, dict) and "erro" in resultado
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [{"type": "text", "text": json.dumps(resultado, ensure_ascii=False)}],
                "isError": falhou,
            },
        }

    return _mcp_jsonrpc_error(request_id, -32601, f"Método desconhecido: {metodo}")




# ============================================================
# CÂMERA AO VIVO
# ============================================================

from cloud.mcp_server.camera import get_camera


@app.post("/camera/stream-ticket")
async def camera_stream_ticket(request: Request):
    token = auth.extrair_token(request)
    try:
        ticket = auth.criar_ticket_camera(token)
    except auth.AuthError as e:
        return JSONResponse({"error": str(e)}, status_code=401)
    return {"ticket": ticket, "expires_in": 30}


@app.get("/camera/stream")
async def camera_stream(request: Request):
    """Stream MJPEG da câmera."""
    token = auth.extrair_token(request)
    if auth.AMBIENTE == "production":
        try:
            auth.autorizar("ver_camera", token)
        except auth.AuthError:
            return JSONResponse({"error": "Não autenticado"}, status_code=401)
    if not auth.consumir_ticket_camera(
        request.query_params.get("ticket"), token
    ):
        return JSONResponse({"error": "Ticket inválido ou expirado"}, status_code=401)

    camera = get_camera(camera_id=-1)
    return StreamingResponse(
        camera.gerar_mjpeg(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@app.get("/camera/status")
async def camera_status(request: Request):
    """Status da câmera."""
    token = auth.extrair_token(request)
    try:
        auth.autorizar("ver_camera", token)
    except auth.AuthError as e:
        return JSONResponse({"error": str(e)}, status_code=401)

    camera = get_camera(camera_id=-1)
    return {
        "rodando": camera.rodando,
        "camera_id": camera.camera_id,
        "fps": camera.fps
    }


@app.post("/camera/start")
async def camera_start(request: Request):
    """Inicia modo placeholder (câmera é usada pelo edge em :8081)."""
    token = auth.extrair_token(request)
    try:
        auth.autorizar("ativar_camera", token)
    except auth.AuthError as e:
        return JSONResponse({"error": str(e)}, status_code=401)
    
    from cloud.mcp_server.camera import get_camera
    camera = get_camera(camera_id=-1)
    return {
        "status": "ok",
        "rodando": True,
        "modo": "placeholder",
        "edge_stream_url": "http://localhost:8081/stream"
    }

@app.post("/camera/stop")
async def camera_stop(request: Request):
    """Para a câmera."""
    token = auth.extrair_token(request)
    try:
        auth.autorizar("controlar_camera", token)
    except auth.AuthError as e:
        return JSONResponse({"error": str(e)}, status_code=401)
    
    camera = get_camera(camera_id=-1)
    camera.parar()
    return {"status": "ok", "rodando": camera.rodando}




# ============================================================
# CHAT E HISTÓRICO
# ============================================================

from cloud.mcp_server.chat import get_store


@app.get("/chat/{idoso_id}/mensagens")
async def listar_mensagens(
    idoso_id: str,
    request: Request,
    limite: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0, le=100000),
):
    """Lista mensagens do idoso."""
    token = auth.extrair_token(request)
    try:
        auth.autorizar_idoso("iniciar_conversa", token, idoso_id)
    except auth.AuthError as e:
        return JSONResponse({"error": str(e)}, status_code=401)
    
    store = get_store()
    mensagens = store.listar_mensagens(idoso_id, limite, offset)
    stats = store.estatisticas(idoso_id)
    
    return {
        "idoso_id": idoso_id,
        "mensagens": mensagens,
        "estatisticas": stats
    }


@app.get("/chat/{idoso_id}/memorias")
async def listar_memorias_chat(idoso_id: str, request: Request):
    """Lista as histórias persistidas pelo agente de memória."""
    token = auth.extrair_token(request)
    try:
        auth.autorizar_idoso("gravar_memoria", token, idoso_id)
    except auth.AuthError as e:
        return JSONResponse({"error": str(e)}, status_code=401)
    
    return {
        "idoso_id": idoso_id,
        "memorias": memory_agent.listar_memorias(idoso_id, limite=100)
    }


@app.get("/chat/{idoso_id}/emergencias")
async def listar_emergencias(idoso_id: str, request: Request):
    """Lista emergências."""
    token = auth.extrair_token(request)
    try:
        auth.autorizar_idoso("verificar_seguranca", token, idoso_id)
    except auth.AuthError as e:
        return JSONResponse({"error": str(e)}, status_code=401)
    
    store = get_store()
    return {
        "idoso_id": idoso_id,
        "emergencias": store.listar_emergencias(idoso_id)
    }


@app.post("/chat/{idoso_id}/mensagem")
async def enviar_mensagem(idoso_id: str, request: Request):
    """Cuidador envia mensagem para o Libero responder ao idoso."""
    token = auth.extrair_token(request)
    try:
        auth.autorizar_idoso("iniciar_conversa", token, idoso_id)
    except auth.AuthError as e:
        return JSONResponse({"error": str(e)}, status_code=401)
    
    try:
        body = await request.json()
    except Exception:
        body = {}
    
    if not isinstance(body, dict):
        return JSONResponse({"error": "Corpo da requisição inválido"}, status_code=400)
    texto = body.get("texto", "")
    if not isinstance(texto, str):
        return JSONResponse({"error": "Texto inválido"}, status_code=400)
    texto = texto.strip()
    if not texto:
        return JSONResponse({"error": "Texto vazio"}, status_code=400)
    if len(texto) > 2000:
        return JSONResponse({"error": "Texto excede 2000 caracteres"}, status_code=413)
    
    store = get_store()
    store.adicionar_mensagem(idoso_id, "cuidador", texto)
    
    from cloud.agents import companion
    mensagem_para_idoso = (
        f"[Mensagem do cuidador] {texto}\n"
        "Gere uma resposta que o idoso possa ouvir, considerando que veio do cuidador."
    )
    resposta = companion.conversar(mensagem_para_idoso, {"nome": idoso_id})
    
    store.adicionar_mensagem(idoso_id, "libero", resposta)
    
    return {
        "idoso_id": idoso_id,
        "resposta": resposta
    }


# ============================================================
# WEBSOCKET
# ============================================================

from fastapi import WebSocket, WebSocketDisconnect
from cloud.mcp_server.websocket import gerenciador_ws


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Endpoint WebSocket para sincronização em tempo real."""
    token = auth.extrair_token_websocket(websocket)
    origin = websocket.headers.get("origin", "").rstrip("/")
    idoso_id = websocket.query_params.get("idoso_id")

    # Em development, permite conexão sem autenticação
    if auth.AMBIENTE == "development":
        print("[Libero WS] Development mode: conexão sem autenticação")
        sessao = {"role": "admin", "idoso_id": "*", "nome": "Dev"}
        idoso_id = idoso_id or "*"
    else:
        try:
            if origin and origin not in ALLOWED_ORIGINS:
                raise auth.AuthError("Origem não autorizada")

            sessao = auth.autorizar("conectar_websocket", token)
            if (websocket.cookies.get("libero_session") and not origin):
                raise auth.AuthError("Origem obrigatória")
            if sessao["idoso_id"] == "*":
                idoso_id = idoso_id or "*"
            else:
                auth.autorizar_idoso("conectar_websocket", token, idoso_id or sessao["idoso_id"])
                idoso_id = sessao["idoso_id"]
        except auth.AuthError as e:
            print(f"[Libero WS] Auth error: {e}")
            await websocket.close(code=1008)
            return

    conectado = await gerenciador_ws.conectar(
        websocket, cliente_id=idoso_id, idoso_id=idoso_id
    )
    if not conectado:
        await websocket.close(code=1013)
        return
    
    try:
        while True:
            # Receber mensagem do cliente
            data = await websocket.receive_text()
            if len(data) > 65536:
                await websocket.close(code=1009)
                break
            try:
                auth.autorizar_idoso(
                    "conectar_websocket", token,
                    idoso_id if idoso_id != "*" else "*",
                )
            except auth.AuthError:
                await websocket.close(code=1008)
                break
            
            try:
                msg = json.loads(data)
            except Exception:
                msg = {"tipo": "texto", "conteudo": data}
            
            # Broadcast para todos
            await gerenciador_ws.broadcast({
                "tipo": "mensagem_cliente",
                "payload": msg
            }, idoso_id=None if idoso_id == "*" else idoso_id)
    except WebSocketDisconnect:
        gerenciador_ws.desconectar(websocket)
    except Exception as e:
        print(f"[Libero WS] Erro: {e}")
        gerenciador_ws.desconectar(websocket)


@app.get("/ws/status")
async def ws_status(request: Request):
    """Status do WebSocket."""
    token = auth.extrair_token(request)
    try:
        auth.autorizar("conectar_websocket", token)
    except auth.AuthError as e:
        return JSONResponse({"error": str(e)}, status_code=401)
    return gerenciador_ws.status()


@app.post("/ws/broadcast")
async def ws_broadcast(request: Request):
    """
    Endpoint HTTP para o Libero (edge) enviar eventos
    para todos os clientes conectados.
    """
    token = auth.extrair_token(request)
    try:
        auth_info = auth.autorizar("broadcast", token)
    except auth.AuthError as e:
        return JSONResponse({"error": str(e)}, status_code=401)
    
    try:
        evento = await request.json()
    except Exception:
        evento = {}
    
    idoso_id = auth_info["idoso_id"]
    await gerenciador_ws.broadcast(
        evento, idoso_id=None if idoso_id == "*" else idoso_id
    )
    return {"status": "ok", "clientes": len(gerenciador_ws.conexoes)}
# ============================================================
# CONTROLE DE ÁUDIO (microfone)
# ============================================================

from cloud.mcp_server import audio as audio_ctrl


@app.get("/audio/status")
async def audio_status():
    """Status do microfone (público — só info de saúde do sistema)."""
    from cloud.mcp_server import audio as audio_ctrl
    return audio_ctrl.status()

@app.post("/audio/start")
async def audio_start(request: Request):
    """Liga o microfone."""
    token = auth.extrair_token(request)
    try:
        auth.autorizar("controlar_audio", token)
    except auth.AuthError as e:
        return JSONResponse({"error": str(e)}, status_code=401)
    
    ok = audio_ctrl.iniciar()
    return {"status": "ok" if ok else "ja_rodando", **audio_ctrl.status()}


@app.post("/audio/stop")
async def audio_stop(request: Request):
    """Desliga o microfone (mute)."""
    token = auth.extrair_token(request)
    try:
        auth.autorizar("controlar_audio", token)
    except auth.AuthError as e:
        return JSONResponse({"error": str(e)}, status_code=401)
    
    ok = audio_ctrl.parar()
    return {"status": "ok" if ok else "ja_parado", **audio_ctrl.status()}


# ============================================================
# TASKS E REMÉDIOS
# ============================================================

from cloud.mcp_server.tasks import get_store as get_task_store


@app.get("/tasks/{idoso_id}")
async def listar_tasks(idoso_id: str, request: Request):
    token = auth.extrair_token(request)
    try:
        auth.autorizar_idoso("gerenciar_tasks", token, idoso_id)
    except auth.AuthError as e:
        return JSONResponse({"error": str(e)}, status_code=401)

    store = get_task_store()
    return {"idoso_id": idoso_id, "tasks": store.listar(idoso_id)}


@app.post("/tasks/{idoso_id}")
async def criar_task(idoso_id: str, request: Request):
    token = auth.extrair_token(request)
    try:
        auth.autorizar_idoso("gerenciar_tasks", token, idoso_id)
    except auth.AuthError as e:
        return JSONResponse({"error": str(e)}, status_code=401)

    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "JSON inválido"}, status_code=400)
    if not isinstance(body, dict):
        return JSONResponse({"error": "Corpo da requisição inválido"}, status_code=400)
    titulo = body.get("titulo", "")
    hora = body.get("hora", "")
    tipo = body.get("tipo", "remedio")
    if not isinstance(titulo, str) or not titulo.strip() or len(titulo) > 160:
        return JSONResponse({"error": "Título obrigatório, com até 160 caracteres"}, status_code=400)
    if not isinstance(hora, str) or len(hora) > 40:
        return JSONResponse({"error": "Hora inválida"}, status_code=400)
    if not isinstance(tipo, str) or tipo not in {"remedio", "refeicao", "agua", "atividade", "outro"}:
        return JSONResponse({"error": "Tipo de tarefa inválido"}, status_code=400)
    store = get_task_store()
    task = store.criar(
        idoso_id,
        titulo.strip(),
        hora,
        tipo,
    )
    return {"task": task}


@app.put("/tasks/{idoso_id}/{task_id}")
async def atualizar_task(idoso_id: str, task_id: str, request: Request):
    token = auth.extrair_token(request)
    try:
        auth.autorizar_idoso("gerenciar_tasks", token, idoso_id)
    except auth.AuthError as e:
        return JSONResponse({"error": str(e)}, status_code=401)

    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "JSON inválido"}, status_code=400)
    if not isinstance(body, dict):
        return JSONResponse({"error": "Corpo da requisição inválido"}, status_code=400)
    status = body.get("status", "feito")
    if status not in {"pendente", "feito", "ignorado"}:
        return JSONResponse({"error": "Status inválido"}, status_code=400)
    task = get_task_store().atualizar(idoso_id, task_id, status)
    if not task:
        return JSONResponse({"error": "Task não encontrada"}, status_code=404)
    return {"task": task}


@app.delete("/tasks/{idoso_id}/{task_id}")
async def remover_task(idoso_id: str, task_id: str, request: Request):
    token = auth.extrair_token(request)
    try:
        auth.autorizar_idoso("gerenciar_tasks", token, idoso_id)
    except auth.AuthError as e:
        return JSONResponse({"error": str(e)}, status_code=401)

    get_task_store().remover(idoso_id, task_id)
    return {"status": "ok"}


# ============================================================
# DISPOSITIVOS (pareamento TV/outros)
# ============================================================

_dispositivos_store = {}

@app.get("/dispositivos/{idoso_id}")
async def listar_dispositivos(idoso_id: str, request: Request):
    """Lista dispositivos emparelhados com o idoso."""
    token = auth.extrair_token(request)
    try:
        auth.autorizar_idoso("gerenciar_tasks", token, idoso_id)
    except auth.AuthError as e:
        return JSONResponse({"error": str(e)}, status_code=401)

    dispositivos = _dispositivos_store.get(idoso_id, [])
    return {"idoso_id": idoso_id, "dispositivos": dispositivos}


@app.post("/dispositivos/{idoso_id}/parear")
async def gerar_codigo_pareamento(idoso_id: str, request: Request):
    """Gera código de pareamento para novo dispositivo."""
    token = auth.extrair_token(request)
    try:
        auth.autorizar_idoso("gerenciar_tasks", token, idoso_id)
    except auth.AuthError as e:
        return JSONResponse({"error": str(e)}, status_code=401)

    codigo = secrets.token_urlsafe(6).upper()
    _dispositivos_store.setdefault(idoso_id, [])
    return {"codigo": codigo, "expira_em": 300}


@app.post("/dispositivos/{idoso_id}/conectar")
async def conectar_dispositivo(idoso_id: str, request: Request):
    """Conecta dispositivo usando código de pareamento."""
    token = auth.extrair_token(request)
    try:
        auth.autorizar_idoso("gerenciar_tasks", token, idoso_id)
    except auth.AuthError as e:
        return JSONResponse({"error": str(e)}, status_code=401)

    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "JSON inválido"}, status_code=400)
    if not isinstance(body, dict):
        return JSONResponse({"error": "Corpo da requisição inválido"}, status_code=400)

    codigo = body.get("codigo", "")
    nome = body.get("nome", "Dispositivo Desconhecido")

    # Em produção, validar código contra store temporário
    # Por agora, aceita qualquer código para demonstração
    dispositivo = {
        "id": os.urandom(4).hex(),
        "nome": nome,
        "ativo": True,
        "ultimo_acesso": datetime.now(timezone.utc).isoformat(),
    }
    _dispositivos_store.setdefault(idoso_id, []).append(dispositivo)
    return {"dispositivo": dispositivo}


# TESTE DE EMERGÊNCIA (para demonstrar)
# ============================================================

class TesteEmergenciaRequest(BaseModel):
    idoso_id: str = "dona-maria"
    evento: str = "queda"
    local: str = "quarto"


@app.post("/teste/emergencia")
async def teste_emergencia(req: TesteEmergenciaRequest):
    """Dispara emergência de teste (para demonstração)."""
    from cloud.mcp_server.websocket import gerenciador_ws
    from datetime import datetime, timezone
    
    await gerenciador_ws.broadcast({
        "tipo": "emergencia",
        "idoso_id": req.idoso_id,
        "evento": req.evento,
        "confianca": 0.95,
        "local": req.local,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "texto": f"Emergência de teste: {req.evento}"
    })
    
    return {"status": "ok", "enviado": True}


if __name__ == "__main__":
    import uvicorn
    print(f"[Libero MCP] Iniciando em {MCP_HOST}:{MCP_PORT}")
    print(f"[Libero MCP] Ferramentas: {len(tools.FERRAMENTAS)}")
    print(f"[Libero MCP] Login: POST /auth/login")
    uvicorn.run(
        app, host=MCP_HOST, port=MCP_PORT,
        ws_max_size=65536, ws_max_queue=16, limit_concurrency=256,
    )


# ============================================================
# EVENTOS SONOROS E VISUAIS
# ============================================================

@app.get("/eventos/{idoso_id}")
async def listar_eventos(idoso_id: str, request: Request, limite: int = 50):
    """Lista eventos sonoros e visuais do idoso."""
    token = auth.extrair_token(request)
    try:
        auth.autorizar("iniciar_conversa", token)
    except auth.AuthError as e:
        return JSONResponse({"error": str(e)}, status_code=401)
    
    from cloud.mcp_server.chat import get_store
    store = get_store()
    
    # Filtrar mensagens do tipo sistema (eventos)
    todas = store.listar_mensagens(idoso_id, limite=limite * 2)
    eventos = [
        m for m in todas
        if m.get("tipo") in ["queda", "grito", "choro", "som_alto", "movimento", "emergencia", "sistema"]
        or m.get("autor") == "sistema"
    ]
    
    return {
        "idoso_id": idoso_id,
        "eventos": eventos[:limite],
        "total": len(eventos)
    }


@app.get("/eventos/{idoso_id}/resumo")
async def resumo_eventos(idoso_id: str, request: Request):
    """Resumo dos eventos por tipo."""
    token = auth.extrair_token(request)
    try:
        auth.autorizar("iniciar_conversa", token)
    except auth.AuthError as e:
        return JSONResponse({"error": str(e)}, status_code=401)
    
    from cloud.mcp_server.chat import get_store
    store = get_store()
    todas = store.listar_mensagens(idoso_id, limite=500)
    
    resumo = {
        "quedas": 0,
        "gritos": 0,
        "choros": 0,
        "sons_altos": 0,
        "movimentos": 0,
        "emergencias": 0,
        "total": 0
    }
    
    for m in todas:
        tipo = m.get("tipo", "")
        if tipo == "queda":
            resumo["quedas"] += 1
        elif tipo == "grito":
            resumo["gritos"] += 1
        elif tipo == "choro":
            resumo["choros"] += 1
        elif tipo == "som_alto":
            resumo["sons_altos"] += 1
        elif tipo == "movimento":
            resumo["movimentos"] += 1
        elif tipo == "emergencia":
            resumo["emergencias"] += 1
        if tipo in ["queda", "grito", "choro", "som_alto", "movimento", "emergencia"]:
            resumo["total"] += 1
    
    return {"idoso_id": idoso_id, "resumo": resumo}


# ============================================================
# MICROFONE DO CUIDADOR (push-to-talk)
# ============================================================

@app.post("/audio/cuidador/enviar")
async def audio_cuidador_enviar(request: Request):
    """Cuidador envia mensagem de voz para o idoso."""
    token = auth.extrair_token(request)
    try:
        auth.autorizar("iniciar_conversa", token)
    except auth.AuthError as e:
        return JSONResponse({"error": str(e)}, status_code=401)
    
    try:
        body = await request.json()
    except Exception:
        body = {}
    
    texto = body.get("texto", "").strip()
    idoso_id = body.get("idoso_id", "dona-maria")
    
    if not texto:
        return JSONResponse({"error": "Texto vazio"}, status_code=400)
    
    # Salvar no chat como mensagem do cuidador
    from cloud.mcp_server.chat import get_store
    store = get_store()
    store.adicionar_mensagem(
        idoso_id, "cuidador", texto,
        tipo="normal",
        metadata={"canal": "voz_cuidador"}
    )
    
    # Tentar falar no edge via WebSocket
    try:
        from cloud.mcp_server.websocket import gerenciador_ws
        await gerenciador_ws.broadcast({
            "tipo": "falar_no_idoso",
            "texto": texto,
            "idoso_id": idoso_id
        })
    except Exception as e:
        print(f"[Libero] Erro ao enviar para o edge: {e}")
    
    return {
        "status": "ok",
        "texto": texto,
        "idoso_id": idoso_id,
        "canal": "cuidador"
    }


# ============================================================
