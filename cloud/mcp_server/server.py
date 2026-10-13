"""
Libero - MCP Server
Expõe ferramentas para Alexa+ via Model Context Protocol.
Spec: 2025-11-25+ (Streamable HTTP)
"""

import os
import json
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from cloud.mcp_server import tools

load_dotenv()

app = FastAPI(title="Libero MCP Server", version="1.0.0")

MCP_PORT = int(os.getenv("MCP_PORT", "8080"))
MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")


# ============================================================
# ENDPOINTS MCP
# ============================================================

@app.get("/")
async def root():
    return {
        "name": "Libero MCP Server",
        "version": "1.0.0",
        "spec": "2025-11-25",
        "transport": "streamable-http",
        "ferramentas": len(tools.FERRAMENTAS)
    }


@app.get("/mcp/tools")
async def listar_tools():
    """Lista todas as ferramentas disponíveis."""
    return {"tools": tools.listar_ferramentas()}


@app.post("/mcp/tools/{tool_name}")
async def executar_tool(tool_name: str, request: Request):
    """Executa uma ferramenta MCP."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    
    print(f"[Libero MCP] Executando: {tool_name}")
    print(f"[Libero MCP] Params: {json.dumps(body, ensure_ascii=False)[:200]}")
    
    resultado = tools.executar(tool_name, body)
    
    return JSONResponse({
        "status": "success" if "erro" not in resultado else "error",
        "tool": tool_name,
        "result": resultado
    })


@app.post("/mcp")
async def mcp_handler(request: Request):
    """
    Endpoint MCP completo (JSON-RPC 2.0).
    Suporta: initialize, tools/list, tools/call
    """
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
    
    # initialize
    if metodo == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2025-11-25",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "libero",
                    "version": "1.0.0"
                }
            }
        }
    
    # tools/list
    if metodo == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": tools.listar_ferramentas()}
        }
    
    # tools/call
    if metodo == "tools/call":
        nome = params.get("name")
        argumentos = params.get("arguments", {})
        resultado = tools.executar(nome, argumentos)
        
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [
                    {"type": "text", "text": json.dumps(resultado, ensure_ascii=False)}
                ]
            }
        }
    
    # Método desconhecido
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Método desconhecido: {metodo}"}
    }


@app.get("/health")
async def health():
    return {"status": "ok", "ferramentas": len(tools.FERRAMENTAS)}


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    import uvicorn
    print(f"[Libero MCP] Iniciando em {MCP_HOST}:{MCP_PORT}")
    print(f"[Libero MCP] Ferramentas: {len(tools.FERRAMENTAS)}")
    uvicorn.run(app, host=MCP_HOST, port=MCP_PORT)
