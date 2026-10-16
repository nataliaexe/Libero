"""
Libero - Ferramentas MCP
Define todas as ferramentas expostas para a Alexa+.
"""

import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from cloud.agents import companion, safety, memory, care, family, health, governance
from cloud.knowledge import therapy, crisis, stages
from edge.decision.levels import Nivel, detectar_emergencia_contextual


# ============================================================
# REGISTRO DE FERRAMENTAS
# ============================================================

FERRAMENTAS = {}


def registrar(nome, descricao, schema):
    """Decorator para registrar uma ferramenta."""
    def wrapper(fn):
        FERRAMENTAS[nome] = {
            "name": nome,
            "description": descricao,
            "inputSchema": schema,
            "handler": fn
        }
        return fn
    return wrapper


# ============================================================
# COMPANHIA
# ============================================================

@registrar(
    "iniciar_conversa",
    "Inicia uma conversa com o idoso usando terapia de validação.",
    {
        "type": "object",
        "properties": {
            "idoso_id": {"type": "string"},
            "mensagem": {"type": "string"},
            "contexto": {"type": "object"}
        },
        "required": ["idoso_id", "mensagem"]
    }
)
def iniciar_conversa(idoso_id, mensagem, contexto=None):
    contexto = contexto or {}
    resposta = companion.conversar(mensagem, contexto)
    governance.Governanca().auditar(
        "companion", "iniciar_conversa",
        {"idoso_id": idoso_id, "mensagem": mensagem},
        {"resposta": resposta}
    )
    return {"resposta": resposta}


# ============================================================
# SEGURANÇA
# ============================================================

@registrar(
    "verificar_seguranca",
    "Verifica se há evento de segurança e toma ação.",
    {
        "type": "object",
        "properties": {
            "idoso_id": {"type": "string"},
            "texto": {"type": "string"},
            "features": {"type": "object"},
            "features_audio": {"type": "object"},
            "features_visao": {"type": "object"},
            "movimento": {"type": "boolean"}
        },
        "required": ["idoso_id"]
    }
)
def verificar_seguranca(
    idoso_id, texto="", features=None, features_audio=None,
    features_visao=None, movimento=False,
):
    features_audio = features_audio if isinstance(features_audio, dict) else features
    features_audio = features_audio if isinstance(features_audio, dict) else {}
    features_visao = features_visao if isinstance(features_visao, dict) else {}
    eventos = []

    emergencia = detectar_emergencia_contextual(texto)
    if emergencia["nivel"] == Nivel.EMERGENCIA:
        eventos.append({
            "detectado": True,
            "confianca": 0.9 if emergencia["confianca"].value == "alta" else 0.7,
            "score_nao_calibrado": True,
            "tipo": "emergencia_texto",
            "razao": emergencia["razao"],
        })

    queda = safety.detectar_queda_multimodal(
        features_audio, features_visao, movimento
    )
    if queda["detectado"]:
        eventos.append(queda)

    fuga = safety.detectar_fuga(texto, datetime.now().hour, movimento)
    if fuga["detectado"]:
        eventos.append(fuga)

    agitacao = safety.detectar_agitacao(features_audio, texto)
    if agitacao["detectado"]:
        eventos.append(agitacao)
    
    if not eventos:
        return {"evento": None, "nivel": 0, "acoes_externas_executadas": False}
    
    evento = max(eventos, key=lambda e: e.get("confianca", 0))
    resultado = safety.agir(evento, {"idoso_id": idoso_id})
    
    governance.Governanca().auditar(
        "safety", "verificar_seguranca",
        {"idoso_id": idoso_id, "evento": evento},
        resultado,
        razao=(
            f"Evento {evento['tipo']} com escore heurístico "
            f"{evento['confianca']} (não calibrado)"
        )
    )
    
    return {
        "evento": evento,
        "nivel": resultado["nivel"],
        "acoes": resultado["acoes"],
        "acoes_externas_executadas": False,
    }


# ============================================================
# MEMÓRIA
# ============================================================

@registrar(
    "gravar_memoria",
    "Grava uma história contada pelo idoso.",
    {
        "type": "object",
        "properties": {
            "idoso_id": {"type": "string"},
            "texto": {"type": "string"},
            "contexto": {"type": "object"}
        },
        "required": ["idoso_id", "texto"]
    }
)
def gravar_memoria(idoso_id, texto, contexto=None):
    contexto = contexto or {}
    resultado = memory.gravar_memoria(idoso_id, texto, contexto)
    
    governance.Governanca().auditar(
        "memory", "gravar_memoria",
        {"idoso_id": idoso_id, "texto": texto[:100]},
        resultado
    )
    
    return resultado


# ============================================================
# CUIDADO
# ============================================================

@registrar(
    "verificar_lembretes",
    "Verifica lembretes de remédio, água, comida.",
    {
        "type": "object",
        "properties": {
            "hora": {"type": "string"},
            "rotina": {"type": "object"}
        }
    }
)
def verificar_lembretes(hora=None, rotina=None):
    lembretes = care.verificar_lembretes(hora, rotina)
    return {"lembretes": lembretes, "total": len(lembretes)}


@registrar(
    "gerar_mensagem_cuidado",
    "Gera uma mensagem de cuidado para o idoso.",
    {
        "type": "object",
        "properties": {
            "idoso_id": {"type": "string"},
            "lembrete": {"type": "object"},
            "contexto": {"type": "object"}
        },
        "required": ["idoso_id", "lembrete"]
    }
)
def gerar_mensagem_cuidado(idoso_id, lembrete, contexto=None):
    contexto = contexto or {}
    mensagem = care.gerar_mensagem_cuidado(lembrete, contexto)
    return {"mensagem": mensagem}


# ============================================================
# FAMÍLIA
# ============================================================

@registrar(
    "notificar_familia",
    "Notifica a família sobre um evento.",
    {
        "type": "object",
        "properties": {
            "idoso_id": {"type": "string"},
            "evento": {"type": "object"},
            "contexto": {"type": "object"}
        },
        "required": ["idoso_id", "evento"]
    }
)
def notificar_familia(idoso_id, evento, contexto=None):
    contexto = contexto or {"idoso_id": idoso_id}
    resultado = family.notificar(evento, contexto)
    
    governance.Governanca().auditar(
        "family", "notificar_familia",
        {"idoso_id": idoso_id, "evento": evento},
        resultado,
        razao=f"Urgência: {evento.get('urgencia', 'media')}"
    )
    
    return resultado


@registrar(
    "relatorio_diario",
    "Gera um relatório diário para a família.",
    {
        "type": "object",
        "properties": {
            "idoso_id": {"type": "string"},
            "historico": {"type": "array"},
            "contexto": {"type": "object"}
        },
        "required": ["idoso_id", "historico"]
    }
)
def relatorio_diario(idoso_id, historico, contexto=None):
    contexto = contexto or {"idoso_id": idoso_id}
    relatorio = family.gerar_relatorio_diario(historico, contexto)
    return relatorio


# ============================================================
# SAÚDE
# ============================================================

@registrar(
    "analisar_saude",
    "Analisa sintomas e detecta possíveis problemas de saúde.",
    {
        "type": "object",
        "properties": {
            "idoso_id": {"type": "string"},
            "sintomas": {"type": "object"},
            "contexto": {"type": "object"}
        },
        "required": ["idoso_id", "sintomas"]
    }
)
def analisar_saude(idoso_id, sintomas, contexto=None):
    contexto = contexto or {}
    resultado = health.analisar(idoso_id, sintomas, contexto)
    
    governance.Governanca().auditar(
        "health", "analisar_saude",
        {"idoso_id": idoso_id, "sintomas": sintomas},
        resultado
    )
    
    return resultado


# ============================================================
# CONHECIMENTO
# ============================================================

@registrar(
    "obter_protocolo_crise",
    "Obtém o protocolo para uma crise específica.",
    {
        "type": "object",
        "properties": {
            "crise": {"type": "string"}
        },
        "required": ["crise"]
    }
)
def obter_protocolo_crise(crise):
    try:
        tipo = crisis.Crise(crise)
        protocolo = crisis.obter_protocolo(tipo)
        return {"protocolo": protocolo}
    except ValueError:
        return {"erro": f"Crise desconhecida: {crise}"}


@registrar(
    "sugerir_terapia",
    "Sugere uma terapia baseada no sintoma.",
    {
        "type": "object",
        "properties": {
            "sintoma": {"type": "string"},
            "estagio": {"type": "string"}
        },
        "required": ["sintoma"]
    }
)
def sugerir_terapia(sintoma, estagio=None):
    terapia = therapy.sugerir_terapia(sintoma, estagio)
    protocolo = therapy.obter_protocolo(terapia)
    return {
        "terapia": terapia.value,
        "protocolo": protocolo
    }


@registrar(
    "obter_estagio",
    "Obtém informações sobre um estágio da demência.",
    {
        "type": "object",
        "properties": {
            "estagio": {"type": "string"}
        },
        "required": ["estagio"]
    }
)
def obter_estagio(estagio):
    try:
        tipo = stages.Estagio[estagio.upper()]
        sintomas = stages.obter_sintomas(tipo)
        return {"estagio": tipo.name, "sintomas": sintomas}
    except KeyError:
        return {"erro": f"Estágio desconhecido: {estagio}"}


# ============================================================
# GOVERNANÇA
# ============================================================

@registrar(
    "verificar_vies",
    "Verifica viés nas decisões do Libero.",
    {
        "type": "object",
        "properties": {}
    }
)
def verificar_vies():
    gov = governance.Governanca()
    return {"vieses": gov.verificar_vies()}


@registrar(
    "verificar_compliance",
    "Verifica compliance com LGPD, GDPR, HIPAA.",
    {
        "type": "object",
        "properties": {}
    }
)
def verificar_compliance():
    gov = governance.Governanca()
    return gov.verificar_compliance()


# ============================================================
# UTILITÁRIOS
# ============================================================

def listar_ferramentas():
    """Lista todas as ferramentas registradas."""
    return [
        {
            "name": f["name"],
            "description": f["description"],
            "inputSchema": f["inputSchema"]
        }
        for f in FERRAMENTAS.values()
    ]


def executar(nome, params):
    """Executa uma ferramenta pelo nome."""
    if nome not in FERRAMENTAS:
        return {"erro": f"Ferramenta desconhecida: {nome}"}
    
    handler = FERRAMENTAS[nome]["handler"]
    try:
        return handler(**params)
    except Exception as e:
        return {"erro": str(e)}


if __name__ == "__main__":
    print(f"=== Ferramentas MCP Registradas ({len(FERRAMENTAS)}) ===\n")
    for nome, f in FERRAMENTAS.items():
        print(f"[{nome}]")
        print(f"  {f['description']}")
        print()
