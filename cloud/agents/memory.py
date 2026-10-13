"""
Libero - Agente de Memória
Grava, organiza e preserva histórias do idoso.
"""

import os
import json
import boto3
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

REGION = os.getenv("AWS_REGION", "us-east-1")
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")
BUCKET = os.getenv("S3_BUCKET", "")

_bedrock = None
_s3 = None

def _get_bedrock():
    global _bedrock
    if _bedrock is None:
        try:
            _bedrock = boto3.client("bedrock-runtime", region_name=REGION)
        except Exception as e:
            print(f"[Libero] Bedrock não disponível: {e}")
            _bedrock = False
    return _bedrock

def _get_s3():
    global _s3
    if _s3 is None:
        try:
            _s3 = boto3.client("s3", region_name=REGION)
        except Exception as e:
            _s3 = False
    return _s3


# ============================================================
# DETECÇÃO DE HISTÓRIA
# ============================================================

def detectar_historia(texto):
    """Detecta se o texto contém uma história que vale gravar."""
    if not texto or len(texto) < 15:
        return {"detectado": False, "confianca": 0.0}
    
    texto_lower = texto.lower()
    
    # Marcadores de história (memória pessoal)
    marcadores = [
        "quando eu era", "na minha época", "eu trabalhei",
        "eu conheci", "meu pai", "minha mãe", "meu marido",
        "minha esposa", "meus filhos", "eu morava",
        "eu estudava", "eu brincava", "eu dançava",
        "me ensinou", "eu aprendi", "eu fiz", "eu fui",
        "eu tinha", "a gente", "nós"
    ]
    
    score = 0
    for marcador in marcadores:
        if marcador in texto_lower:
            score += 0.3
    
    # Texto mais longo = mais provável ser história
    if len(texto) > 60:
        score += 0.2
    
    # Verbos no passado = história
    verbos_passado = [
        "era", "foi", "tinha", "fazia", "morava",
        "trabalhava", "dançava", "brincava", "estudava",
        "conheci", "aprendi", "ensinou"
    ]
    if any(v in texto_lower for v in verbos_passado):
        score += 0.2
    
    if score >= 0.4:
        return {"detectado": True, "confianca": min(score, 1.0)}
    
    return {"detectado": False, "confianca": score}


# ============================================================
# ORGANIZAÇÃO DE HISTÓRIA
# ============================================================

SYSTEM_PROMPT_MEMORIA = """Você é o Libero. Extraia a essência da história.

Retorne APENAS um JSON válido:
{
  "titulo": "...",
  "resumo": "...",
  "pessoas": ["..."],
  "lugares": ["..."],
  "emocao": "...",
  "tags": ["..."]
}
"""


def organizar_historia(texto, contexto):
    """Organiza uma história usando Bedrock."""
    bedrock = _get_bedrock()
    
    if not bedrock:
        # Fallback offline: extração simples
        return {
            "titulo": texto[:50] + ("..." if len(texto) > 50 else ""),
            "resumo": texto[:150],
            "pessoas": [],
            "lugares": [],
            "emocao": "neutra",
            "tags": []
        }
    
    prompt = f"""História contada por {contexto.get('nome', 'idoso')}:
"{texto}"

Retorne APENAS o JSON."""
    
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 500,
        "system": SYSTEM_PROMPT_MEMORIA,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = bedrock.invoke_model(modelId=MODEL_ID, body=json.dumps(body))
        resultado = json.loads(response["body"].read())
        texto_resposta = resultado["content"][0]["text"].strip()
        
        if texto_resposta.startswith("```"):
            texto_resposta = texto_resposta.split("```")[1]
            if texto_resposta.startswith("json"):
                texto_resposta = texto_resposta[4:]
        
        return json.loads(texto_resposta)
    except Exception as e:
        print(f"[Libero Memória] Erro: {e}")
        return {
            "titulo": texto[:50],
            "resumo": texto[:150],
            "pessoas": [],
            "lugares": [],
            "emocao": "neutra",
            "tags": []
        }


# ============================================================
# GRAVAÇÃO
# ============================================================

def gravar_memoria(idoso_id, texto, contexto):
    """Grava uma memória."""
    historia = detectar_historia(texto)
    
    if not historia["detectado"]:
        return {"gravado": False, "motivo": "Não é uma história"}
    
    organizada = organizar_historia(texto, contexto)
    
    memoria = {
        "idoso_id": idoso_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "texto_original": texto,
        "titulo": organizada.get("titulo", "História"),
        "resumo": organizada.get("resumo", ""),
        "pessoas": organizada.get("pessoas", []),
        "lugares": organizada.get("lugares", []),
        "emocao": organizada.get("emocao", "neutra"),
        "tags": organizada.get("tags", []),
        "confianca": historia["confianca"]
    }
    
    s3 = _get_s3()
    if BUCKET and s3:
        try:
            key = f"memorias/{idoso_id}/{datetime.now(timezone.utc).isoformat()}.json"
            s3.put_object(
                Bucket=BUCKET,
                Key=key,
                Body=json.dumps(memoria, ensure_ascii=False, indent=2),
                ContentType="application/json"
            )
            memoria["s3_key"] = key
            print(f"[Libero Memória] Salvo em s3://{BUCKET}/{key}")
        except Exception as e:
            print(f"[Libero Memória] Erro S3: {e}")
    else:
        print(f"[Libero Memória] Gravado localmente: {memoria['titulo']}")
    
    return {"gravado": True, "memoria": memoria}


if __name__ == "__main__":
    contexto = {"nome": "Dona Maria", "hora": "15:00"}
    
    testes = [
        "Quando eu era jovem, eu dançava toda sexta com meu marido. Ele era lindo.",
        "Bom dia.",
        "Meu pai me ensinou a trabalhar. Ele era muito bom.",
    ]
    
    for texto in testes:
        print(f"\n[Teste] '{texto[:60]}...'")
        resultado = gravar_memoria("dona-maria", texto, contexto)
        if resultado["gravado"]:
            m = resultado["memoria"]
            print(f"  Título: {m['titulo']}")
            print(f"  Emoção: {m['emocao']}")
            print(f"  Confiança: {m['confianca']}")
        else:
            print(f"  Não gravado: {resultado['motivo']}")
