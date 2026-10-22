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
    assert decidir_nivel("Oi", 12, False) == Nivel.CONVERSA
    assert decidir_nivel("Hello", 12, False) == Nivel.CONVERSA


def test_pedido_de_ajuda_escalona_proporcionalmente():
    assert decidir_nivel("Me ajuda", 12, False) == Nivel.INTERVENCAO
    assert decidir_nivel("Ajuda!", 12, False) == Nivel.INTERVENCAO
    assert decidir_nivel("Me ajuda!", 12, False) == Nivel.EMERGENCIA
    assert decidir_nivel("Socorro, minha filha, me ajuda!", 12, False) == Nivel.EMERGENCIA
    assert decidir_nivel("Eu já caí e não consigo levantar", 12, False) in {
        Nivel.INTERVENCAO, Nivel.EMERGENCIA,
    }
    assert decidir_nivel("Me machuquei, ele não me ajudou", 12, False) in {
        Nivel.INTERVENCAO, Nivel.EMERGENCIA,
    }


def test_match_de_confusao_exige_palavra_inteira():
    assert decidir_nivel("cadeira", 12, False) == Nivel.OBSERVACAO
    assert decidir_nivel("cadê", 12, False) == Nivel.INTERVENCAO
    assert decidir_nivel("quero ir", 12, False) == Nivel.INTERVENCAO
    assert decidir_nivel("quero ir ao banheiro", 12, False) == Nivel.INTERVENCAO


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
