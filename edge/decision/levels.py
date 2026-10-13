"""
Libero - Níveis de Decisão
"""

from enum import Enum
from datetime import datetime


class Nivel(Enum):
    OBSERVACAO = 0
    CONVERSA = 1
    INTERVENCAO = 2
    EMERGENCIA = 3


PALAVRAS_EMERGENCIA = [
    "socorro", "caí", "cai", "caiu", "dor", "ajuda",
    "me machuquei", "não consigo", "sangue", "quebrei",
    "não sinto"
]

# Palavras que indicam confusão (NÃO incluir marido/mãe/pai — são memórias)
PALAVRAS_CONFUSAO = [
    "onde estou", "quem é você", "cadê", "preciso ir",
    "vou embora", "quero ir", "me leva"
]

PALAVRAS_SOLIDAO = [
    "sozinho", "sozinha", "ninguém", "triste", "chorar"
]


def decidir_nivel(texto, hora=None, movimento=False):
    """Decide o nível de intervenção."""
    if hora is None:
        hora = datetime.now().hour
    
    texto_lower = texto.lower() if texto else ""
    
    # PRIORIDADE 1: Emergência
    if any(p in texto_lower for p in PALAVRAS_EMERGENCIA):
        return Nivel.EMERGENCIA
    
    # PRIORIDADE 2: Confusão (frases específicas)
    if any(p in texto_lower for p in PALAVRAS_CONFUSAO):
        return Nivel.INTERVENCAO
    
    # PRIORIDADE 3: Madrugada + movimento
    if 2 <= hora <= 5 and movimento:
        return Nivel.INTERVENCAO
    
    # PRIORIDADE 4: Solidão
    if any(p in texto_lower for p in PALAVRAS_SOLIDAO):
        return Nivel.CONVERSA
    
    # PRIORIDADE 5: Conversa normal
    if texto_lower and len(texto_lower) > 10:
        return Nivel.CONVERSA
    
    return Nivel.OBSERVACAO


def descrever_nivel(nivel):
    descricoes = {
        Nivel.OBSERVACAO: "Observação passiva",
        Nivel.CONVERSA: "Conversa proativa",
        Nivel.INTERVENCAO: "Intervenção ativa",
        Nivel.EMERGENCIA: "Emergência",
    }
    return descricoes.get(nivel, "Desconhecido")


if __name__ == "__main__":
    testes = [
        ("Preciso ir para casa", 15, False),
        ("Socorro, caí", 3, True),
        ("Estou sozinha", 14, False),
        ("Bom dia", 8, False),
        ("Quando eu era jovem, eu dançava com meu marido", 15, False),
    ]
    
    for texto, hora, movimento in testes:
        nivel = decidir_nivel(texto, hora, movimento)
        print(f"[Libero] '{texto}' → {nivel.name}")
