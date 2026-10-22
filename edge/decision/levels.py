"""
Libero - Níveis de Decisão
Detecção contextual com tratamento de negação e ambiguidade.
"""

import re
import unicodedata
from enum import Enum
from datetime import datetime


class Nivel(Enum):
    OBSERVACAO = 0
    CONVERSA = 1
    INTERVENCAO = 2
    EMERGENCIA = 3


class Confianca(Enum):
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"


# ============================================================
# PALAVRAS DE EMERGÊNCIA (com peso)
# ============================================================

EMERGENCIA_PALAVRAS = {
    "socorro": 1.0,
    "me machuquei": 1.0,
    "nao consigo levantar": 1.0,
    "nao consigo respirar": 1.0,
    "nao sinto as pernas": 0.8,
    "nao sinto um lado do corpo": 0.8,
    "nao sinto o braco": 0.8,
    "quebrei": 0.9,
    "cai": 0.7,
    "caiu": 0.7,
    "caindo": 0.7,
    "caido": 0.7,
    "queda": 0.9,
    "desabei": 0.9,
    "tombou": 0.7,
    "sangue": 0.8,
    "dor": 0.5,
    "ajuda": 0.4,
}

# Contexto de passado
PASSADO = [
    "quando eu", "na minha epoca", "eu ja", "antigamente",
    "costumava", "aconteceu", "foi quando", "ha muito tempo"
]

# Terceiros
TERCEIROS = [
    "meu filho", "minha filha", "meu neto", "minha neta",
    "meu vizinho", "minha vizinha", "o vizinho", "a vizinha",
    "ele", "ela"
]


def _match_palavra(texto, palavras):
    """Match por palavra inteira (não substring)."""
    if not texto:
        return False
    # Criar regex que exige palavra inteira
    for p in palavras:
        padrao = r'\b' + re.escape(p) + r'\b'
        if re.search(padrao, texto, re.IGNORECASE):
            return True
    return False


def _remover_acentos(texto):
    """Remove acentos para normalização."""
    if not texto:
        return ""
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _normalizar(texto):
    """Normaliza texto: minúsculas, sem acentos, sem pontuação excessiva."""
    if not texto:
        return ""
    texto = texto.lower().strip()
    texto = _remover_acentos(texto)
    texto = re.sub(r'[!?]{2,}', '!', texto)
    return texto


def _fragmentos(texto_norm):
    """Divide contrastes para uma negação ou passado não apagar outro fato."""
    return [
        parte.strip()
        for parte in re.split(r"[;.!?]+|\b(?:mas|por[eé]m|agora|hoje)\b", texto_norm)
        if parte.strip()
    ]


def _ocorrencias(fragmento, termo):
    padrao = re.escape(termo).replace(r"\ ", r"\s+")
    return list(re.finditer(rf"(?<!\w){padrao}(?!\w)", fragmento))


def _negacao_aplica(fragmento, termo, ocorrencia):
    # Expressões como "não consigo levantar" descrevem incapacidade, não negação.
    if termo.startswith("nao "):
        return False
    trecho = re.split(r"[,;.!?]+|\b(?:mas|por[eé]m|agora|hoje)\b", fragmento[:ocorrencia.start()])[-1]
    anteriores = trecho.split()
    return any(
        palavra in {"nao", "nunca", "jamais", "sem", "nem"}
        for palavra in anteriores[-3:]
    )


def _tem_contexto_passado(texto_norm):
    return any(re.search(rf"(?<!\w){re.escape(p)}(?!\w)", texto_norm) for p in PASSADO)


def _tem_terceiros(texto_norm):
    return any(re.search(rf"(?<!\w){re.escape(t)}(?!\w)", texto_norm) for t in TERCEIROS)


def _ocorrencia_de_terceiro(fragmento, ocorrencia):
    palavras = fragmento.split()
    indice = len(fragmento[:ocorrencia.start()].split())
    inicio = max(0, indice - 3)
    fim = min(len(palavras), indice + 4)
    contexto_proximo = " ".join(palavras[inicio:fim])
    return any(
        re.search(rf"(?<!\w){re.escape(marcador)}(?!\w)", contexto_proximo)
        for marcador in TERCEIROS
    )


def detectar_emergencia_contextual(texto):
    """
    Detecta emergência com análise contextual.
    
    Retorna dict com nivel, confianca, evidencias, razao.
    """
    texto_norm = _normalizar(texto)
    
    if not texto_norm:
        return {
            "nivel": Nivel.OBSERVACAO,
            "confianca": Confianca.BAIXA,
            "evidencias": [],
            "razao": "Texto vazio"
        }
    
    evidencias = []
    score_total = 0.0
    
    for fragmento in _fragmentos(texto_norm):
        passado = _tem_contexto_passado(fragmento)
        for palavra, peso in EMERGENCIA_PALAVRAS.items():
            palavra_norm = _remover_acentos(palavra)
            for ocorrencia in _ocorrencias(fragmento, palavra_norm):
                if _negacao_aplica(fragmento, palavra_norm, ocorrencia):
                    evidencias.append({
                        "palavra": palavra, "peso": 0.0, "negada": True,
                        "razao": "Negação próxima no mesmo trecho",
                    })
                    continue

                terceiro = _ocorrencia_de_terceiro(fragmento, ocorrencia)
                sinal_pessoal_atual = palavra_norm in {
                    "nao consigo levantar", "me machuquei",
                }
                fator = (
                    0.2 if passado and not sinal_pessoal_atual
                    else 0.2 if terceiro and not sinal_pessoal_atual
                    else 1.0
                )
                peso_ajustado = peso * fator
                razao = (
                    "Contexto de passado" if passado
                    else "Contexto de terceiros" if terceiro
                    else "Sinal textual"
                )
                evidencias.append({
                    "palavra": palavra, "peso": peso_ajustado,
                    "negada": False, "razao": razao,
                })
                score_total += peso_ajustado
    
    # Decisão
    if score_total >= 0.9:
        return {
            "nivel": Nivel.EMERGENCIA,
            "confianca": Confianca.ALTA,
            "evidencias": evidencias,
            "score_sinais": score_total,
            "score_nao_calibrado": True,
            "razao": f"Score: {score_total:.2f}"
        }
    elif score_total >= 0.5:
        return {
            "nivel": Nivel.EMERGENCIA,
            "confianca": Confianca.MEDIA,
            "evidencias": evidencias,
            "score_sinais": score_total,
            "score_nao_calibrado": True,
            "razao": f"Possível emergência. Score: {score_total:.2f}"
        }
    elif score_total > 0:
        return {
            "nivel": Nivel.INTERVENCAO,
            "confianca": Confianca.BAIXA,
            "evidencias": evidencias,
            "score_sinais": score_total,
            "score_nao_calibrado": True,
            "razao": f"Sinais fracos. Score: {score_total:.2f}"
        }
    
    return {
        "nivel": Nivel.OBSERVACAO,
        "confianca": Confianca.BAIXA,
        "evidencias": [],
        "score_sinais": 0.0,
        "score_nao_calibrado": True,
        "razao": "Nenhum sinal de emergência"
    }


# ============================================================
# CONFUSÃO / FUGA / SOLIDÃO
# ============================================================

PALAVRAS_CONFUSAO = [
    "onde estou", "quem e voce", "cade", "preciso ir",
    "quero ir", "me leva", "nao sei onde"
]

PALAVRAS_SOLIDAO = ["sozinho", "sozinha", "ninguem", "triste", "chorar"]
SAUDACOES = [
    "hi", "hello", "hey", "good morning", "good afternoon", "good evening",
    "how are you", "oi", "ola", "bom dia", "boa tarde", "boa noite",
]


def decidir_nivel(texto, hora=None, movimento=False):
    """Decide o nível de intervenção baseado em contexto."""
    if hora is None:
        hora = datetime.now().hour
    
    # Emergência contextual
    emergencia = detectar_emergencia_contextual(texto)
    if emergencia["nivel"] == Nivel.EMERGENCIA:
        return emergencia["nivel"]

    texto_norm = _normalizar(texto)
    if _match_palavra(texto_norm, SAUDACOES):
        return Nivel.CONVERSA
    ajuda = _match_palavra(texto_norm, ["ajuda", "me ajuda", "me ajudem"])
    if ajuda:
        if re.search(r"\bme\s+ajuda\s*!+", texto_norm):
            return Nivel.EMERGENCIA
        return Nivel.INTERVENCAO

    # Confusão
    if _match_palavra(texto_norm, PALAVRAS_CONFUSAO):
        return Nivel.INTERVENCAO
    
    # Madrugada + movimento
    if 2 <= hora <= 5 and movimento:
        return Nivel.INTERVENCAO
    
    # Solidão
    if _match_palavra(texto_norm, PALAVRAS_SOLIDAO):
        return Nivel.CONVERSA
    
    # Conversa normal
    if texto_norm and len(texto_norm) > 10:
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


# ============================================================
# TESTE
# ============================================================

if __name__ == "__main__":
    testes = [
        ("Socorro, caí!", "EMERGENCIA"),
        ("Me machuquei", "EMERGENCIA"),
        ("Não consigo levantar", "EMERGENCIA"),
        ("Não estou sentindo dor", "OBSERVACAO"),
        ("Não caí, estou bem", "OBSERVACAO"),
        ("Quando eu era jovem, eu caí muito de bicicleta", "CONVERSA"),
        ("Meu filho caiu ontem", "CONVERSA"),
        ("Onde estou? Preciso ir para casa", "INTERVENCAO"),
        ("Estou sozinha", "CONVERSA"),
        ("Bom dia, como você está?", "CONVERSA"),
        ("Oi", "CONVERSA"),
        ("Hello", "CONVERSA"),
    ]
    
    print("=== Teste de Decisão Contextual ===\n")
    acertos = 0
    for texto, esperado in testes:
        nivel = decidir_nivel(texto)
        ok = nivel.name == esperado
        acertos += 1 if ok else 0
        status = "✓" if ok else "✗"
        print(f"{status} '{texto}'")
        print(f"  Esperado: {esperado} | Obtido: {nivel.name}")
    
    print(f"\n{acertos}/{len(testes)} corretos")
