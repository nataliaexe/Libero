"""
Libero - MCP Server com login
"""

import os
import json
from contextlib import asynccontextmanager
from urllib.parse import urlparse
from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from cloud.mcp_server import tools
from cloud.mcp_server import auth

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


app = FastAPI(title="Libero MCP Server", version="1.4.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Libero-Token"],
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
        "version": "1.3.0",
        "spec": "2025-11-25",
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


@app.post("/mcp")
async def mcp_handler(request: Request):
    token = auth.extrair_token(request)
    
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({
            "jsonrpc": "2.0",
            "error": {"code": -32700, "message": "Parse error"},
            "id": None
        }, status_code=400)
    
    metodo = body.get("method")
    params = body.get("params", {})
    req_id = body.get("id")
    
    if metodo == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2025-11-25",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "libero", "version": "1.4.0"}
            }
        }
    
    if metodo == "tools/list":
        try:
            auth.autorizar("listar_ferramentas", token)
        except auth.AuthError as e:
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32001, "message": str(e)}}
        
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": tools.listar_ferramentas()}}
    
    if metodo == "tools/call":
        nome = params.get("name")
        argumentos = params.get("arguments", {})
        
        try:
            auth.autorizar(nome, token)
            auth.autorizar_argumentos(nome, token, argumentos)
        except auth.AuthError as e:
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32001, "message": str(e)}}
        
        resultado = tools.executar(nome, argumentos)
        
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [{"type": "text", "text": json.dumps(resultado, ensure_ascii=False)}]
            }
        }
    
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Método desconhecido: {metodo}"}}




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

    camera = get_camera()
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

    camera = get_camera()
    return {
        "rodando": camera.rodando,
        "camera_id": camera.camera_id,
        "fps": camera.fps
    }


@app.post("/camera/start")
async def camera_start(request: Request):
    """Inicia a câmera."""
    token = auth.extrair_token(request)
    try:
        auth.autorizar("controlar_camera", token)
    except auth.AuthError as e:
        return JSONResponse({"error": str(e)}, status_code=401)
    
    camera = get_camera()
    camera.iniciar()
    return {"status": "ok", "rodando": camera.rodando}


@app.post("/camera/stop")
async def camera_stop(request: Request):
    """Para a câmera."""
    token = auth.extrair_token(request)
    try:
        auth.autorizar("controlar_camera", token)
    except auth.AuthError as e:
        return JSONResponse({"error": str(e)}, status_code=401)
    
    camera = get_camera()
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
    """Lista apenas memórias."""
    token = auth.extrair_token(request)
    try:
        auth.autorizar_idoso("gravar_memoria", token, idoso_id)
    except auth.AuthError as e:
        return JSONResponse({"error": str(e)}, status_code=401)
    
    store = get_store()
    return {
        "idoso_id": idoso_id,
        "memorias": store.listar_memorias(idoso_id)
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
    resposta = companion.conversar(texto, {"nome": idoso_id})
    
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
    token = auth.extrair_token(websocket)
    origin = websocket.headers.get("origin", "").rstrip("/")
    idoso_id = websocket.query_params.get("idoso_id")
    try:
        if (auth.AMBIENTE == "production" and origin
                and origin not in ALLOWED_ORIGINS):
            raise auth.AuthError("Origem não autorizada")
        sessao = auth.autorizar("conectar_websocket", token)
        if (auth.AMBIENTE == "production"
                and websocket.cookies.get("libero_session")
                and not origin):
            raise auth.AuthError("Origem obrigatória")
        if sessao["idoso_id"] == "*":
            idoso_id = idoso_id or "*"
        else:
            auth.autorizar_idoso("conectar_websocket", token, idoso_id or sessao["idoso_id"])
            idoso_id = sessao["idoso_id"]
    except auth.AuthError:
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
async def audio_status(request: Request):
    """Status do microfone."""
    token = auth.extrair_token(request)
    try:
        auth.autorizar("controlar_audio", token)
    except auth.AuthError as e:
        return JSONResponse({"error": str(e)}, status_code=401)
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


if __name__ == "__main__":
    import uvicorn
    print(f"[Libero MCP] Iniciando em {MCP_HOST}:{MCP_PORT}")
    print(f"[Libero MCP] Ferramentas: {len(tools.FERRAMENTAS)}")
    print(f"[Libero MCP] Login: POST /auth/login")
    uvicorn.run(
        app, host=MCP_HOST, port=MCP_PORT,
        ws_max_size=65536, ws_max_queue=16, limit_concurrency=256,
    )
