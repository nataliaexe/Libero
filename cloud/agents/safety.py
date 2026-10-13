"""
Libero - Agente de Segurança
Detecta perigo (fuga, queda, agitação) e intervém.
"""

import os
import json
import boto3
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

REGION = os.getenv("AWS_REGION", "us-east-1")
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")

_bedrock = None

def _get_bedrock():
    global _bedrock
    if _bedrock is None:
        try:
            _bedrock = boto3.client("bedrock-runtime", region_name=REGION)
        except Exception as e:
            print(f"[Libero] Bedrock não disponível: {e}")
            _bedrock = False
    return _bedrock


# ============================================================
# DETECÇÃO DE EVENTOS
# ============================================================

def detectar_queda(features):
    """Detecta queda baseado em features de áudio."""
    energia_max = features.get("energia_max", 0)
    duracao = features.get("duracao", 0)
    
    if energia_max > 0.5 and duracao < 2:
        return {"detectado": True, "confianca": 0.9, "tipo": "queda"}
    
    return {"detectado": False, "confianca": 0.0, "tipo": None}


def detectar_fuga(texto, hora, movimento):
    """Detecta tentativa de fuga."""
    texto_lower = texto.lower() if texto else ""
    
    frases_fuga = [
        "vou sair", "vou trabalhar", "vou embora",
        "vou para casa", "preciso sair", "preciso ir trabalhar",
        "vou para o trabalho", "vou para rua"
    ]
    
    palavras_fuga = ["sair", "embora", "rua"]
    
    if any(frase in texto_lower for frase in frases_fuga):
        return {"detectado": True, "confianca": 0.85, "tipo": "fuga"}
    
    if movimento and any(p in texto_lower for p in palavras_fuga):
        return {"detectado": True, "confianca": 0.7, "tipo": "fuga"}
    
    if 2 <= hora <= 5 and movimento and not texto_lower:
        return {"detectado": True, "confianca": 0.75, "tipo": "fuga_noturna"}
    
    return {"detectado": False, "confianca": 0.0, "tipo": None}


def detectar_agitacao(features, texto):
    """Detecta agitação (sundowning, confusão)."""
    energia = features.get("energia_media", 0)
    zcr = features.get("zcr", 0)
    texto_lower = texto.lower() if texto else ""
    
    palavras_confusao = ["casa", "onde", "quem", "cadê", "preciso ir"]
    
    score = 0
    if energia > 0.1:
        score += 0.3
    if zcr > 0.15:
        score += 0.3
    if any(p in texto_lower for p in palavras_confusao):
        score += 0.4
    
    if score >= 0.6:
        return {"detectado": True, "confianca": score, "tipo": "agitacao"}
    
    return {"detectado": False, "confianca": score, "tipo": None}


# ============================================================
# INTERVENÇÃO
# ============================================================

SYSTEM_PROMPT_SEGURANCA = """Você é o Libero, um companheiro para idosos com Alzheimer ou demência.

Sua função AGORA é SEGURANÇA. O idoso está em risco.

Princípios:
1. Fale com calma, mas com firmeza.
2. Use o nome dele.
3. Diga que está tudo bem.
4. Peça para ele sentar e esperar.
5. Diga que a família está vindo.
6. NUNCA diga que ele está errado.
7. NUNCA assuste.
"""


def gerar_resposta_seguranca(evento, contexto):
    """Gera uma resposta de segurança."""
    bedrock = _get_bedrock()
    nome = contexto.get("nome", "")
    
    if not bedrock:
        if evento["tipo"] == "queda":
            return f"{nome}, estou aqui. Não se mexa. Vou chamar ajuda."
        elif evento["tipo"] in ["fuga", "fuga_noturna"]:
            return f"{nome}, espere. Está tudo bem. Senta aqui comigo."
        elif evento["tipo"] == "emergencia_texto":
            return f"{nome}, estou aqui. Não se preocupe. Vou chamar ajuda."
        else:
            return f"{nome}, estou aqui com você. Está tudo bem."
    
    prompt = f"""Evento: {evento['tipo']}
Confiança: {evento['confianca']}
Contexto: {json.dumps(contexto, ensure_ascii=False)}

Gere uma resposta curta, calma e firme."""
    
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 150,
        "system": SYSTEM_PROMPT_SEGURANCA,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = bedrock.invoke_model(modelId=MODEL_ID, body=json.dumps(body))
        resultado = json.loads(response["body"].read())
        return resultado["content"][0]["text"].strip()
    except Exception as e:
        print(f"[Libero Segurança] Erro Bedrock: {e}")
        return f"{nome}, estou aqui. Está tudo bem."


# ============================================================
# AÇÃO
# ============================================================

def agir(evento, contexto):
    """Toma ação baseada no evento detectado."""
    acoes = []
    
    if not evento["detectado"]:
        return {"acoes": [], "nivel": 0}
    
    tipo = evento["tipo"]
    confianca = evento["confianca"]
    
    # EMERGÊNCIA: queda, fuga confirmada, emergência por texto, ou confiança alta
    if tipo in ["queda", "emergencia_texto"] or confianca >= 0.8:
        resposta = gerar_resposta_seguranca(evento, contexto)
        acoes.append({"tipo": "voz", "conteudo": resposta})
        acoes.append({"tipo": "ativar_camera"})
        acoes.append({"tipo": "notificar_familia", "urgencia": "alta"})
        
        # Chamar emergência baseado no tipo
        if tipo == "queda":
            acoes.append({"tipo": "chamar_emergencia", "servico": "samu"})
        elif tipo in ["fuga", "fuga_noturna"]:
            acoes.append({"tipo": "chamar_emergencia", "servico": "policia"})
        elif tipo == "emergencia_texto":
            acoes.append({"tipo": "chamar_emergencia", "servico": "samu"})
        
        return {"acoes": acoes, "nivel": 3}
    
    # INTERVENÇÃO: agitação, fuga incerta
    resposta = gerar_resposta_seguranca(evento, contexto)
    acoes.append({"tipo": "voz", "conteudo": resposta})
    acoes.append({"tipo": "notificar_familia", "urgencia": "media"})
    return {"acoes": acoes, "nivel": 2}
