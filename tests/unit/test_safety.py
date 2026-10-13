"""
Libero - Testes do Agente de Segurança
"""

import sys
sys.path.insert(0, ".")

from cloud.agents import safety


def test_detectar_queda():
    features = {"energia_max": 0.8, "duracao": 1}
    resultado = safety.detectar_queda(features)
    assert resultado["detectado"] is True
    assert resultado["tipo"] == "queda"
    assert resultado["confianca"] >= 0.8


def test_nao_detectar_queda():
    features = {"energia_max": 0.1, "duracao": 5}
    resultado = safety.detectar_queda(features)
    assert resultado["detectado"] is False


def test_detectar_fuga():
    resultado = safety.detectar_fuga("Preciso ir trabalhar", 10, True)
    assert resultado["detectado"] is True
    assert resultado["tipo"] == "fuga"


def test_detectar_fuga_noturna():
    resultado = safety.detectar_fuga("", 3, True)
    assert resultado["detectado"] is True
    assert resultado["tipo"] == "fuga_noturna"


def test_nao_detectar_fuga():
    resultado = safety.detectar_fuga("Bom dia", 10, False)
    assert resultado["detectado"] is False


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


def test_agir_nivel_2():
    evento = {"detectado": True, "confianca": 0.6, "tipo": "agitacao"}
    contexto = {"nome": "Dona Maria"}
    resultado = safety.agir(evento, contexto)
    assert resultado["nivel"] == 2
    assert len(resultado["acoes"]) >= 2


def test_agir_nivel_3():
    evento = {"detectado": True, "confianca": 0.9, "tipo": "queda"}
    contexto = {"nome": "Seu João"}
    resultado = safety.agir(evento, contexto)
    assert resultado["nivel"] == 3
    tipos = [a["tipo"] for a in resultado["acoes"]]
    assert "ativar_camera" in tipos
    assert "chamar_emergencia" in tipos


def test_agir_sem_evento():
    evento = {"detectado": False, "confianca": 0.0, "tipo": None}
    resultado = safety.agir(evento, {})
    assert resultado["nivel"] == 0
    assert len(resultado["acoes"]) == 0
