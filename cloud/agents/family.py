"""
Libero - Agente de Família
Notificações honestas com estados verificáveis.
"""

import os
import json
import uuid
import boto3
from datetime import datetime, timezone
from enum import Enum
from dotenv import load_dotenv

load_dotenv()

REGION = os.getenv("AWS_REGION", "us-east-1")
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "").strip()
TOPIC_ARN = os.getenv("SNS_TOPIC_ARN", "")

_bedrock = None
_sns = None


class StatusNotificacao(Enum):
    """Estados reais de uma notificação."""
    SIMULATED = "simulated"   # Modo dev, não enviado
    QUEUED = "queued"         # Na fila
    SENT = "sent"             # Enviado à AWS
    DELIVERED = "delivered"   # Confirmado pela AWS
    FAILED = "failed"         # Falhou


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

SYSTEM_PROMPT_FAMILIA = """Você é o Libero, um companheiro para idosos com Alzheimer.

Sua função AGORA é FAMÍLIA. Você está se comunicando com o cuidador.

Princípios:
1. Nunca culpe o cuidador.
2. Reconheça o esforço dele.
3. Seja específico mas gentil.
4. Se for emergência, seja direto.
5. Se for rotina, seja tranquilizador.
6. Sempre diga que a IA está cuidando.
"""


def gerar_mensagem_familia(evento, contexto):
    """Gera uma mensagem para a família."""
    bedrock = _get_bedrock()
    
    if not bedrock:
        tipo = evento.get("tipo", "rotina")
        urgencia = evento.get("urgencia", "media")
        detalhes = evento.get("detalhes", "")
        
        if urgencia == "alta":
            return f"⚠️ EMERGÊNCIA: {detalhes}. Estou cuidando. Você quer falar?"
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
# NOTIFICAÇÃO HONESTA
# ============================================================

def notificar(evento, contexto):
    """
    Notifica a família com estados verificáveis.
    
    Returns:
        dict com:
        - id: ID único da notificação
        - status: StatusNotificacao
        - mensagem: texto enviado
        - tentativas: número de tentativas
        - erro: mensagem de erro (se houver)
        - timestamp: quando foi enviado
    """
    notif_id = str(uuid.uuid4())[:8]
    mensagem = gerar_mensagem_familia(evento, contexto)
    timestamp = datetime.now(timezone.utc).isoformat()
    
    resultado = {
        "id": notif_id,
        "status": StatusNotificacao.QUEUED.value,
        "mensagem": mensagem,
        "urgencia": evento.get("urgencia", "media"),
        "tentativas": 0,
        "timestamp": timestamp,
        "erro": None
    }
    
    sns = _get_sns()
    
    # Modo simulado: sem SNS configurado
    if not TOPIC_ARN or not sns:
        resultado["status"] = StatusNotificacao.SIMULATED.value
        resultado["motivo"] = "SNS não configurado"
        print(f"[Libero Família] (SIMULADO) [{notif_id}] {mensagem[:80]}")
        return resultado
    
    # Tentar enviar com retry
    max_tentativas = 3
    for tentativa in range(1, max_tentativas + 1):
        resultado["tentativas"] = tentativa
        try:
            response = sns.publish(
                TopicArn=TOPIC_ARN,
                Subject=f"[Libero] {evento.get('titulo', 'Notificação')}",
                Message=mensagem,
                MessageAttributes={
                    "urgencia": {
                        "DataType": "String",
                        "StringValue": evento.get("urgencia", "media")
                    },
                    "notif_id": {
                        "DataType": "String",
                        "StringValue": notif_id
                    }
                }
            )
            
            message_id = response.get("MessageId")
            
            if message_id:
                resultado["status"] = StatusNotificacao.SENT.value
                resultado["message_id"] = message_id
                print(f"[Libero Família] [{notif_id}] ENVIADO (msg_id: {message_id})")
                return resultado
            else:
                # Sem message_id = falha silenciosa
                resultado["status"] = StatusNotificacao.FAILED.value
                resultado["erro"] = "SNS não retornou MessageId"
                
        except Exception as e:
            resultado["erro"] = str(e)
            print(f"[Libero Família] [{notif_id}] Tentativa {tentativa} falhou: {e}")
            
            if tentativa < max_tentativas:
                import time
                time.sleep(1 * tentativa)  # Backoff
            else:
                resultado["status"] = StatusNotificacao.FAILED.value
    
    return resultado


# ============================================================
# RELATÓRIO DIÁRIO
# ============================================================

def gerar_relatorio_diario(historico, contexto):
    """Gera um relatório diário."""
    total = len(historico)
    emergencias = [h for h in historico if h.get("nivel") == 3]
    intervencoes = [h for h in historico if h.get("nivel") == 2]
    memorias = [h for h in historico if "memoria" in h]
    
    return {
        "data": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "idoso_id": contexto.get("idoso_id"),
        "total_interacoes": total,
        "emergencias": len(emergencias),
        "intervencoes": len(intervencoes),
        "memorias_gravadas": len(memorias),
        "resumo": f"{total} interações, {len(emergencias)} emergências, {len(intervencoes)} intervenções, {len(memorias)} memórias."
    }


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
        print(f"  ID: {resultado['id']}")
        print(f"  Status: {resultado['status']}")
        print(f"  Urgência: {resultado['urgencia']}")
        print(f"  Tentativas: {resultado['tentativas']}")
