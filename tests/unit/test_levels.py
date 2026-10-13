"""
Libero - Testes dos níveis de decisão
"""

import sys
sys.path.insert(0, ".")

from edge.decision.levels import decidir_nivel, Nivel


def test_emergencia():
    assert decidir_nivel("Socorro, caí!", 3, True) == Nivel.EMERGENCIA
    assert decidir_nivel("Estou com dor", 10, False) == Nivel.EMERGENCIA


def test_intervencao():
    assert decidir_nivel("Preciso ir para casa", 15, False) == Nivel.INTERVENCAO
    assert decidir_nivel("Cadê minha mãe?", 14, False) == Nivel.INTERVENCAO


def test_conversa():
    assert decidir_nivel("Estou sozinha", 14, False) == Nivel.CONVERSA
    assert decidir_nivel("Bom dia, como você está?", 8, False) == Nivel.CONVERSA


def test_observacao():
    assert decidir_nivel("", 12, False) == Nivel.OBSERVACAO
    assert decidir_nivel("Oi", 12, False) == Nivel.OBSERVACAO


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
