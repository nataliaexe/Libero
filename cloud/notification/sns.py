"""
Libero - Notificações
Envia notificações para a família via SNS.
"""

import os
import json
import boto3
from dotenv import load_dotenv

load_dotenv()

REGION = os.getenv("AWS_REGION", "us-east-1")
TOPIC_ARN = os.getenv("SNS_TOPIC_ARN", "")

sns = boto3.client("sns", region_name=REGION)


def notificar_familia(idoso_id, evento, urgencia="media", detalhes=None):
    """
    Notifica a família sobre um evento.
    
    Args:
        idoso_id: ID do idoso
        evento: descrição do evento
        urgencia: baixa, media, alta
        detalhes: dict com informações adicionais
    """
    if not TOPIC_ARN:
        print("[Libero] SNS_TOPIC_ARN não configurado. Notificação simulada.")
        print(f"[Libero] → Família: [{urgencia.upper()}] {evento}")
        return
    
    mensagem = {
        "idoso_id": idoso_id,
        "evento": evento,
        "urgencia": urgencia,
        "detalhes": detalhes or {},
    }
    
    try:
        sns.publish(
            TopicArn=TOPIC_ARN,
            Subject=f"[Libero] {evento}",
            Message=json.dumps(mensagem, ensure_ascii=False, indent=2)
        )
        print(f"[Libero] Notificação enviada: {evento}")
    except Exception as e:
        print(f"[Libero] Erro SNS: {e}")


if __name__ == "__main__":
    notificar_familia(
        "dona-maria",
        "Dona Maria está tentando sair",
        "alta",
        {"local": "porta da frente", "hora": "03:15"}
    )
