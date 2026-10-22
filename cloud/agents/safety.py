"""
Libero - Agente de Segurança
Detecção multimodal por escores heurísticos não calibrados.

Compatível com API antiga (detectar_queda, detectar_fuga) e nova
(detectar_queda_multimodal).
"""

import os
import json
import re
import boto3
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

REGION = os.getenv("AWS_REGION", "us-east-1")
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "").strip()

_bedrock = None


def _get_bedrock():
    global _bedrock
    if not MODEL_ID:
        return None
    if _bedrock is None:
        try:
            _bedrock = boto3.client("bedrock-runtime", region_name=REGION)
        except Exception:
            _bedrock = None
    return _bedrock


# ============================================================
# QUEDA MULTIMODAL (NOVA API)
# ============================================================

def detectar_queda_multimodal(features_audio=None, features_visao=None, movimento=False):
    """
    Detecta queda combinando múltiplos sinais.
    
    Áudio sozinho nunca marca uma queda como detectada. O escore é uma
    heurística para priorizar verificação, não uma probabilidade calibrada.
    """
    features_audio = features_audio if isinstance(features_audio, dict) else {}
    features_visao = features_visao if isinstance(features_visao, dict) else {}
    
    sinais = []
    score = 0.0
    
    # Sinal 1: Áudio (peso baixo sozinho)
    energia_max = features_audio.get(
        "energia_rms", features_audio.get("energia_max", 0)
    )
    duracao = features_audio.get("duracao", 0)
    
    if energia_max > 0.7 and duracao < 2:
        sinais.append({"tipo": "audio_alto_curto", "peso": 0.3})
        score += 0.3
    elif energia_max > 0.5 and duracao < 2:
        sinais.append({"tipo": "audio_medio_curto", "peso": 0.15})
        score += 0.15
    
    # A detecção local é tratada como um indício único, sem contar de novo
    # o mesmo ângulo usado pelo detector da câmera.
    local_detectou = features_visao.get("queda_detectada_edge") is True
    angulo = features_visao.get("angulo_corpo", 0)
    if local_detectou:
        confianca_edge = features_visao.get("confianca_queda_edge")
        peso_edge = 0.5 if confianca_edge is None else min(max(float(confianca_edge), 0.0), 1.0)
        sinais.append({"tipo": "queda_sinalizada_no_edge", "peso": peso_edge})
        score += peso_edge
    else:
        if angulo > 75:
            sinais.append({"tipo": "corpo_deitado", "peso": 0.4})
            score += 0.4
        elif angulo > 60:
            sinais.append({"tipo": "corpo_inclinado", "peso": 0.2})
            score += 0.2

        velocidade = features_visao.get("velocidade_queda", 0)
        if velocidade > 0.7:
            sinais.append({"tipo": "queda_rapida", "peso": 0.3})
            score += 0.3
        elif velocidade > 0.5:
            sinais.append({"tipo": "queda_media", "peso": 0.15})
            score += 0.15

        if features_visao.get("imobilidade_pos_queda") is True and angulo > 60:
            sinais.append({"tipo": "imobilidade_pos_queda", "peso": 0.2})
            score += 0.2
    
    detectado = score >= 0.5
    
    if score >= 0.8:
        razao = "Múltiplos sinais compatíveis; requer verificação"
    elif score >= 0.5:
        razao = "Sinais compatíveis; requer verificação"
    elif score > 0:
        razao = "Sinais fracos"
    else:
        razao = "Sem sinal"
    
    return {
        "tipo": "queda" if detectado else None,
        "detectado": detectado,
        "confianca": min(score, 1.0),
        "score_nao_calibrado": True,
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

SYSTEM_PROMPT_SEGURANCA = """You are Libero, a companion for elderly people with Alzheimer's.
Speak calmly, firmly, and respectfully.
Principles:
1. Speak calmly, firmly, and respectfully.
2. NEVER tell them they are wrong.
3. NEVER scare them.
4. Preserve a autonomia.
5. If it is an emergency, be clear.
6. If it is just an intention, dialogue.
7. Never claim that you contacted anyone, opened a camera, or dispatched a service unless it happened.
8. Ask simple questions and encourage a caregiver to check the situation.
"""

SYSTEM_PROMPT_SEGURANCA_PT = """Você é Libero, um companheiro gentil para pessoas idosas.
Fale com calma, clareza e respeito. Não diga que a pessoa está errada nem a assuste.
Não afirme que chamou alguém, abriu uma câmera ou acionou um serviço se isso não
aconteceu. Faça perguntas simples e peça que um cuidador verifique a situação."""


def _resposta_local(tipo, nome, confianca, language="en"):
    """Language-matched fallback when Bedrock is unavailable."""
    nome = nome or "Maria"
    if str(language).lower().startswith("pt"):
        if tipo in ["queda", "queda_audio_suspeito", "emergencia_texto"]:
            return (
                f"{nome}, você consegue me responder? Fique onde está; estou aqui com você."
                if confianca >= 0.8 else f"{nome}, você está bem? Consegue me responder?"
            )
        if tipo in ["fuga", "fuga_noturna"]:
            return f"{nome}, vamos conversar um pouco antes de sair. O que você precisa agora?"
        if tipo == "agitacao":
            return f"{nome}, estou aqui com você. Pode me contar o que está sentindo?"
        return f"{nome}, estou aqui com você. Como posso ajudar agora?"
    if tipo in ["queda", "queda_audio_suspeito", "emergencia_texto"]:
        if confianca >= 0.8:
            return f"{nome}, I am here with you. Please stay still and answer me."
        else:
            return f"{nome}, are you okay? Can you answer me?"
    elif tipo in ["fuga", "fuga_noturna"]:
        if confianca >= 0.8:
            return f"{nome}, please wait. Let's talk first. Sit here with me."
        else:
            return f"{nome}, where are you going? Tell me."
    elif tipo == "agitacao":
        return f"{nome}, it's okay. Tell me what you are feeling."
    return f"{nome}, I am here with you. Everything is okay."
def _limpar_resposta(texto):
    """Remove markdown e limita a 2 frases."""
    import re
    if not texto:
        return None
    texto = re.sub(r'[#*_`~]', '', texto)
    texto = re.sub(r'^\s*[-•]\s*', '', texto, flags=re.MULTILINE)
    texto = re.sub(r'\s+', ' ', texto).strip()
    frases = re.split(r'(?<=[.!?])\s+', texto)
    frases = [f.strip() for f in frases if f.strip()]
    if not frases:
        return None
    resultado = ' '.join(frases[:2]).strip()
    return resultado if len(resultado) >= 10 else None


def gerar_resposta_seguranca(evento, contexto):
    """Gera resposta de segurança."""
    bedrock = _get_bedrock()
    nome = contexto.get("nome", "")
    tipo = evento.get("tipo", "unknown")
    confianca = evento.get("confianca", 0)
    language = contexto.get("language", "en")
    system_prompt = (
        SYSTEM_PROMPT_SEGURANCA_PT
        if str(language).lower().startswith("pt")
        else SYSTEM_PROMPT_SEGURANCA
    )
    
    if not bedrock:
        return _resposta_local(tipo, nome, confianca, language)
    
    prompt = f"""Evento: {tipo}
Confiança: {confianca:.2f}
Contexto: {json.dumps(contexto, ensure_ascii=False)}

Gere uma resposta curta, calma e respeitosa."""
    
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 150,
        "system": system_prompt,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = bedrock.invoke_model(modelId=MODEL_ID, body=json.dumps(body))
        resultado = json.loads(response["body"].read())
        texto = resultado["content"][0]["text"].strip()
        
        # 1. Limpar markdown e limitar a 2 frases
        texto_limpo = _limpar_resposta(texto)
        
        # Se a limpeza falhou, usar resposta local
        if not texto_limpo:
            return _resposta_local(tipo, nome, confianca, language)
        
        # 2. Bloquear alegações de ação (não deve dizer que está fazendo)
        alegacao_de_acao = re.search(
            r"\b(?:vou|estou|já|acionei|chamei|avisei|notifiquei)\b"
            r".{0,50}\b(?:ajuda|samu|família|cuidador|emergência|câmera)\b",
            texto_limpo,
            re.IGNORECASE | re.DOTALL,
        )
        
        return _resposta_local(tipo, nome, confianca, language) if alegacao_de_acao else texto_limpo
    except Exception as e:
        print(f"[Libero Segurança] Erro Bedrock: {e}")
        return _resposta_local(tipo, nome, confianca, language)


# ============================================================
# AÇÃO
# ============================================================

def agir(evento, contexto):
    """
    IMPORTANTE: Esta função APENAS PROPÕE ações.
    Nenhuma ação externa (SAMU, polícia, câmera) é executada automaticamente.
    Todas as ações são registradas com status "proposta_nao_executada"
    e precisam de confirmação humana via UI.
    """
    """
    Monta um plano de ação proporcional; não executa serviços externos.

    Os limiares usam escore heurístico e não representam probabilidades.
    """
    acoes = []
    
    if not evento.get("detectado"):
        return {"acoes": [], "nivel": 0, "confianca": 0}
    
    tipo = evento.get("tipo", "unknown")
    confianca = evento.get("confianca", 0)
    
    # Voz SEMPRE
    resposta = gerar_resposta_seguranca(evento, contexto)
    acoes.append({
        "tipo": "voz", "conteudo": resposta, "confianca": confianca,
        "status": "preparada",
    })
    
    # Nível 3 - Emergência (confiança >= 0.8)
    if confianca >= 0.8:
        acoes.append({
            "tipo": "notificar_familia", "urgencia": "alta",
            "status": "proposta_nao_executada",
        })
        
        if contexto.get("camera_autorizada", False):
            acoes.append({
                "tipo": "ativar_camera", "local": contexto.get("local"),
                "status": "proposta_nao_executada",
            })
        
        # SAMU só com confiança >= 0.9
        if confianca >= 0.9:
            if tipo in ["queda", "emergencia_texto", "queda_audio_suspeito"]:
                acoes.append({
                    "tipo": "chamar_emergencia", "servico": "samu",
                    "status": "proposta_nao_executada",
                })
            elif tipo in ["fuga", "fuga_noturna"]:
                acoes.append({
                    "tipo": "aguardar_retorno", "minutos": 15,
                    "status": "proposta_nao_executada",
                })
        else:
            acoes.append({
                "tipo": "monitorar_intensamente", "duracao_min": 5,
                "status": "proposta_nao_executada",
            })
        
        return {"acoes": acoes, "nivel": 3, "confianca": confianca}
    
    # A single, uncalibrated edge flag scores 0.5. It can prompt a voice
    # check-in, but family notification needs corroborating evidence.
    # Nível 2 - Intervenção (0.6-0.8)
    if confianca >= 0.6:
        acoes.append({
            "tipo": "notificar_familia", "urgencia": "media",
            "status": "proposta_nao_executada",
        })
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



# ============================================================
# BROADCAST DE EMERGÊNCIA (notificação em tempo real)
# ============================================================

async def broadcast_emergencia(evento, contexto):
    """Envia notificação de emergência via WebSocket."""
    try:
        from cloud.mcp_server.websocket import gerenciador_ws
        await gerenciador_ws.broadcast({
            "tipo": "emergencia",
            "idoso_id": contexto.get("idoso_id", "dona-maria"),
            "evento": evento.get("tipo"),
            "confianca": evento.get("confianca"),
            "local": contexto.get("local", "casa"),
            "timestamp": contexto.get("timestamp_utc"),
            "texto": f"Emergência detectada: {evento.get('tipo')}"
        })
        print(f"[Libero] Notificação de emergência enviada")
    except Exception as e:
        print(f"[Libero] Erro ao enviar notificação: {e}")
