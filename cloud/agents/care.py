"""
Libero - Agente de Cuidado
Lembra remédios, água, comida, banheiro.
Respeitoso, adaptativo, não intrusivo.
"""

import os
import json
import boto3
from datetime import datetime, timezone, timedelta
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
# ROTINAS
# ============================================================

ROTINA_PADRAO = {
    "remedios": [
        {"nome": "Pressão", "horario": "07:00", "periodo": "manhã"},
        {"nome": "Pressão", "horario": "19:00", "periodo": "noite"},
        {"nome": "Diabetes", "horario": "07:30", "periodo": "manhã"},
        {"nome": "Diabetes", "horario": "19:30", "periodo": "noite"},
    ],
    "agua": [
        {"horario": "08:00", "periodo": "manhã"},
        {"horario": "10:00", "periodo": "manhã"},
        {"horario": "14:00", "periodo": "tarde"},
        {"horario": "16:00", "periodo": "tarde"},
        {"horario": "20:00", "periodo": "noite"},
    ],
    "refeicoes": [
        {"nome": "Café da manhã", "horario": "07:00"},
        {"nome": "Almoço", "horario": "12:00"},
        {"nome": "Jantar", "horario": "18:00"},
    ],
}


def verificar_lembretes(hora_atual=None, rotina=None):
    """
    Verifica quais lembretes devem ser disparados agora.
    
    Returns:
        list de lembretes
    """
    if hora_atual is None:
        hora_atual = datetime.now().strftime("%H:%M")
    
    if rotina is None:
        rotina = ROTINA_PADRAO
    
    lembretes = []
    
    # Verificar remédios
    for remedio in rotina.get("remedios", []):
        if remedio["horario"] == hora_atual:
            lembretes.append({
                "tipo": "remedio",
                "nome": remedio["nome"],
                "horario": remedio["horario"],
                "urgencia": "alta"
            })
    
    # Verificar água
    for agua in rotina.get("agua", []):
        if agua["horario"] == hora_atual:
            lembretes.append({
                "tipo": "agua",
                "horario": agua["horario"],
                "urgencia": "media"
            })
    
    # Verificar refeições
    for refeicao in rotina.get("refeicoes", []):
        if refeicao["horario"] == hora_atual:
            lembretes.append({
                "tipo": "refeicao",
                "nome": refeicao["nome"],
                "horario": refeicao["horario"],
                "urgencia": "media"
            })
    
    return lembretes


# ============================================================
# GERAÇÃO DE MENSAGEM
# ============================================================

SYSTEM_PROMPT_CUIDADO = """Você é o Libero, um companheiro para idosos com Alzheimer ou demência.

Sua função AGORA é CUIDADO. Lembre o idoso de algo importante.

Princípios:
1. Nunca ordene. Sugira.
2. Nunca diga "você esqueceu". Diga "está na hora de".
3. Use o nome dele.
4. Seja específico mas gentil.
5. Se ele recusar, não insista. Ofereça alternativa.
6. Se for remédio, seja claro mas calmo.

Exemplos:
- Remédio: "Seu João, está na hora do remédio da pressão. Está na caixinha de manhã."
- Água: "Dona Maria, que tal um copo de água? Está calor hoje."
- Refeição: "Seu João, o almoço está pronto. Vamos comer?"
"""


def gerar_mensagem_cuidado(lembrete, contexto):
    """Gera uma mensagem de cuidado."""
    bedrock = _get_bedrock()
    nome = contexto.get("nome", "")
    
    if not bedrock:
        # Fallback offline
        tipo = lembrete["tipo"]
        if tipo == "remedio":
            return f"{nome}, está na hora do remédio de {lembrete['nome']}."
        elif tipo == "agua":
            return f"{nome}, que tal um copo de água?"
        elif tipo == "refeicao":
            return f"{nome}, está na hora do {lembrete['nome']}."
        return f"{nome}, está na hora."
    
    prompt = f"""Lembrete: {json.dumps(lembrete, ensure_ascii=False)}
Contexto: {json.dumps(contexto, ensure_ascii=False)}

Gere uma mensagem curta, gentil e específica."""
    
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 100,
        "system": SYSTEM_PROMPT_CUIDADO,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = bedrock.invoke_model(modelId=MODEL_ID, body=json.dumps(body))
        resultado = json.loads(response["body"].read())
        return resultado["content"][0]["text"].strip()
    except Exception:
        return f"{nome}, está na hora."


# ============================================================
# AÇÃO
# ============================================================

def agir(lembretes, contexto):
    """
    Gera ações para os lembretes.
    
    Returns:
        dict com ações
    """
    if not lembretes:
        return {"acoes": [], "nivel": 0}
    
    acoes = []
    
    for lembrete in lembretes:
        mensagem = gerar_mensagem_cuidado(lembrete, contexto)
        acoes.append({
            "tipo": "voz",
            "conteudo": mensagem,
            "lembrete": lembrete
        })
    
    return {
        "acoes": acoes,
        "nivel": 1,
        "total": len(lembretes)
    }


# ============================================================
# TESTE
# ============================================================

if __name__ == "__main__":
    contexto = {"nome": "Dona Maria", "local": "sala"}
    
    # Testar com hora específica
    testes = [
        ("07:00", "Remédio da manhã"),
        ("07:30", "Remédio diabetes"),
        ("12:00", "Almoço"),
        ("15:00", "Nada"),
    ]
    
    for hora, descricao in testes:
        print(f"\n[Teste] {hora} - {descricao}")
        lembretes = verificar_lembretes(hora)
        
        if lembretes:
            resultado = agir(lembretes, contexto)
            for acao in resultado["acoes"]:
                print(f"  → {acao['conteudo']}")
        else:
            print(f"  Sem lembretes.")
