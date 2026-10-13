"""
Libero - Protocolos de Crise
O que fazer em cada situação de crise.
"""

from enum import Enum


class Crise(Enum):
    SUNDOWNING = "sundowning"
    AGITACAO = "agitacao"
    AGRESSIVIDADE = "agressividade"
    ALUCINACAO = "alucinacao"
    DELIRIO = "delirio"
    FUGA = "fuga"
    QUEDA = "queda"
    CHORO = "choro"


PROTOCOLOS_CRISE = {
    Crise.SUNDOWNING: {
        "sinais": ["agitação ao entardecer", "confusão", "inquietação"],
        "acoes": [
            "Acender luzes suaves",
            "Tocar música calma da juventude",
            "Oferecer chá ou água",
            "Reduzir estímulos (TV, barulho)",
            "Falar devagar e com calma",
            "Validar a emoção",
        ],
        "nao_fazer": [
            "Não discutir",
            "Não corrigir",
            "Não acender luzes fortes",
            "Não aumentar estímulos",
        ]
    },
    Crise.AGITACAO: {
        "sinais": ["voz alta", "movimento acelerado", "repetição"],
        "acoes": [
            "Falar com calma",
            "Validar a emoção",
            "Oferecer distração (música, foto)",
            "Reduzir estímulos",
            "Se persistir, notificar família",
        ],
        "nao_fazer": [
            "Não conter fisicamente",
            "Não gritar",
            "Não ignorar",
        ]
    },
    Crise.AGRESSIVIDADE: {
        "sinais": ["gritos", "empurrões", "ameaças"],
        "acoes": [
            "Manter distância segura",
            "Falar com calma",
            "Não tocar sem permissão",
            "Oferecer espaço",
            "Notificar família imediatamente",
        ],
        "nao_fazer": [
            "Não revidar",
            "Não conter",
            "Não ameaçar",
        ]
    },
    Crise.ALUCINACAO: {
        "sinais": ["ver coisas que não existem", "ouvir vozes"],
        "acoes": [
            "Validar a emoção ('deve ser assustador')",
            "Não confirmar nem negar",
            "Redirecionar para outra atividade",
            "Verificar se há causa física (dor, infecção)",
            "Notificar família",
        ],
        "nao_fazer": [
            "Não dizer 'isso não existe'",
            "Não entrar na alucinação",
            "Não ignorar",
        ]
    },
    Crise.DELIRIO: {
        "sinais": ["acreditar em coisas falsas", "desconfiança"],
        "acoes": [
            "Validar a emoção",
            "Não confrontar",
            "Redirecionar",
            "Verificar causa física",
            "Notificar família",
        ],
        "nao_fazer": [
            "Não argumentar",
            "Não provar que está errado",
            "Não rir",
        ]
    },
    Crise.FUGA: {
        "sinais": ["tentativa de sair", "andar sem rumo", "confusão"],
        "acoes": [
            "Falar com calma ('Seu João, espere')",
            "Oferecer distração",
            "Acender luzes no caminho de volta",
            "Notificar família em 5 segundos",
            "Ativar GPS se sair",
            "Chamar polícia se não retornar em 15 min",
        ],
        "nao_fazer": [
            "Não bloquear fisicamente",
            "Não gritar",
            "Não assustar",
        ]
    },
    Crise.QUEDA: {
        "sinais": ["som de queda", "grito", "silêncio"],
        "acoes": [
            "Perguntar se está bem",
            "Pedir para não se mexer",
            "Ativar câmera se autorizado",
            "Notificar família imediatamente",
            "Chamar SAMU se necessário",
            "Ficar falando até ajuda chegar",
        ],
        "nao_fazer": [
            "Não tentar levantar",
            "Não mover",
            "Não ignorar",
        ]
    },
    Crise.CHORO: {
        "sinais": ["choro", "tristeza", "saudade"],
        "acoes": [
            "Validar a emoção",
            "Oferecer companhia",
            "Perguntar sobre a causa",
            "Tocar música calma",
            "Notificar família se persistir",
        ],
        "nao_fazer": [
            "Não dizer 'não chore'",
            "Não minimizar",
            "Não ignorar",
        ]
    },
}


def obter_protocolo(crise):
    """Retorna o protocolo de uma crise."""
    return PROTOCOLOS_CRISE.get(crise)


def detectar_crise(texto, features, contexto):
    """Detecta o tipo de crise baseado em texto e features."""
    texto_lower = texto.lower() if texto else ""
    
    if any(p in texto_lower for p in ["socorro", "caí", "dor", "machuquei"]):
        return Crise.QUEDA
    
    if any(p in texto_lower for p in ["vou sair", "vou trabalhar", "vou embora"]):
        return Crise.FUGA
    
    if any(p in texto_lower for p in ["não existe", "estou vendo", "estou ouvindo"]):
        return Crise.ALUCINACAO
    
    if any(p in texto_lower for p in ["estão roubando", "não confio", "me enganando"]):
        return Crise.DELIRIO
    
    energia = features.get("energia_media", 0)
    zcr = features.get("zcr", 0)
    
    if energia > 0.15 and zcr > 0.2:
        return Crise.AGRESSIVIDADE
    
    if energia > 0.1:
        return Crise.AGITACAO
    
    if "chorar" in texto_lower or "triste" in texto_lower:
        return Crise.CHORO
    
    return None


if __name__ == "__main__":
    print("=== Protocolos de Crise ===\n")
    for crise in Crise:
        protocolo = PROTOCOLOS_CRISE[crise]
        print(f"[{crise.name}]")
        print(f"  Sinais: {protocolo['sinais']}")
        print(f"  Ações: {len(protocolo['acoes'])}")
        print()
