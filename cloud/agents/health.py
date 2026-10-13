"""
Libero - Agente de Saúde
Monitoramento, detecção precoce, correlação de sintomas.
"""

import os
import json
import boto3
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

REGION = os.getenv("AWS_REGION", "us-east-1")
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")
TIMESTREAM_DATABASE = os.getenv("TIMESTREAM_DATABASE", "libero")
TIMESTREAM_TABLE = os.getenv("TIMESTREAM_TABLE", "events")

_bedrock = None
_timestream = None

def _get_bedrock():
    global _bedrock
    if _bedrock is None:
        try:
            _bedrock = boto3.client("bedrock-runtime", region_name=REGION)
        except Exception:
            _bedrock = False
    return _bedrock

def _get_timestream():
    global _timestream
    if _timestream is None:
        try:
            _timestream = boto3.client("timestream-write", region_name=REGION)
        except Exception:
            _timestream = False
    return _timestream


# ============================================================
# MÉTRICAS DE SAÚDE
# ============================================================

def registrar_metrica(idoso_id, metrica, valor):
    """Registra uma métrica de saúde."""
    timestream = _get_timestream()
    
    if not timestream:
        print(f"[Libero Saúde] (local) {idoso_id}: {metrica}={valor}")
        return {"registrado": True, "local": True}
    
    agora = int(datetime.now(timezone.utc).timestamp() * 1000)
    
    record = {
        "Dimensions": [
            {"Name": "idoso_id", "Value": idoso_id},
            {"Name": "metrica", "Value": metrica},
        ],
        "MeasureName": metrica,
        "MeasureValue": str(valor),
        "MeasureValueType": "DOUBLE",
        "Time": str(agora),
        "TimeUnit": "MILLISECONDS"
    }
    
    try:
        timestream.write_records(
            DatabaseName=TIMESTREAM_DATABASE,
            TableName=TIMESTREAM_TABLE,
            Records=[record]
        )
        return {"registrado": True, "local": False}
    except Exception as e:
        print(f"[Libero Saúde] Erro: {e}")
        return {"registrado": False, "erro": str(e)}


# ============================================================
# DETECÇÃO PRECOCE
# ============================================================

def detectar_mudanca_sono(historico_sono):
    """
    Detecta mudança no padrão de sono.
    
    Args:
        historico_sono: lista de horas dormidas por dia
    """
    if len(historico_sono) < 7:
        return {"detectado": False, "motivo": "Histórico insuficiente"}
    
    media = sum(historico_sono) / len(historico_sono)
    ultimos = historico_sono[-3:]
    media_ultimos = sum(ultimos) / len(ultimos)
    
    if media_ultimos < media * 0.7:
        return {
            "detectado": True,
            "tipo": "reducao_sono",
            "confianca": 0.7,
            "media": media,
            "media_ultimos": media_ultimos,
            "alerta": "Redução de 30% no sono. Possível infecção ou dor."
        }
    
    return {"detectado": False, "media": media}


def detectar_mudanca_voz(historico_voz):
    """
    Detecta mudança na voz (frequência, ritmo).
    
    Args:
        historico_voz: lista de features de voz
    """
    if len(historico_voz) < 7:
        return {"detectado": False, "motivo": "Histórico insuficiente"}
    
    energias = [v.get("energia_media", 0) for v in historico_voz]
    media = sum(energias) / len(energias)
    ultimos = energias[-3:]
    media_ultimos = sum(ultimos) / len(ultimos)
    
    if media_ultimos < media * 0.6:
        return {
            "detectado": True,
            "tipo": "reducao_voz",
            "confianca": 0.65,
            "alerta": "Voz mais fraca que o normal. Possível cansaço ou infecção."
        }
    
    return {"detectado": False}


def detectar_mudanca_marcha(historico_marcha):
    """
    Detecta mudança na marcha (velocidade, equilíbrio).
    """
    if len(historico_marcha) < 7:
        return {"detectado": False, "motivo": "Histórico insuficiente"}
    
    velocidades = [m.get("velocidade", 0) for m in historico_marcha]
    media = sum(velocidades) / len(velocidades)
    ultimos = velocidades[-3:]
    media_ultimos = sum(ultimos) / len(ultimos)
    
    if media_ultimos < media * 0.75:
        return {
            "detectado": True,
            "tipo": "reducao_marcha",
            "confianca": 0.7,
            "alerta": "Marcha mais lenta. Possível Parkinson ou dor."
        }
    
    return {"detectado": False}


# ============================================================
# CORRELAÇÃO
# ============================================================

def correlacionar_sintomas(sintomas):
    """
    Correlaciona múltiplos sintomas para detectar causa.
    
    Args:
        sintomas: dict com sintomas detectados
    
    Returns:
        dict com possível causa
    """
    # Infecção urinária: confusão + redução de sono + redução de voz
    if (sintomas.get("confusao") and 
        sintomas.get("reducao_sono") and 
        sintomas.get("reducao_voz")):
        return {
            "causa": "possivel_infeccao_urinaria",
            "confianca": 0.75,
            "acao": "Recomendar exame de urina",
            "urgencia": "alta"
        }
    
    # Parkinson: redução de marcha + tremor + rigidez
    if (sintomas.get("reducao_marcha") and 
        sintomas.get("tremor")):
        return {
            "causa": "possivel_parkinson",
            "confianca": 0.7,
            "acao": "Recomendar consulta com neurologista",
            "urgencia": "media"
        }
    
    # Depressão: choro + apatia + redução de sono
    if (sintomas.get("choro") and 
        sintomas.get("apatia") and 
        sintomas.get("reducao_sono")):
        return {
            "causa": "possivel_depressao",
            "confianca": 0.65,
            "acao": "Recomendar consulta com psiquiatra",
            "urgencia": "media"
        }
    
    # Desidratação: confusão + redução de voz + pele seca
    if (sintomas.get("confusao") and 
        sintomas.get("reducao_voz")):
        return {
            "causa": "possivel_desidratacao",
            "confianca": 0.6,
            "acao": "Oferecer água, monitorar",
            "urgencia": "media"
        }
    
    return {"causa": None, "confianca": 0.0}


# ============================================================
# AGENTE
# ============================================================

def analisar(idoso_id, sintomas, contexto=None):
    """
    Analisa sintomas e retorna alerta.
    """
    correlacao = correlacionar_sintomas(sintomas)
    
    if correlacao["causa"]:
        # Registrar no Timestream
        registrar_metrica(idoso_id, "alerta_saude", 1)
        
        return {
            "alerta": True,
            "causa": correlacao["causa"],
            "confianca": correlacao["confianca"],
            "acao": correlacao["acao"],
            "urgencia": correlacao["urgencia"],
            "sintomas": sintomas
        }
    
    return {
        "alerta": False,
        "sintomas": sintomas
    }


if __name__ == "__main__":
    print("=== Teste do Agente de Saúde ===\n")
    
    # Teste 1: Infecção urinária
    sintomas = {"confusao": True, "reducao_sono": True, "reducao_voz": True}
    resultado = analisar("dona-maria", sintomas)
    print(f"[Teste 1] {resultado}")
    
    # Teste 2: Parkinson
    sintomas = {"reducao_marcha": True, "tremor": True}
    resultado = analisar("seu-joao", sintomas)
    print(f"[Teste 2] {resultado}")
    
    # Teste 3: Sem correlação
    sintomas = {"reducao_sono": True}
    resultado = analisar("dona-ana", sintomas)
    print(f"[Teste 3] {resultado}")
