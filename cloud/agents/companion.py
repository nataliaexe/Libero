"""
Libero - Agente de Companhia
Groq (Llama) primeiro, Bedrock segundo, fallback offline por último.
"""

import os
import re
import json
from dotenv import load_dotenv

load_dotenv()

# Groq
try:
    from groq import Groq
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_LLM_MODEL", "openai/gpt-oss-120b")
    _groq = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
except ImportError:
    _groq = None
    GROQ_MODEL = None

# Bedrock
try:
    import boto3
    REGION = os.getenv("AWS_REGION", "us-east-2")
    BEDROCK_MODEL = os.getenv("BEDROCK_MODEL_ID", "")
    _bedrock = boto3.client("bedrock-runtime", region_name=REGION) if BEDROCK_MODEL else None
except Exception:
    _bedrock = None
    BEDROCK_MODEL = None


SYSTEM_PROMPT = """Você é o Libero, um companheiro para idosos com Alzheimer ou demência.

REGRAS:
1. Responda SEMPRE em português brasileiro.
2. Máximo 2 frases curtas.
3. NUNCA use markdown, asteriscos, bullets, emojis, títulos.
4. NUNCA explique o que você está fazendo.
5. Fale como uma pessoa fala. Simples. Gentil.
6. Valide a emoção, nunca corrija a realidade.
7. Use o nome dele naturalmente.

Exemplos CORRETOS:
- "Entendo, Dona Maria. Me conta mais sobre isso."
- "Sua mãe deve ter sido especial. Como ela era?"
- "Estou aqui com você. Está tudo bem."

Exemplos ERRADOS (não faça):
- "## Resposta para Dona Maria"
- "**Dona Maria**, percebi que..."
- "✓ Notificando cuidador"
- "Vou te ajudar com isso! 😊"
"""


def _limpar_resposta(texto):
    """Remove markdown e limita a 2 frases."""
    if not texto:
        return None
    
    # Remover markdown
    texto = re.sub(r'[#*_`~]', '', texto)
    texto = re.sub(r'^\s*[-•]\s*', '', texto, flags=re.MULTILINE)
    
    # Substituir quebras por espaço
    texto = re.sub(r'\s+', ' ', texto).strip()
    
    # Cortar em até 2 frases
    frases = re.split(r'(?<=[.!?])\s+', texto)
    frases = [f.strip() for f in frases if f.strip()]
    
    if not frases:
        return None
    
    resultado = ' '.join(frases[:2]).strip()
    
    # Se ficou muito curto (< 10 chars), retornar None
    if len(resultado) < 10:
        return None
    
    return resultado


def _fallback(mensagem, nome):
    """Fallback offline."""
    msg_lower = mensagem.lower()
    if "casa" in msg_lower:
        return f"{nome}, me fala da sua casa. Como ela é?"
    elif "mãe" in msg_lower or "pai" in msg_lower:
        return f"{nome}, me conta sobre eles. Como eles eram?"
    elif "trabalho" in msg_lower:
        return f"{nome}, você trabalhou por muitos anos. Me conta sobre isso."
    elif "triste" in msg_lower or "sozinh" in msg_lower:
        return f"{nome}, eu entendo. Quer me contar o que aconteceu?"
    else:
        return f"{nome}, estou aqui com você. Me conta mais."


def conversar(mensagem, contexto=None):
    """Conversa com o idoso."""
    if contexto is None:
        contexto = {}
    
    nome = contexto.get("nome", "")
    
    # 1. Groq
    if _groq:
        try:
            response = _groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Nome: {nome}\nIdoso: {mensagem}"}
                ],
                max_tokens=200,
                temperature=0.7,
                **({"reasoning_effort": "low"} if GROQ_MODEL and "gpt-oss" in GROQ_MODEL else {}),
            )
            texto = response.choices[0].message.content
            limpo = _limpar_resposta(texto)
            if limpo:
                return limpo
            # Se vazio, tenta de novo com temperatura menor
            response = _groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Nome: {nome}\nIdoso: {mensagem}"}
                ],
                max_tokens=200,
                temperature=0.3,
                **({"reasoning_effort": "low"} if GROQ_MODEL and "gpt-oss" in GROQ_MODEL else {}),
            )
            texto = response.choices[0].message.content
            limpo = _limpar_resposta(texto)
            if limpo:
                return limpo
        except Exception as e:
            print(f"[Libero] Groq falhou: {e}")
    
    # 2. Bedrock
    if _bedrock:
        try:
            response = _bedrock.invoke_model(
                modelId=BEDROCK_MODEL,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 200,
                    "system": SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": f"Nome: {nome}\nIdoso: {mensagem}"}]
                })
            )
            resultado = json.loads(response["body"].read())
            limpo = _limpar_resposta(resultado["content"][0]["text"])
            if limpo:
                return limpo
        except Exception as e:
            print(f"[Libero] Bedrock falhou: {e}")
    
    # 3. Fallback
    return _fallback(mensagem, nome)


if __name__ == "__main__":
    contexto = {"nome": "Dona Maria"}
    testes = [
        "Preciso ir para casa.",
        "Cadê minha mãe?",
        "Preciso ir trabalhar.",
        "Estou triste.",
        "Oi, tudo bem?",
        "Quero um copo de água.",
    ]
    for msg in testes:
        resposta = conversar(msg, contexto)
        print(f"\n[Idoso] {msg}")
        print(f"[Libero] {resposta}")
