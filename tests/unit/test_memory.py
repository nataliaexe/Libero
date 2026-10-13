"""
Libero - Testes do Agente de Memória
"""

import sys
sys.path.insert(0, ".")

from cloud.agents import memory


def test_detectar_historia_curta():
    resultado = memory.detectar_historia("Bom dia")
    assert resultado["detectado"] is False


def test_detectar_historia_longa():
    texto = "Quando eu era jovem, eu dançava toda sexta com meu marido no clube da cidade."
    resultado = memory.detectar_historia(texto)
    assert resultado["detectado"] is True
    assert resultado["confianca"] > 0.4


def test_detectar_historia_marcadores():
    texto = "Meu pai me ensinou a trabalhar. Ele era muito bom."
    resultado = memory.detectar_historia(texto)
    assert resultado["detectado"] is True


def test_nao_detectar_historia():
    texto = "Oi, tudo bem?"
    resultado = memory.detectar_historia(texto)
    assert resultado["detectado"] is False
