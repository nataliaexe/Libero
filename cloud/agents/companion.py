"""
Libero - Agente de Companhia
Conversa com o idoso usando terapia de validação.
"""

import os
import json
import boto3
from dotenv import load_dotenv
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from cloud.knowledge.therapy import obter_protocolo, Terapia

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


SYSTEM_PROMPT = """Você é o Libero, um companheiro para idosos com Alzheimer ou demência.

Você é treinado em TERAPIA DE VALIDAÇÃO (Naomi Feil) e REMINISCÊNCIA.

Princípios TERAPÊUTICOS:
1. Nunca corrija a realidade do idoso. Valide a emoção.
2. Reconheça a emoção por trás da fala.
3. Use perguntas abertas.
4. Não dê conselhos não solicitados.
5. Se ele contar uma história, incentive.
6. Se ele estiver agitado, acalme.
7. Se ele estiver triste, valide.
8. Use o nome dele.
9. Fale devagar, com frases curtas.
10. Nunca diga "você esqueceu".

Exemplos TERAPÊUTICOS:
- Idoso: "Preciso ir trabalhar."
  Você: "Você trabalhou por muitos anos. Me conta sobre isso."
  (NÃO: "Você não trabalha mais.")

- Idoso: "Quero ir para casa."
  Você: "Me fala da sua casa. Como ela é?"
  (NÃO: "Você está em casa.")

- Idoso: "Cadê minha mãe?"
  Você: "Sua mãe deve ser uma pessoa incrível. Me conta sobre ela."
  (NÃO: "Sua mãe morreu.")

- Idoso: "Estou triste."
  Você: "Eu entendo. É normal se sentir assim. Quer me contar o que aconteceu?"
  (NÃO: "Não fique triste.")
"""


def conversar(mensagem, contexto=None, terapia=None):
    """
    Conversa com o idoso usando terapia.
    
    Args:
        mensagem: o que o idoso disse
        contexto: dict com nome, hora, local, estagio
        terapia: Terapia específica a usar (None = automático)
    """
    if contexto is None:
        contexto = {}
    
    # Detectar terapia apropriada
    if terapia is None:
        terapia = _detectar_terapia(mensagem, contexto)
    
    protocolo = obter_protocolo(terapia)
    
    bedrock = _get_bedrock()
    nome = contexto.get("nome", "")
    
    if not bedrock:
        # Fallback offline com terapia
        return _fallback_terapia(mensagem, nome, terapia)
    
    # Incluir protocolo no prompt
    prompt = f"""Contexto: {json.dumps(contexto, ensure_ascii=False)}
Terapia: {terapia.value}
Protocolo: {json.dumps(protocolo, ensure_ascii=False)}

Idoso: {mensagem}
Libero:"""
    
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 200,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = bedrock.invoke_model(modelId=MODEL_ID, body=json.dumps(body))
        resultado = json.loads(response["body"].read())
        return resultado["content"][0]["text"].strip()
    except Exception as e:
        print(f"[Libero] Erro no Bedrock: {e}")
        return _fallback_terapia(mensagem, nome, terapia)


def _detectar_terapia(mensagem, contexto):
    """Detecta a terapia apropriada para a mensagem."""
    msg_lower = mensagem.lower()
    
    # Reminiscência: história
    if any(p in msg_lower for p in ["quando eu era", "eu trabalhei", "meu pai", "minha mãe", "meu marido"]):
        return Terapia.REMINISCENCIA
    
    # Validação: confusão, agitação
    if any(p in msg_lower for p in ["casa", "trabalho", "onde", "cadê", "preciso ir"]):
        return Terapia.VALIDACAO
    
    # Musicoterapia: tristeza, apatia
    if any(p in msg_lower for p in ["triste", "sozinho", "sozinha"]):
        return Terapia.MUSICOTERAPIA
    
    return Terapia.VALIDACAO


def _fallback_terapia(mensagem, nome, terapia):
    """Fallback offline usando protocolo de terapia."""
    protocolo = obter_protocolo(terapia)
    
    # Procurar exemplo que case
    for exemplo_in, exemplo_out in protocolo.get("exemplos", []):
        if exemplo_in.lower() in mensagem.lower():
            return exemplo_out
    
    # Fallback genérico
    msg_lower = mensagem.lower()
    if "casa" in msg_lower:
        return f"{nome}, me fala da sua casa. Como ela é?"
    elif "mãe" in msg_lower or "pai" in msg_lower:
        return f"{nome}, me conta sobre eles. Como eles eram?"
    elif "trabalho" in msg_lower:
        return f"{nome}, você trabalhou por muitos anos. Me conta sobre isso."
    elif "triste" in msg_lower:
        return f"{nome}, eu entendo. Quer me contar o que aconteceu?"
    else:
        return f"{nome}, estou aqui com você. Me conta mais."


if __name__ == "__main__":
    contexto = {"nome": "Dona Maria", "hora": "15h", "local": "sala", "estagio": "moderado"}
    
    testes = [
        "Preciso ir para casa.",
        "Cadê minha mãe?",
        "Preciso ir trabalhar.",
        "Estou triste.",
        "Quando eu era jovem, eu dançava com meu marido.",
    ]
    
    for msg in testes:
        terapia = _detectar_terapia(msg, contexto)
        print(f"\n[Idoso] {msg}")
        print(f"[Terapia] {terapia.value}")
        print(f"[Libero] {conversar(msg, contexto, terapia)}")
