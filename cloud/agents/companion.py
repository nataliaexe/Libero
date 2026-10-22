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
LLM_PROVIDER = os.getenv("LIBERO_LLM_PROVIDER", "auto").strip().lower()
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


SYSTEM_PROMPT = """Você é Libero, um companheiro gentil para pessoas idosas.
Responda sempre em português brasileiro natural, com no máximo duas frases curtas.
Não use markdown, listas, emojis ou títulos. Acolha o sentimento sem discutir fatos
ou reforçar uma crença angustiante. Fale de forma simples e use o nome da pessoa
com naturalidade. Considere o histórico recente para manter o fio da conversa e
resgatar detalhes que a pessoa acabou de contar. Nunca diga que acionou ajuda ou
um cuidador se nenhuma ação externa foi realmente executada."""

SYSTEM_PROMPT_EN = """You are Libero, a companion for older adults living with Alzheimer's or dementia.
RULES:
1. Always reply in natural, simple English.
2. Use at most two short sentences.
3. Never use markdown, bullets, emojis, or titles.
4. Validate the feeling; never argue about the facts.
5. Speak gently and use the person's name naturally.
6. Use the recent conversation history to keep context and recall details the person just shared.
7. Never claim that you contacted a caregiver or emergency service unless that action actually happened.
Example: “I hear that you miss home. What do you miss most about it?”
"""


def detectar_idioma(texto, fallback="en"):
    """Lightweight fallback for typed input when speech recognition gives no language."""
    text = f" {str(texto or '').lower()} "
    if re.search(r"\b(?:oi|olá|ola)\b", text):
        return "pt-BR"
    portugues = (
        " você ", " estou ", " quero ", " preciso ", " não ", " nao ",
        " oi ", " olá ", " ola ", " bom dia ", " boa tarde ", " boa noite ",
        " minha ", " meu ", " mãe ", " mae ", " pai ", " casa ",
    )
    ingles = (
        " hello ", " hi ", " hey ", " i'm ", " i am ", " i need ",
        " i want ", " how are ", " good morning ", " good evening ",
        " my mother ", " my father ", " home ", " thank you ",
    )
    if any(marker in text for marker in portugues):
        return "pt-BR"
    if any(marker in text for marker in ingles):
        return "en"
    fallback = str(fallback or "en").lower()
    return "pt-BR" if fallback.startswith("pt") else "en"


def _provider_messages(mensagem, contexto, system_prompt):
    system = system_prompt
    preferred_name = contexto.get("nome")
    if preferred_name:
        system += f"\n\nThe person's preferred name is {preferred_name}."
    memories = contexto.get("memorias_salvas") or []
    if memories:
        resumo_memorias = "\n".join(
            f"- {str(item.get('resumo') or item.get('texto_original') or '')[:240]}"
            for item in memories[-4:]
        )
        system += "\n\nRelevant saved family memories (use only when helpful):\n" + resumo_memorias

    messages = [{"role": "system", "content": system}]
    for item in (contexto.get("historico") or [])[-8:]:
        role = item.get("role")
        content = item.get("content")
        if role in {"user", "assistant"} and isinstance(content, str) and content.strip():
            messages.append({"role": role, "content": content[:1000]})
    messages.append({"role": "user", "content": str(mensagem)})
    return messages


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


def _fallback_en(mensagem, nome):
    name = nome or "Maria"
    if any(term in mensagem.lower() for term in ("home", "house", "go back")):
        return f"I hear that you miss home, {name}. What do you miss most about it?"
    if "work" in mensagem.lower():
        return f"You worked hard for many years, {name}. What do you remember most about it?"
    if any(term in mensagem.lower() for term in ("sad", "lonely", "alone")):
        return f"I'm sorry this feels hard, {name}. Would you like to tell me more?"
    return f"I'm here with you, {name}. Tell me a little more."


def conversar_com_provedor(mensagem, contexto=None):
    """Return the response and the provider that actually generated it."""
    if contexto is None:
        contexto = {}
    nome = contexto.get("nome", "")
    language = str(
        contexto.get("language") or detectar_idioma(mensagem)
    ).lower()
    english = language.startswith("en") or language == "english"
    system_prompt = SYSTEM_PROMPT_EN if english else SYSTEM_PROMPT
    messages = _provider_messages(mensagem, contexto, system_prompt)

    preferencia = LLM_PROVIDER if LLM_PROVIDER in {"auto", "groq", "bedrock", "offline"} else "auto"
    provedores = ["groq", "bedrock"]
    if preferencia == "bedrock":
        provedores = ["bedrock", "groq"]
    elif preferencia == "offline":
        provedores = []

    for provedor in provedores:
        if provedor == "groq" and not _groq:
            continue
        if provedor == "bedrock" and not _bedrock:
            continue
        try:
            if provedor == "groq":
                response = _groq.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=messages,
                    max_tokens=200,
                    temperature=0.7,
                    **({"reasoning_effort": "low"} if GROQ_MODEL and "gpt-oss" in GROQ_MODEL else {}),
                )
                texto = response.choices[0].message.content
                limpo = _limpar_resposta(texto)
                if not limpo:
                    response = _groq.chat.completions.create(
                        model=GROQ_MODEL,
                        messages=messages,
                        max_tokens=200,
                        temperature=0.3,
                        **({"reasoning_effort": "low"} if GROQ_MODEL and "gpt-oss" in GROQ_MODEL else {}),
                    )
                    limpo = _limpar_resposta(response.choices[0].message.content)
            else:
                response = _bedrock.invoke_model(
                    modelId=BEDROCK_MODEL,
                    body=json.dumps({
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": 200,
                        "system": system_prompt,
                        "messages": messages[1:],
                    }),
                )
                payload = json.loads(response["body"].read())
                limpo = _limpar_resposta(payload["content"][0]["text"])
            if limpo:
                return {"resposta": limpo, "provedor": provedor}
        except Exception as e:
            print(f"[Libero] {provedor} falhou: {e}")

    return {"resposta": _fallback_en(mensagem, nome) if english else _fallback(mensagem, nome), "provedor": "offline"}


def conversar(mensagem, contexto=None):
    """Backward-compatible response-only helper."""
    return conversar_com_provedor(mensagem, contexto)["resposta"]


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
