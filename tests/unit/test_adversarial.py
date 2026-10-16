"""
Libero - Testes Adversariais
Casos que devem ser tratados corretamente.
"""

import sys
sys.path.insert(0, ".")

from edge.decision.levels import decidir_nivel, Nivel, detectar_emergencia_contextual
from cloud.agents import safety


# ============================================================
# NEGAÇÃO
# ============================================================

def test_negacao_dor():
    """'Não estou sentindo dor' NÃO é emergência."""
    resultado = detectar_emergencia_contextual("Não estou sentindo dor")
    assert resultado["nivel"] != Nivel.EMERGENCIA


def test_negacao_queda():
    """'Não caí' NÃO é emergência."""
    resultado = detectar_emergencia_contextual("Não caí, estou bem")
    assert resultado["nivel"] != Nivel.EMERGENCIA


def test_negacao_ajuda():
    """'Não preciso de ajuda' NÃO é emergência."""
    resultado = detectar_emergencia_contextual("Não preciso de ajuda")
    assert resultado["nivel"] != Nivel.EMERGENCIA


# ============================================================
# CONTEXTO DE PASSADO
# ============================================================

def test_passado_queda():
    """'Quando eu era jovem, eu caí' NÃO é emergência."""
    resultado = detectar_emergencia_contextual("Quando eu era jovem, eu caí de bicicleta")
    assert resultado["nivel"] != Nivel.EMERGENCIA


def test_passado_dor():
    """'Eu já senti muita dor' NÃO é emergência."""
    resultado = detectar_emergencia_contextual("Antigamente eu sentia muita dor nas costas")
    assert resultado["nivel"] != Nivel.EMERGENCIA


# ============================================================
# TERCEIROS
# ============================================================

def test_terceiro_queda():
    """'Meu filho caiu' NÃO é emergência DO IDOSO."""
    resultado = detectar_emergencia_contextual("Meu filho caiu ontem")
    assert resultado["nivel"] != Nivel.EMERGENCIA


# ============================================================
# EMERGÊNCIA REAL
# ============================================================

def test_emergencia_real():
    """'Socorro, caí!' É emergência."""
    resultado = detectar_emergencia_contextual("Socorro, caí!")
    assert resultado["nivel"] == Nivel.EMERGENCIA


def test_emergencia_machucado():
    """'Me machuquei' É emergência."""
    resultado = detectar_emergencia_contextual("Me machuquei, não consigo levantar")
    assert resultado["nivel"] == Nivel.EMERGENCIA


# ============================================================
# QUEDA MULTIMODAL
# ============================================================

def test_queda_so_audio_nao_confirma():
    """Só áudio NÃO confirma queda."""
    resultado = safety.detectar_queda_multimodal(
        features_audio={"energia_max": 0.8, "duracao": 1}
    )
    assert resultado["confianca"] < 0.8  # Não deve ser alta


def test_queda_multimodal_confirma():
    """Áudio + visão + movimento CONFIRMA queda."""
    resultado = safety.detectar_queda_multimodal(
        features_audio={"energia_max": 0.8, "duracao": 1},
        features_visao={"angulo_corpo": 80, "velocidade_queda": 0.8},
        movimento=True
    )
    assert resultado["detectado"] is True
    assert resultado["confianca"] >= 0.8


def test_objeto_caindo_nao_e_queda():
    """Objeto caindo (sem visão de corpo) NÃO é queda."""
    resultado = safety.detectar_queda_multimodal(
        features_audio={"energia_max": 0.9, "duracao": 0.5},
        features_visao={"angulo_corpo": 0, "velocidade_queda": 0}
    )
    assert resultado["detectado"] is False


# ============================================================
# FUGA (INTENÇÃO ≠ COMPORTAMENTO)
# ============================================================

def test_intencao_verbal_nao_e_fuga():
    """'Vou sair' sozinho NÃO é fuga."""
    resultado = safety.detectar_fuga("Vou sair", 10, False)
    assert resultado["detectado"] is False


def test_porta_aberta_e_fuga():
    """'Vou sair' + porta aberta É fuga."""
    resultado = safety.detectar_fuga("Vou sair", 10, True, {"porta_aberta": True})
    assert resultado["detectado"] is True


def test_madrugada_movimento_e_fuga():
    """Madrugada + movimento É fuga noturna."""
    resultado = safety.detectar_fuga("", 3, True, {"direcao_porta": True})
    assert resultado["detectado"] is True


# ============================================================
# ESCALONAMENTO
# ============================================================

def test_nao_chama_samu_sem_certeza():
    """Não chama SAMU com confiança < 0.9."""
    evento = {"detectado": True, "confianca": 0.6, "tipo": "queda"}
    resultado = safety.agir(evento, {"nome": "Test"})
    tipos = [a["tipo"] for a in resultado["acoes"]]
    assert "chamar_emergencia" not in tipos


def test_chama_samu_com_certeza():
    """Chama SAMU com confiança >= 0.9."""
    evento = {"detectado": True, "confianca": 0.95, "tipo": "queda"}
    resultado = safety.agir(evento, {"nome": "Test", "camera_autorizada": False})
    tipos = [a["tipo"] for a in resultado["acoes"]]
    assert "chamar_emergencia" in tipos


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
