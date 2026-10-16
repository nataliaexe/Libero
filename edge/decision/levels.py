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
    "nao sinto": 0.8,
    "quebrei": 0.9,
    "cai": 0.7,
    "sangue": 0.8,
    "dor": 0.5,
    "ajuda": 0.4,
}

# Negação (cancela emergência)
NEGACOES = [
    "nao", "nunca", "jamais", "sem",
    "nem", "tampouco", "nenhum", "nenhuma",
    "nao estou", "nao tenho", "nao sinto"
]

# Contexto de passado
PASSADO = [
    "quando eu", "na minha epoca", "eu ja", "antigamente",
    "costumava", "aconteceu", "foi quando", "ha muito tempo"
]

# Terceiros
TERCEIROS = [
    "meu filho", "minha filha", "meu neto", "minha neta",
    "ele", "ela", "o vizinho", "a vizinha"
]


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


def _tem_negacao_proxima(texto_norm, palavra_norm, janela=7):
    """
    Verifica se há negação próxima à palavra.
    
    Janela ampliada para 7 palavras (era 5).
    """
    palavras = texto_norm.split()
    try:
        idx = palavras.index(palavra_norm)
    except ValueError:
        # Tentar encontrar em frases de múltiplas palavras
        for i, w in enumerate(palavras):
            if palavra_norm.split()[0] in w:
                idx = i
                break
        else:
            return False
    
    inicio = max(0, idx - janela)
    contexto = " ".join(palavras[inicio:idx])
    
    # Verificar negações simples
    for neg in NEGACOES:
        if neg in contexto.split() or neg in contexto:
            return True
    
    # Verificar negação direta antes (palavra anterior)
    if idx > 0:
        palavra_anterior = palavras[idx - 1]
        if palavra_anterior in ["nao", "nunca", "jamais", "sem", "nem"]:
            return True
    
    return False


def _tem_contexto_passado(texto_norm):
    return any(p in texto_norm for p in PASSADO)


def _tem_terceiros(texto_norm):
    return any(t in texto_norm for t in TERCEIROS)


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
    
    # Contexto global
    passado = _tem_contexto_passado(texto_norm)
    terceiros = _tem_terceiros(texto_norm)
    
    evidencias = []
    score_total = 0.0
    
    # Analisar cada palavra-chave
    for palavra, peso in EMERGENCIA_PALAVRAS.items():
        palavra_norm = _remover_acentos(palavra)
        
        if palavra_norm not in texto_norm:
            continue
        
        # 1. Verificar negação (cancela)
        if _tem_negacao_proxima(texto_norm, palavra_norm):
            evidencias.append({
                "palavra": palavra,
                "peso": 0.0,
                "negada": True,
                "razao": "Negação detectada"
            })
            continue
        
        # 2. Contexto de passado (reduz)
        if passado:
            peso_ajustado = peso * 0.2
            evidencias.append({
                "palavra": palavra,
                "peso": peso_ajustado,
                "negada": False,
                "razao": "Contexto de passado"
            })
            score_total += peso_ajustado
            continue
        
        # 3. Terceiros (reduz)
        if terceiros:
            peso_ajustado = peso * 0.3
            evidencias.append({
                "palavra": palavra,
                "peso": peso_ajustado,
                "negada": False,
                "razao": "Contexto de terceiros"
            })
            score_total += peso_ajustado
            continue
        
        # 4. Emergência direta
        evidencias.append({
            "palavra": palavra,
            "peso": peso,
            "negada": False,
            "razao": "Emergência direta"
        })
        score_total += peso
    
    # Decisão
    if score_total >= 0.9:
        return {
            "nivel": Nivel.EMERGENCIA,
            "confianca": Confianca.ALTA,
            "evidencias": evidencias,
            "razao": f"Score: {score_total:.2f}"
        }
    elif score_total >= 0.5:
        return {
            "nivel": Nivel.EMERGENCIA,
            "confianca": Confianca.MEDIA,
            "evidencias": evidencias,
            "razao": f"Possível emergência. Score: {score_total:.2f}"
        }
    elif score_total > 0:
        return {
            "nivel": Nivel.INTERVENCAO,
            "confianca": Confianca.BAIXA,
            "evidencias": evidencias,
            "razao": f"Sinais fracos. Score: {score_total:.2f}"
        }
    
    return {
        "nivel": Nivel.OBSERVACAO,
        "confianca": Confianca.BAIXA,
        "evidencias": [],
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


def decidir_nivel(texto, hora=None, movimento=False):
    """Decide o nível de intervenção baseado em contexto."""
    if hora is None:
        hora = datetime.now().hour
    
    # Emergência contextual
    emergencia = detectar_emergencia_contextual(texto)
    if emergencia["nivel"] == Nivel.EMERGENCIA:
        return emergencia["nivel"]
    
    texto_norm = _normalizar(texto)
    
    # Confusão
    if any(p in texto_norm for p in PALAVRAS_CONFUSAO):
        return Nivel.INTERVENCAO
    
    # Madrugada + movimento
    if 2 <= hora <= 5 and movimento:
        return Nivel.INTERVENCAO
    
    # Solidão
    if any(p in texto_norm for p in PALAVRAS_SOLIDAO):
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
        ("Oi", "OBSERVACAO"),
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
