"""
Libero - Terapias Baseadas em Evidência
"""

from enum import Enum


class Terapia(Enum):
    VALIDACAO = "validacao"
    REMINISCENCIA = "reminiscencia"
    MUSICOTERAPIA = "musicoterapia"
    PRESENCA_SIMULADA = "presenca_simulada"
    ESTIMULACAO_COGNITIVA = "estimulacao_cognitiva"
    TERAPIA_OCUPACIONAL = "terapia_ocupacional"
    CBT_CUIDADOR = "cbt_cuidador"
    TERAPIA_SISTEMICA = "terapia_sistemica"
    LUTO_ANTECIPADO = "luto_antecipado"


PROTOCOLOS = {
    Terapia.VALIDACAO: {
        "descricao": "Validar a emoção, não a realidade.",
        "principios": [
            "Nunca corrija o idoso",
            "Reconheça a emoção por trás da fala",
            "Use perguntas abertas",
            "Não dê conselhos não solicitados",
        ],
        "exemplos": [
            ("Preciso ir para casa", "Me fala da sua casa. Como ela é?"),
            ("Cadê minha mãe?", "Sua mãe deve ter sido incrível. Me conta sobre ela."),
            ("Preciso ir trabalhar", "Você trabalhou por muitos anos. Me conta sobre isso."),
        ]
    },
    Terapia.REMINISCENCIA: {
        "descricao": "Usar memórias antigas para acalmar.",
        "principios": [
            "Memórias antigas são preservadas",
            "Fotos, músicas, objetos ajudam",
            "Sessões curtas (15-30 min)",
            "Não force a lembrança",
        ],
        "exemplos": [
            ("Quando eu era jovem", "Me conta mais. O que você fazia?"),
            ("Eu dançava com meu marido", "Que lindo. Qual era a música?"),
        ]
    },
    Terapia.MUSICOTERAPIA: {
        "descricao": "Música como âncora emocional.",
        "principios": [
            "Música da juventude (15-25 anos)",
            "Música calma para agitação",
            "Música alegre para apatia",
            "Cantar junto ajuda",
        ],
        "exemplos": [
            ("Agitação", "Tocar música calma da juventude"),
            ("Apatia", "Tocar música alegre e dançar"),
        ]
    },
    Terapia.PRESENCA_SIMULADA: {
        "descricao": "Vídeos/áudios de entes queridos.",
        "principios": [
            "Usar com consentimento",
            "Nunca enganar",
            "Vozes familiares acalmam",
            "Fotos e vídeos ajudam",
        ],
        "exemplos": [
            ("Agitação noturna", "Tocar voz da filha dizendo 'está tudo bem'"),
            ("Saudade", "Mostrar fotos da família"),
        ]
    },
    Terapia.ESTIMULACAO_COGNITIVA: {
        "descricao": "Exercícios que retardam o declínio.",
        "principios": [
            "Desafio leve, não estresse",
            "Variedade de atividades",
            "Sessões curtas",
            "Celebrar sucessos",
        ],
        "exemplos": [
            ("Memória", "Jogo de memória com fotos da família"),
            ("Linguagem", "Nomear objetos da casa"),
        ]
    },
    Terapia.TERAPIA_OCUPACIONAL: {
        "descricao": "Manter autonomia e rotina.",
        "principios": [
            "Adaptar tarefas à capacidade",
            "Manter rotina",
            "Preservar dignidade",
            "Celebrar pequenas conquistas",
        ],
        "exemplos": [
            ("Vestir-se", "Vamos vestir juntos? Eu te ajudo."),
            ("Cozinhar", "Você quer me ajudar a preparar o café?"),
        ]
    },
    Terapia.CBT_CUIDADOR: {
        "descricao": "Terapia cognitivo-comportamental para o cuidador.",
        "principios": [
            "Identificar pensamentos negativos",
            "Reestruturar crenças",
            "Reduzir culpa",
            "Aumentar autocuidado",
        ],
        "exemplos": [
            ("Eu não sou boa filha", "Você tem cuidado 24/7. Isso é amor."),
            ("Eu deveria fazer mais", "Você está fazendo o possível. E é muito."),
        ]
    },
    Terapia.TERAPIA_SISTEMICA: {
        "descricao": "Terapia para a família como um todo.",
        "principios": [
            "A família é um sistema",
            "Cada membro tem necessidades",
            "Conflitos precisam ser mediados",
            "Todos adoecem juntos",
        ],
        "exemplos": [
            ("Conflito entre irmãos", "Vamos conversar sobre o que cada um pode fazer."),
            ("Culpa", "Ninguém está sozinho nisso."),
        ]
    },
    Terapia.LUTO_ANTECIPADO: {
        "descricao": "Preparar a família para a perda gradual.",
        "principios": [
            "A perda acontece em etapas",
            "Cada etapa tem um luto",
            "Não é fraqueza sentir",
            "Apoio profissional ajuda",
        ],
        "exemplos": [
            ("Ele não me reconhece mais", "Isso é doloroso. Você não está sozinha."),
            ("Sinto falta de quem ele era", "Você está de luto. É normal."),
        ]
    },
}


def obter_protocolo(terapia):
    """Retorna o protocolo de uma terapia."""
    return PROTOCOLOS.get(terapia)


def sugerir_terapia(sintoma, estagio=None):
    """Sugere terapia baseada no sintoma."""
    mapa = {
        "agitacao": Terapia.VALIDACAO,
        "sundowning": Terapia.MUSICOTERAPIA,
        "confusao": Terapia.VALIDACAO,
        "saudade": Terapia.REMINISCENCIA,
        "apatia": Terapia.MUSICOTERAPIA,
        "agressividade": Terapia.VALIDACAO,
        "alucinacao": Terapia.VALIDACAO,
        "delirio": Terapia.VALIDACAO,
        "culpa_cuidador": Terapia.CBT_CUIDADOR,
        "conflito_familia": Terapia.TERAPIA_SISTEMICA,
        "luto": Terapia.LUTO_ANTECIPADO,
        "perda_autonomia": Terapia.TERAPIA_OCUPACIONAL,
    }
    
    return mapa.get(sintoma, Terapia.VALIDACAO)


if __name__ == "__main__":
    print("=== Protocolos de Terapia ===\n")
    for terapia in Terapia:
        protocolo = PROTOCOLOS[terapia]
        print(f"[{terapia.name}]")
        print(f"  {protocolo['descricao']}")
        print(f"  Princípios: {len(protocolo['principios'])}")
        print()
    
    print("=== Sugestões por Sintoma ===\n")
    sintomas = ["agitacao", "sundowning", "saudade", "culpa_cuidador", "perda_autonomia"]
    for sintoma in sintomas:
        terapia = sugerir_terapia(sintoma)
        print(f"  {sintoma} → {terapia.name}")
