"""
Libero - WebSocket
Sincroniza eventos entre notebook (servidor) e celular (cliente).
"""

import os
import json
import asyncio
from datetime import datetime, timezone
from fastapi import WebSocket, WebSocketDisconnect
from typing import List


class GerenciadorWebSocket:
    """Gerencia conexões WebSocket (celular, tablet, outro notebook)."""
    
    def __init__(self):
        self.conexoes: List[WebSocket] = []
        self.escopos = {}
        self.eventos_recentes = []
        self.max_eventos = 100
        self.max_conexoes = 64
        self.max_conexoes_por_idoso = 8
    
    async def conectar(self, websocket: WebSocket, cliente_id: str = None, idoso_id: str = "*"):
        """Registra nova conexão."""
        if len(self.conexoes) >= self.max_conexoes:
            return False
        if idoso_id != "*" and sum(
            1 for escopo in self.escopos.values() if escopo == idoso_id
        ) >= self.max_conexoes_por_idoso:
            return False
        await websocket.accept()
        self.conexoes.append(websocket)
        self.escopos[websocket] = idoso_id
        
        print(f"[Libero WS] Cliente conectado: {cliente_id or 'anônimo'} "
              f"(total: {len(self.conexoes)})")
        
        # Enviar eventos recentes
        eventos = [
            evento for escopo, evento in self.eventos_recentes
            if idoso_id == "*" or escopo in (idoso_id, "*")
        ]
        for evento in eventos[-20:]:
            try:
                await websocket.send_json(evento)
            except Exception:
                break
        return True
    
    def desconectar(self, websocket: WebSocket):
        """Remove conexão."""
        if websocket in self.conexoes:
            self.conexoes.remove(websocket)
        self.escopos.pop(websocket, None)
        print(f"[Libero WS] Cliente desconectado (total: {len(self.conexoes)})")
    
    async def broadcast(self, evento: dict, idoso_id: str = None):
        """Envia evento para todos os clientes conectados."""
        evento = dict(evento)
        # Adicionar timestamp se não tiver
        if "timestamp" not in evento:
            evento["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        # Guardar nos recentes
        self.eventos_recentes.append((idoso_id or "*", evento))
        if len(self.eventos_recentes) > self.max_eventos:
            self.eventos_recentes.pop(0)
        
        # Enviar para todos
        desconectados = []
        for ws in self.conexoes:
            escopo = self.escopos.get(ws)
            if idoso_id is not None and escopo not in (idoso_id, "*"):
                continue
            try:
                await ws.send_json(evento)
            except Exception:
                desconectados.append(ws)
        
        # Limpar desconectados
        for ws in desconectados:
            self.desconectar(ws)
        
        if self.conexoes:
            print(f"[Libero WS] Broadcast: {evento.get('tipo', 'evento')} "
                  f"para {len(self.conexoes)} clientes")
    
    async def enviar_para(self, websocket: WebSocket, evento: dict):
        """Envia evento para um cliente específico."""
        try:
            await websocket.send_json(evento)
        except Exception:
            self.desconectar(websocket)
    
    def status(self):
        """Retorna status."""
        return {
            "clientes_conectados": len(self.conexoes),
            "eventos_recentes": len(self.eventos_recentes)
        }


# Instância global
gerenciador_ws = GerenciadorWebSocket()
