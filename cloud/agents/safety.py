"""
Libero - Agente de Segurança
Detecção multimodal com confiança calibrada.

Compatível com API antiga (detectar_queda, detectar_fuga) e nova
(detectar_queda_multimodal).
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
        except Exception:
            _bedrock = False
    return _bedrock


# ============================================================
# QUEDA MULTIMODAL (NOVA API)
# ============================================================

def detectar_queda_multimodal(features_audio=None, features_visao=None, movimento=False):
    """
    Detecta queda combinando múltiplos sinais.
    
    Regra: áudio SOZINHO nunca confirma queda (confiança máx 0.3).
    """
    features_audio = features_audio or {}
    features_visao = features_visao or {}
    
    sinais = []
    score = 0.0
    
    # Sinal 1: Áudio (peso baixo sozinho)
    energia_max = features_audio.get("energia_max", 0)
    duracao = features_audio.get("duracao", 0)
    
    if energia_max > 0.7 and duracao < 2:
        sinais.append({"tipo": "audio_alto_curto", "peso": 0.3})
        score += 0.3
    elif energia_max > 0.5 and duracao < 2:
        sinais.append({"tipo": "audio_medio_curto", "peso": 0.15})
        score += 0.15
    
    # Sinal 2: Visão (ângulo)
    angulo = features_visao.get("angulo_corpo", 0)
    if angulo > 75:
        sinais.append({"tipo": "corpo_deitado", "peso": 0.4})
        score += 0.4
    elif angulo > 60:
        sinais.append({"tipo": "corpo_inclinado", "peso": 0.2})
        score += 0.2
    
    # Sinal 3: Velocidade de queda
    velocidade = features_visao.get("velocidade_queda", 0)
    if velocidade > 0.7:
        sinais.append({"tipo": "queda_rapida", "peso": 0.3})
        score += 0.3
    elif velocidade > 0.5:
        sinais.append({"tipo": "queda_media", "peso": 0.15})
        score += 0.15
    
    # Sinal 4: Imobilidade pós-queda
    if movimento and angulo > 60:
        sinais.append({"tipo": "imobilidade_pos_queda", "peso": 0.2})
        score += 0.2
    
    detectado = score >= 0.5
    
    if score >= 0.8:
        razao = "Queda confirmada"
    elif score >= 0.5:
        razao = "Possível queda"
    elif score > 0:
        razao = "Sinais fracos"
    else:
        razao = "Sem sinal"
    
    return {
        "detectado": detectado,
        "confianca": min(score, 1.0),
        "sinais": sinais,
        "razao": razao
    }


# ============================================================
# QUEDA (API ANTIGA - compatibilidade)
# ============================================================

def detectar_queda(features):
    """
    API antiga: recebe só features de áudio.
    
    DEPRECATED: use detectar_queda_multimodal.
    Retorna resultado com confiança limitada porque áudio sozinho
    NÃO confirma queda.
    """
    features = features or {}
    energia_max = features.get("energia_max", 0)
    duracao = features.get("duracao", 0)
    
    if energia_max > 0.5 and duracao < 2:
        # Áudio sozinho: confiança limitada a 0.3
        return {
            "detectado": True,
            "confianca": 0.3,
            "tipo": "queda_audio_suspeito",
            "razao": "Áudio suspeito - aguardando confirmação multimodal"
        }
    
    return {"detectado": False, "confianca": 0.0, "tipo": None}


# ============================================================
# FUGA (NOVA API)
# ============================================================

def detectar_fuga(texto, hora, movimento, contexto=None):
    """
    Detecta fuga APENAS com comportamento observado.
    
    Intenção verbal sozinha NÃO é fuga.
    """
    contexto = contexto or {}
    texto_lower = texto.lower() if texto else ""
    
    fatores_comportamento = []
    
    # 1. Movimento em direção à porta
    if contexto.get("direcao_porta") and movimento:
        fatores_comportamento.append({"tipo": "direcao_porta", "peso": 0.5})
    
    # 2. Porta abrindo
    if contexto.get("porta_aberta"):
        fatores_comportamento.append({"tipo": "porta_aberta", "peso": 0.7})
    
    # 3. Saiu de casa
    if contexto.get("saiu_casa"):
        fatores_comportamento.append({"tipo": "saiu_casa", "peso": 1.0})
    
    fatores_verbais = []
    
    frases_fuga = ["vou sair", "vou embora", "preciso sair", "vou trabalhar", "preciso ir trabalhar"]
    if any(f in texto_lower for f in frases_fuga):
        fatores_verbais.append({"tipo": "intencao_verbal", "peso": 0.2})
    
    if 2 <= hora <= 5 and movimento:
        fatores_verbais.append({"tipo": "madrugada_movimento", "peso": 0.3})
    
    # Score: comportamento pesa integral, verbal pesa 0.5
    score = sum(f["peso"] for f in fatores_comportamento)
    score += sum(f["peso"] * 0.5 for f in fatores_verbais)
    
    detectado = score >= 0.5
    
    return {
        "detectado": detectado,
        "confianca": min(score, 1.0),
        "tipo": "fuga" if detectado else None,
        "comportamento": fatores_comportamento,
        "verbal": fatores_verbais,
        "razao": f"Comportamento: {len(fatores_comportamento)}, Verbal: {len(fatores_verbais)}"
    }


# ============================================================
# FUGA NOTURNA (helper para compatibilidade)
# ============================================================

def detectar_fuga_noturna(movimento, hora):
    """Detecta fuga noturna: madrugada + movimento."""
    if 2 <= hora <= 5 and movimento:
        return {
            "detectado": True,
            "confianca": 0.75,
            "tipo": "fuga_noturna"
        }
    return {"detectado": False, "confianca": 0.0, "tipo": None}


# ============================================================
# AGITAÇÃO
# ============================================================

def detectar_agitacao(features, texto):
    """Detecta agitação (sundowning, confusão)."""
    features = features or {}
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
# RESPOSTA
# ============================================================

SYSTEM_PROMPT_SEGURANCA = """Você é o Libero, companheiro de idosos com Alzheimer.

Função AGORA: SEGURANÇA.

Princípios:
1. Fale com calma, firmeza e respeito.
2. NUNCA diga que ele está errado.
3. NUNCA assuste.
4. Preserve a autonomia.
5. Se for emergência, seja claro.
6. Se for só intenção, dialogue.
"""


def gerar_resposta_seguranca(evento, contexto):
    """Gera resposta de segurança."""
    bedrock = _get_bedrock()
    nome = contexto.get("nome", "")
    tipo = evento.get("tipo", "unknown")
    confianca = evento.get("confianca", 0)
    
    if not bedrock:
        if tipo in ["queda", "queda_audio_suspeito"]:
            if confianca >= 0.8:
                return f"{nome}, estou aqui. Não se mexa. Vou chamar ajuda."
            else:
                return f"{nome}, você está bem? Pode me responder?"
        elif tipo in ["fuga", "fuga_noturna"]:
            if confianca >= 0.8:
                return f"{nome}, espere. Vamos conversar antes. Senta aqui comigo."
            else:
                return f"{nome}, onde você vai? Me conta."
        elif tipo == "emergencia_texto":
            return f"{nome}, estou aqui. Não se preocupe. Vou chamar ajuda."
        elif tipo == "agitacao":
            return f"{nome}, está tudo bem. Me conta o que está sentindo."
        return f"{nome}, estou aqui. Está tudo bem."
    
    prompt = f"""Evento: {tipo}
Confiança: {confianca:.2f}
Contexto: {json.dumps(contexto, ensure_ascii=False)}

Gere uma resposta curta, calma e respeitosa."""
    
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
    """
    Toma ação com escalonamento proporcional.
    
    Regra: SAMU/polícia só com confiança >= 0.9.
    """
    acoes = []
    
    if not evento.get("detectado"):
        return {"acoes": [], "nivel": 0, "confianca": 0}
    
    tipo = evento.get("tipo", "unknown")
    confianca = evento.get("confianca", 0)
    
    # Voz SEMPRE
    resposta = gerar_resposta_seguranca(evento, contexto)
    acoes.append({"tipo": "voz", "conteudo": resposta, "confianca": confianca})
    
    # Nível 3 - Emergência (confiança >= 0.8)
    if confianca >= 0.8:
        acoes.append({"tipo": "notificar_familia", "urgencia": "alta"})
        
        if contexto.get("camera_autorizada", True):
            acoes.append({"tipo": "ativar_camera", "local": contexto.get("local")})
        
        # SAMU só com confiança >= 0.9
        if confianca >= 0.9:
            if tipo in ["queda", "emergencia_texto", "queda_audio_suspeito"]:
                acoes.append({"tipo": "chamar_emergencia", "servico": "samu"})
            elif tipo in ["fuga", "fuga_noturna"]:
                acoes.append({"tipo": "aguardar_retorno", "minutos": 15})
        else:
            acoes.append({"tipo": "monitorar_intensamente", "duracao_min": 5})
        
        return {"acoes": acoes, "nivel": 3, "confianca": confianca}
    
    # Nível 2 - Intervenção (0.5-0.8)
    if confianca >= 0.5:
        acoes.append({"tipo": "notificar_familia", "urgencia": "media"})
        return {"acoes": acoes, "nivel": 2, "confianca": confianca}
    
    return {"acoes": acoes, "nivel": 1, "confianca": confianca}


# ============================================================
# TESTE
# ============================================================

if __name__ == "__main__":
    contexto = {"nome": "Seu João", "hora": "03:00", "local": "sala"}
    
    print("=== Teste 1: Queda multimodal ===\n")
    
    r = detectar_queda_multimodal(
        features_audio={"energia_max": 0.8, "duracao": 1},
        features_visao={"angulo_corpo": 80, "velocidade_queda": 0.8},
        movimento=True
    )
    print(f"Multimodal: {r}")
    print(f"Ação: {agir(r, contexto)}\n")
    
    r = detectar_queda_multimodal(features_audio={"energia_max": 0.8, "duracao": 1})
    print(f"Só áudio: {r}")
    print(f"Ação: {agir(r, contexto)}\n")
    
    print("=== Teste 2: Fuga ===\n")
    
    r = detectar_fuga("Vou sair", 10, False)
    print(f"Só intenção: {r}")
    
    r = detectar_fuga("Vou sair", 10, True, {"porta_aberta": True})
    print(f"Intenção + porta: {r}")
