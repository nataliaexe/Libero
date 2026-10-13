"""
Libero - Orquestrador
"""

import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from edge.decision.levels import decidir_nivel, Nivel, descrever_nivel
from cloud.agents import companion, safety, memory


class Orquestrador:
    def __init__(self, idoso_id, contexto=None):
        self.idoso_id = idoso_id
        self.contexto = contexto or {}
        self.historico = []
    
    def _agora(self):
        return datetime.now(timezone.utc).isoformat()
    
    def processar(self, texto, features=None, movimento=False):
        features = features or {}
        hora = datetime.now().hour
        
        self.contexto.update({
            "hora": f"{hora:02d}:00",
            "movimento": movimento
        })
        
        # 1. PRIORIDADE ABSOLUTA: Emergência por texto
        nivel_texto = decidir_nivel(texto, hora, movimento)
        
        if nivel_texto == Nivel.EMERGENCIA:
            evento = {"detectado": True, "confianca": 1.0, "tipo": "emergencia_texto"}
            resultado = safety.agir(evento, self.contexto)
            
            self.historico.append({
                "timestamp": self._agora(),
                "texto": texto,
                "evento": evento,
                "nivel": 3
            })
            
            return {
                "nivel": 3,
                "nivel_nome": "EMERGENCIA",
                "evento": evento,
                "acoes": resultado["acoes"],
                "resposta": resultado["acoes"][0]["conteudo"] if resultado["acoes"] else None
            }
        
        # 2. Verificar segurança (queda, fuga, agitação)
        eventos = []
        
        queda = safety.detectar_queda(features)
        if queda["detectado"]:
            eventos.append(queda)
        
        fuga = safety.detectar_fuga(texto, hora, movimento)
        if fuga["detectado"]:
            eventos.append(fuga)
        
        agitacao = safety.detectar_agitacao(features, texto)
        if agitacao["detectado"]:
            eventos.append(agitacao)
        
        if eventos:
            evento = max(eventos, key=lambda e: e["confianca"])
            resultado_seguranca = safety.agir(evento, self.contexto)
            
            self.historico.append({
                "timestamp": self._agora(),
                "texto": texto,
                "evento": evento,
                "nivel": resultado_seguranca["nivel"]
            })
            
            return {
                "nivel": resultado_seguranca["nivel"],
                "nivel_nome": f"NIVEL_{resultado_seguranca['nivel']}",
                "evento": evento,
                "acoes": resultado_seguranca["acoes"],
                "resposta": resultado_seguranca["acoes"][0]["conteudo"] if resultado_seguranca["acoes"] else None
            }
        
        # 3. Verificar memória (ANTES de decidir nível geral)
        historia = memory.detectar_historia(texto)
        memoria_gravada = None
        
        if historia["detectado"]:
            resultado_memoria = memory.gravar_memoria(
                self.idoso_id, texto, self.contexto
            )
            if resultado_memoria["gravado"]:
                memoria_gravada = resultado_memoria["memoria"]
                self.historico.append({
                    "timestamp": self._agora(),
                    "texto": texto,
                    "memoria": memoria_gravada
                })
        
        # 4. Decidir nível (agora a história já foi extraída)
        nivel = decidir_nivel(texto, hora, movimento)
        
        # 5. Agir
        resposta = None
        if nivel in [Nivel.CONVERSA, Nivel.INTERVENCAO]:
            resposta = companion.conversar(texto, self.contexto)
        
        self.historico.append({
            "timestamp": self._agora(),
            "texto": texto,
            "nivel": nivel.value,
            "nivel_nome": nivel.name
        })
        
        return {
            "nivel": nivel.value,
            "nivel_nome": nivel.name,
            "nivel_descricao": descrever_nivel(nivel),
            "resposta": resposta,
            "memoria": memoria_gravada,
            "acoes": [{"tipo": "voz", "conteudo": resposta}] if resposta else []
        }
    
    def resumo(self):
        return {
            "idoso_id": self.idoso_id,
            "total_interacoes": len(self.historico),
            "historico": self.historico[-10:]
        }


if __name__ == "__main__":
    orq = Orquestrador("dona-maria", {"nome": "Dona Maria", "local": "sala"})
    
    testes = [
        ("Bom dia, como você está?", {"energia_media": 0.02}, False),
        ("Preciso ir para casa.", {"energia_media": 0.1}, False),
        ("Socorro, caí!", {"energia_max": 0.8, "duracao": 1}, True),
        ("Quando eu era jovem, eu dançava com meu marido.", {"energia_media": 0.05}, False),
        ("Meu pai me ensinou a trabalhar. Ele era muito bom.", {"energia_media": 0.05}, False),
    ]
    
    for texto, features, movimento in testes:
        print(f"\n{'='*60}")
        print(f"[Entrada] '{texto}'")
        resultado = orq.processar(texto, features, movimento)
        print(f"[Nível] {resultado['nivel']} - {resultado.get('nivel_nome', '')}")
        if resultado.get("resposta"):
            print(f"[Resposta] {resultado['resposta']}")
        if resultado.get("memoria"):
            m = resultado["memoria"]
            print(f"[Memória GRAVADA] '{m['titulo']}' (confiança: {m['confianca']:.2f})")
        print(f"[Ações] {[a['tipo'] for a in resultado['acoes']]}")
    
    print(f"\n{'='*60}")
    print(f"[Resumo] {orq.resumo()['total_interacoes']} interações")
