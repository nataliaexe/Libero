"""
Libero - Orquestrador
Coordena agentes com timestamps consistentes em UTC.
"""

import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from edge.decision.levels import (
    decidir_nivel, Nivel, descrever_nivel,
    detectar_emergencia_contextual
)
from cloud.agents import companion, safety, memory
from cloud.mcp_server.chat import get_store


class Orquestrador:
    def __init__(self, idoso_id, contexto=None, timezone_offset=-3):
        """
        Args:
            idoso_id: ID do idoso
            contexto: dict com nome, local, etc.
            timezone_offset: offset do fuso em horas (default: -3 Brasil)
        """
        self.idoso_id = idoso_id
        self.contexto = contexto or {}
        self.historico = []
        self.timezone_offset = timezone_offset
    
    def _agora_utc(self):
        """Timestamp UTC padronizado."""
        return datetime.now(timezone.utc).isoformat()
    
    def _hora_local(self):
        """Hora local do idoso (baseada no offset)."""
        from datetime import timedelta
        utc = datetime.now(timezone.utc)
        local = utc + timedelta(hours=self.timezone_offset)
        return local.hour

    def _registrar_chat(self, texto, resposta, nivel, tipo="normal", metadata=None):
        """Persiste a interação para que o dashboard veja o resultado real."""
        try:
            store = get_store()
            if texto:
                store.adicionar_mensagem(
                    self.idoso_id, "idoso", texto, tipo=tipo, metadata=metadata
                )
            if resposta:
                store.adicionar_mensagem(
                    self.idoso_id, "libero", resposta, tipo=tipo,
                    metadata={"nivel": nivel, **(metadata or {})},
                )
        except Exception as e:
            print(f"[Libero] Erro ao salvar no chat: {e}")
    
    def processar(self, texto, features_audio=None, features_visao=None, movimento=False):
        """
        Processa entrada com análise contextual.
        
        Returns:
            dict com nível, ações, resposta
        """
        features_audio = features_audio or {}
        features_visao = features_visao or {}
        hora_local = self._hora_local()
        
        self.contexto.update({
            "hora_local": f"{hora_local:02d}:00",
            "movimento": movimento,
            "timestamp_utc": self._agora_utc()
        })
        
        # 1. EMERGÊNCIA por texto (com contexto)
        emergencia = detectar_emergencia_contextual(texto)
        
        if emergencia["nivel"] == Nivel.EMERGENCIA:
            evento = {
                "detectado": True,
                "confianca": 0.9 if emergencia["confianca"].value == "alta" else 0.7,
                "tipo": "emergencia_texto",
                "razao": emergencia["razao"]
            }
            resultado = safety.agir(evento, self.contexto)
            resposta = resultado["acoes"][0]["conteudo"] if resultado["acoes"] else None
            self._registrar_chat(
                texto, resposta, resultado["nivel"], "emergencia",
                {"evento": evento["tipo"], "acoes_externas_executadas": False},
            )
            
            self.historico.append({
                "timestamp_utc": self._agora_utc(),
                "texto": texto,
                "evento": evento,
                "nivel": resultado["nivel"],
                "confianca": emergencia["confianca"].value
            })
            
            return {
                "nivel": resultado["nivel"],
                "nivel_nome": "EMERGENCIA",
                "confianca": emergencia["confianca"].value,
                "evento": evento,
                "acoes": resultado["acoes"],
                "resposta": resposta,
                "acoes_externas_executadas": False,
            }
        
        # 2. Verificar segurança multimodal
        eventos = []
        
        queda = safety.detectar_queda_multimodal(features_audio, features_visao, movimento)
        if queda["detectado"]:
            eventos.append(queda)
        
        fuga = safety.detectar_fuga(texto, hora_local, movimento, self.contexto)
        if fuga["detectado"]:
            eventos.append(fuga)
        
        agitacao = safety.detectar_agitacao(features_audio, texto)
        if agitacao["detectado"]:
            eventos.append(agitacao)
        
        if eventos:
            evento = max(eventos, key=lambda e: e.get("confianca", 0))
            resultado_seguranca = safety.agir(evento, self.contexto)
            resposta = (
                resultado_seguranca["acoes"][0]["conteudo"]
                if resultado_seguranca["acoes"] else None
            )
            nivel_resultado = resultado_seguranca["nivel"]
            tipo_mensagem = "emergencia" if nivel_resultado == 3 else "normal"
            self._registrar_chat(
                texto, resposta, nivel_resultado, tipo_mensagem,
                {"evento": evento.get("tipo"), "acoes_externas_executadas": False},
            )
            
            self.historico.append({
                "timestamp_utc": self._agora_utc(),
                "texto": texto,
                "evento": evento,
                "nivel": resultado_seguranca["nivel"]
            })
            
            return {
                "nivel": resultado_seguranca["nivel"],
                "nivel_nome": f"NIVEL_{resultado_seguranca['nivel']}",
                "evento": evento,
                "acoes": resultado_seguranca["acoes"],
                "resposta": resposta,
                "acoes_externas_executadas": False,
            }
        
        # 3. Verificar memória
        historia = memory.detectar_historia(texto)
        memoria_gravada = None
        
        if historia["detectado"]:
            resultado_memoria = memory.gravar_memoria(
                self.idoso_id, texto, self.contexto
            )
            if resultado_memoria["gravado"]:
                memoria_gravada = resultado_memoria["memoria"]
                self.historico.append({
                    "timestamp_utc": self._agora_utc(),
                    "texto": texto,
                    "memoria": memoria_gravada
                })
        
        # 4. Decidir nível
        nivel = decidir_nivel(texto, hora_local, movimento)
        
        # 5. Agir
        resposta = None
        if nivel in [Nivel.CONVERSA, Nivel.INTERVENCAO]:
            resposta = companion.conversar(texto, self.contexto)
        
        self.historico.append({
            "timestamp_utc": self._agora_utc(),
            "texto": texto,
            "nivel": nivel.value,
            "nivel_nome": nivel.name
        })

        tipo_mensagem = "memoria" if memoria_gravada else "normal"
        self._registrar_chat(
            texto, resposta, nivel.value, tipo_mensagem,
            {"memoria_id": memoria_gravada.get("id")} if memoria_gravada else None,
        )
        
        return {
            "nivel": nivel.value,
            "nivel_nome": nivel.name,
            "nivel_descricao": descrever_nivel(nivel),
            "resposta": resposta,
            "memoria": memoria_gravada,
            "acoes": [{"tipo": "voz", "conteudo": resposta, "status": "preparada"}] if resposta else [],
            "acoes_externas_executadas": False,
        }
    
    def resumo(self):
        return {
            "idoso_id": self.idoso_id,
            "total_interacoes": len(self.historico),
            "historico": self.historico[-10:]
        }


def lambda_handler(event, context):
    """Handler para AWS Lambda."""
    import json
    
    body = event.get("body")
    if isinstance(body, str):
        body = json.loads(body)
    elif body is None:
        body = event
    
    idoso_id = body.get("idoso_id", "default")
    texto = body.get("texto", "")
    features_audio = body.get("features_audio", {})
    features_visao = body.get("features_visao", {})
    movimento = body.get("movimento", False)
    contexto = body.get("contexto", {})
    
    orq = Orquestrador(idoso_id, contexto)
    resultado = orq.processar(texto, features_audio, features_visao, movimento)
    
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(resultado, ensure_ascii=False, default=str)
    }


# ============================================================
# TESTE
# ============================================================

if __name__ == "__main__":
    orq = Orquestrador("dona-maria", {"nome": "Dona Maria", "local": "sala"})
    
    testes = [
        ("Bom dia, como você está?", {"energia_media": 0.02}, {}, False),
        ("Não estou sentindo dor", {"energia_media": 0.05}, {}, False),
        ("Preciso ir para casa.", {"energia_media": 0.1}, {}, False),
        ("Socorro, caí!", {"energia_max": 0.8, "duracao": 1}, {"angulo_corpo": 80, "velocidade_queda": 0.8}, True),
        ("Quando eu era jovem, eu dançava com meu marido.", {"energia_media": 0.05}, {}, False),
    ]
    
    for texto, fa, fv, mov in testes:
        print(f"\n{'='*60}")
        print(f"[Entrada] '{texto}'")
        resultado = orq.processar(texto, fa, fv, mov)
        print(f"[Nível] {resultado['nivel']} - {resultado.get('nivel_nome', '')}")
        if resultado.get("confianca"):
            print(f"[Confiança] {resultado['confianca']}")
        if resultado.get("resposta"):
            print(f"[Resposta] {resultado['resposta']}")
        if resultado.get("memoria"):
            m = resultado["memoria"]
            print(f"[Memória GRAVADA] '{m['titulo']}'")
        print(f"[Ações] {[a['tipo'] for a in resultado['acoes']]}")
    
    print(f"\n{'='*60}")
    print(f"[Resumo] {orq.resumo()['total_interacoes']} interações")
