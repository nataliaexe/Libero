"""
Libero - Estágios da Demência
Baseado em Braak, Reisberg, CDR e GDS.
"""

from enum import Enum


class Estagio(Enum):
    PRECLINICO = 0
    LEVE = 1
    MODERADO_LEVE = 2
    MODERADO = 3
    MODERADO_GRAVE = 4
    GRAVE = 5
    TERMINAL = 6


SINTOMAS = {
    Estagio.PRECLINICO: {
        "cognitivos": ["leve perda de memória episódica"],
        "comportamentais": [],
        "funcionais": [],
        "intervencoes": ["estimulação cognitiva", "exercício físico"]
    },
    Estagio.LEVE: {
        "cognitivos": ["esquecimento de nomes", "dificuldade de concentração"],
        "comportamentais": ["ansiedade leve", "irritabilidade"],
        "funcionais": ["dificuldade com finanças", "perda de objetos"],
        "intervencoes": ["reminiscência", "organização visual", "rotina"]
    },
    Estagio.MODERADO_LEVE: {
        "cognitivos": ["dificuldade de linguagem", "desorientação"],
        "comportamentais": ["apatia", "agitação leve"],
        "funcionais": ["dificuldade com higiene", "perda de marcha"],
        "intervencoes": ["validação", "musicoterapia", "terapia ocupacional"]
    },
    Estagio.MODERADO: {
        "cognitivos": ["não reconhece familiares", "perda de memória recente"],
        "comportamentais": ["sundowning", "alucinações", "delírios"],
        "funcionais": ["necessita ajuda para vestir", "incontinência"],
        "intervencoes": ["validação", "presença simulada", "ambiente calmo"]
    },
    Estagio.MODERADO_GRAVE: {
        "cognitivos": ["fala prejudicada", "não reconhece a si mesmo"],
        "comportamentais": ["agressividade", "gritos", "choro"],
        "funcionais": ["mobilidade reduzida", "risco de queda"],
        "intervencoes": ["conforto", "toque", "música familiar"]
    },
    Estagio.GRAVE: {
        "cognitivos": ["comunicação não verbal"],
        "comportamentais": ["apatia profunda"],
        "funcionais": ["acamado", "disfagia"],
        "intervencoes": ["cuidados paliativos", "conforto"]
    },
    Estagio.TERMINAL: {
        "cognitivos": ["sem resposta"],
        "comportamentais": ["silêncio"],
        "funcionais": ["falência múltipla"],
        "intervencoes": ["cuidados paliativos"]
    }
}


def adaptar_intervencao(estagio, sintoma):
    """Adapta a intervenção ao estágio e sintoma."""
    estagio_sintomas = SINTOMAS.get(estagio, {})
    
    for categoria in ["cognitivos", "comportamentais", "funcionais"]:
        if sintoma in estagio_sintomas.get(categoria, []):
            return estagio_sintomas.get("intervencoes", [])
    
    return []


def obter_sintomas(estagio):
    """Retorna todos os sintomas de um estágio."""
    return SINTOMAS.get(estagio, {})


if __name__ == "__main__":
    for estagio in Estagio:
        sintomas = SINTOMAS[estagio]
        print(f"\n[{estagio.name}]")
        print(f"  Cognitivos: {sintomas['cognitivos']}")
        print(f"  Comportamentais: {sintomas['comportamentais']}")
        print(f"  Funcionais: {sintomas['funcionais']}")
        print(f"  Intervenções: {sintomas['intervencoes']}")
