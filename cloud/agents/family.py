"""
Libero - Agente de Família
Notifica, coordena, tranquiliza.
Nunca culpa o cuidador.
"""

import os
import json
import boto3
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

REGION = os.getenv("AWS_REGION", "us-east-1")
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")
TOPIC_ARN = os.getenv("SNS_TOPIC_ARN", "")

_bedrock = None
_sns = None

def _get_bedrock():
    global _bedrock
    if _bedrock is None:
        try:
            _bedrock = boto3.client("bedrock-runtime", region_name=REGION)
        except Exception:
            _bedrock = False
    return _bedrock

def _get_sns():
    global _sns
    if _sns is None:
        try:
            _sns = boto3.client("sns", region_name=REGION)
        except Exception:
            _sns = False
    return _sns


# ============================================================
# GERAÇÃO DE MENSAGEM
# ============================================================

SYSTEM_PROMPT_FAMILIA = """Você é o Libero, um companheiro para idosos com Alzheimer ou demência.

Sua função AGORA é FAMÍLIA. Você está se comunicando com o cuidador.

Princípios:
1. Nunca culpe o cuidador.
2. Reconheça o esforço dele.
3. Seja específico mas gentil.
4. Se for emergência, seja direto.
5. Se for rotina, seja tranquilizador.
6. Sempre diga que a IA está cuidando.

Exemplos:
- Emergência: "Ana, seu pai caiu. Câmera ativada. Ele está consciente. SAMU chamado. Você quer falar com ele?"
- Rotina: "Ana, sua mãe teve um bom dia. Dormiu 7h. Tomou remédio. Teve 1 episódio de agitação às 15h. Passou. Você pode dormir tranquila."
- Memória: "Ana, sua mãe contou uma história linda sobre o seu pai hoje. Quer ouvir?"
"""


def gerar_mensagem_familia(evento, contexto):
    """Gera uma mensagem para a família."""
    bedrock = _get_bedrock()
    
    if not bedrock:
        # Fallback offline
        tipo = evento.get("tipo", "rotina")
        urgencia = evento.get("urgencia", "media")
        detalhes = evento.get("detalhes", "")
        
        if urgencia == "alta":
            return f"Emergência: {detalhes}. Estou cuidando. Você quer falar?"
        elif tipo == "memoria":
            return f"Sua mãe contou uma história hoje. Quer ouvir?"
        else:
            return f"Tudo bem por aqui. {detalhes}"
    
    prompt = f"""Evento: {json.dumps(evento, ensure_ascii=False)}
Contexto: {json.dumps(contexto, ensure_ascii=False)}

Gere uma mensagem curta e empática para o cuidador."""
    
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 200,
        "system": SYSTEM_PROMPT_FAMILIA,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = bedrock.invoke_model(modelId=MODEL_ID, body=json.dumps(body))
        resultado = json.loads(response["body"].read())
        return resultado["content"][0]["text"].strip()
    except Exception:
        return "Estou cuidando. Está tudo bem."


# ============================================================
# NOTIFICAÇÃO
# ============================================================

def notificar(evento, contexto):
    """
    Notifica a família sobre um evento.
    
    Args:
        evento: dict com tipo, urgencia, detalhes
        contexto: dict com nome, idoso_id
    
    Returns:
        dict com status
    """
    mensagem = gerar_mensagem_familia(evento, contexto)
    
    sns = _get_sns()
    if TOPIC_ARN and sns:
        try:
            sns.publish(
                TopicArn=TOPIC_ARN,
                Subject=f"[Libero] {evento.get('titulo', 'Notificação')}",
                Message=mensagem
            )
            print(f"[Libero Família] Notificação enviada: {mensagem[:60]}...")
        except Exception as e:
            print(f"[Libero Família] Erro SNS: {e}")
    else:
        print(f"[Libero Família] (simulado) {mensagem}")
    
    return {
        "notificado": True,
        "mensagem": mensagem,
        "urgencia": evento.get("urgencia", "media")
    }


# ============================================================
# RELATÓRIO DIÁRIO
# ============================================================

def gerar_relatorio_diario(historico, contexto):
    """Gera um relatório diário para a família."""
    total = len(historico)
    emergencias = [h for h in historico if h.get("nivel") == 3]
    intervencoes = [h for h in historico if h.get("nivel") == 2]
    memorias = [h for h in historico if "memoria" in h]
    
    relatorio = {
        "data": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "idoso_id": contexto.get("idoso_id"),
        "total_interacoes": total,
        "emergencias": len(emergencias),
        "intervencoes": len(intervencoes),
        "memorias_gravadas": len(memorias),
        "resumo": f"{total} interações, {len(emergencias)} emergências, {len(intervencoes)} intervenções, {len(memorias)} memórias gravadas."
    }
    
    return relatorio


# ============================================================
# TESTE
# ============================================================

if __name__ == "__main__":
    contexto = {"nome": "Dona Maria", "idoso_id": "dona-maria", "cuidador": "Ana"}
    
    testes = [
        {"tipo": "emergencia", "urgencia": "alta", "detalhes": "Dona Maria caiu. SAMU chamado."},
        {"tipo": "rotina", "urgencia": "baixa", "detalhes": "Dormiu bem. Tomou remédio."},
        {"tipo": "memoria", "urgencia": "baixa", "detalhes": "Contou história sobre o marido."},
    ]
    
    for evento in testes:
        print(f"\n[Teste] {evento['tipo']}")
        resultado = notificar(evento, contexto)
        print(f"  Urgência: {resultado['urgencia']}")
