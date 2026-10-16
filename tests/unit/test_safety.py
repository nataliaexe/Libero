"""
Libero - Testes do Agente de Segurança
Atualizado para a nova API multimodal.
"""

import sys
sys.path.insert(0, ".")

from cloud.agents import safety


# ============================================================
# QUEDA MULTIMODAL
# ============================================================

def test_queda_multimodal_confirma():
    """Áudio + visão + movimento confirma queda."""
    resultado = safety.detectar_queda_multimodal(
        features_audio={"energia_max": 0.8, "duracao": 1},
        features_visao={"angulo_corpo": 80, "velocidade_queda": 0.8},
        movimento=True
    )
    assert resultado["detectado"] is True
    assert resultado["confianca"] >= 0.8


def test_queda_so_audio_nao_confirma():
    """Só áudio NÃO confirma queda (confiança < 0.5)."""
    resultado = safety.detectar_queda_multimodal(
        features_audio={"energia_max": 0.8, "duracao": 1}
    )
    assert resultado["confianca"] < 0.5


def test_objeto_caindo_nao_e_queda():
    """Som alto sem visão NÃO é queda."""
    resultado = safety.detectar_queda_multimodal(
        features_audio={"energia_max": 0.9, "duracao": 0.5},
        features_visao={"angulo_corpo": 0, "velocidade_queda": 0}
    )
    assert resultado["detectado"] is False


# ============================================================
# API ANTIGA (compatibilidade)
# ============================================================

def test_detectar_queda_audio_limitado():
    """API antiga limita confiança a 0.3 (áudio sozinho)."""
    features = {"energia_max": 0.8, "duracao": 1}
    resultado = safety.detectar_queda(features)
    assert resultado["detectado"] is True
    assert resultado["confianca"] <= 0.3


def test_nao_detectar_queda_audio_baixo():
    """Áudio com energia baixa não é queda."""
    features = {"energia_max": 0.1, "duracao": 5}
    resultado = safety.detectar_queda(features)
    assert resultado["detectado"] is False


# ============================================================
# FUGA
# ============================================================

def test_intencao_verbal_nao_e_fuga():
    """'Vou sair' sozinho NÃO é fuga."""
    resultado = safety.detectar_fuga("Vou sair", 10, False)
    assert resultado["detectado"] is False


def test_porta_aberta_e_fuga():
    """'Vou sair' + porta aberta É fuga."""
    resultado = safety.detectar_fuga("Vou sair", 10, True, {"porta_aberta": True})
    assert resultado["detectado"] is True


def test_fuga_noturna():
    """Madrugada + movimento + direção porta = fuga noturna."""
    resultado = safety.detectar_fuga("", 3, True, {"direcao_porta": True})
    assert resultado["detectado"] is True


def test_nao_detectar_fuga():
    """Bom dia, sem comportamento suspeito, não é fuga."""
    resultado = safety.detectar_fuga("Bom dia", 10, False)
    assert resultado["detectado"] is False


# ============================================================
# AGITAÇÃO
# ============================================================

def test_detectar_agitacao():
    features = {"energia_media": 0.15, "zcr": 0.2}
    texto = "Cadê minha casa? Preciso ir para casa."
    resultado = safety.detectar_agitacao(features, texto)
    assert resultado["detectado"] is True
    assert resultado["tipo"] == "agitacao"


def test_nao_detectar_agitacao():
    features = {"energia_media": 0.01, "zcr": 0.05}
    resultado = safety.detectar_agitacao(features, "Bom dia")
    assert resultado["detectado"] is False


# ============================================================
# ESCALONAMENTO
# ============================================================

def test_agir_nivel_2():
    evento = {"detectado": True, "confianca": 0.6, "tipo": "agitacao"}
    resultado = safety.agir(evento, {"nome": "Test"})
    assert resultado["nivel"] == 2
    assert len(resultado["acoes"]) >= 2


def test_agir_nivel_3_alto():
    evento = {"detectado": True, "confianca": 0.95, "tipo": "queda"}
    resultado = safety.agir(evento, {"nome": "Test", "camera_autorizada": False})
    assert resultado["nivel"] == 3
    tipos = [a["tipo"] for a in resultado["acoes"]]
    assert "chamar_emergencia" in tipos


def test_nao_chama_samu_confianca_media():
    """Confiança 0.7 NÃO chama SAMU."""
    evento = {"detectado": True, "confianca": 0.7, "tipo": "queda"}
    resultado = safety.agir(evento, {"nome": "Test"})
    tipos = [a["tipo"] for a in resultado["acoes"]]
    assert "chamar_emergencia" not in tipos


def test_agir_sem_evento():
    evento = {"detectado": False, "confianca": 0.0, "tipo": None}
    resultado = safety.agir(evento, {})
    assert resultado["nivel"] == 0
