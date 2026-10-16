"""
Libero - Testes de Integração
Testa o fluxo completo: edge → cloud → agentes → ação.
"""

import sys
sys.path.insert(0, ".")

from cloud.agents.orchestrator import Orquestrador
from cloud.mcp_server import tools


def test_fluxo_completo_emergencia():
    """Testa fluxo de emergência."""
    orq = Orquestrador(
        "teste-1", {"nome": "Seu João", "camera_autorizada": True}
    )
    
    resultado = orq.processar(
        "Socorro, caí!",
        {"energia_max": 0.8, "duracao": 1},
        True
    )
    
    assert resultado["nivel"] == 3
    tipos = [a["tipo"] for a in resultado["acoes"]]
    assert "chamar_emergencia" in tipos
    assert "ativar_camera" in tipos


def test_fluxo_completo_memoria():
    """Testa fluxo de memória."""
    orq = Orquestrador("teste-2", {"nome": "Dona Maria"})
    
    resultado = orq.processar(
        "Quando eu era jovem, eu dançava com meu marido.",
        {"energia_media": 0.05},
        False
    )
    
    assert resultado.get("memoria") is not None
    assert resultado["memoria"]["confianca"] > 0.5


def test_mcp_listar_ferramentas():
    """Testa listagem de ferramentas MCP."""
    ferramentas = tools.listar_ferramentas()
    
    assert len(ferramentas) >= 10
    
    nomes = [f["name"] for f in ferramentas]
    assert "iniciar_conversa" in nomes
    assert "verificar_seguranca" in nomes
    assert "gravar_memoria" in nomes
    assert "notificar_familia" in nomes


def test_mcp_executar_conversa():
    """Testa execução de ferramenta MCP."""
    resultado = tools.executar("iniciar_conversa", {
        "idoso_id": "teste-3",
        "mensagem": "Preciso ir para casa",
        "contexto": {"nome": "Dona Maria"}
    })
    
    assert "resposta" in resultado
    assert len(resultado["resposta"]) > 0


def test_mcp_executar_protocolo_crise():
    """Testa obtenção de protocolo de crise."""
    resultado = tools.executar("obter_protocolo_crise", {"crise": "queda"})
    
    assert "protocolo" in resultado
    assert "acoes" in resultado["protocolo"]


def test_mcp_executar_sugerir_terapia():
    """Testa sugestão de terapia."""
    resultado = tools.executar("sugerir_terapia", {"sintoma": "sundowning"})
    
    assert resultado["terapia"] == "musicoterapia"


def test_mcp_executar_verificar_compliance():
    """Testa verificação de compliance."""
    resultado = tools.executar("verificar_compliance", {})
    
    assert "LGPD" in resultado
    assert "GDPR" in resultado
    assert "HIPAA" in resultado


def test_health_correlacao():
    """Testa correlação de sintomas."""
    from cloud.agents import health
    
    resultado = health.analisar("teste-4", {
        "confusao": True,
        "reducao_sono": True,
        "reducao_voz": True
    })
    
    assert resultado["alerta"] is True
    assert "infeccao" in resultado["causa"]


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
