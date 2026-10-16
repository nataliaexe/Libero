from cloud.agents.identity import Papel, identificar_por_canal, pode_fazer


def test_identificar_por_canal():
    assert identificar_por_canal("voz") is Papel.IDOSO
    assert identificar_por_canal("dashboard") is Papel.CUIDADOR
    assert identificar_por_canal("outro") is Papel.VISITANTE


def test_acoes_permitidas_por_papel():
    assert pode_fazer(Papel.IDOSO, "pedir_ajuda")
    assert pode_fazer(Papel.CUIDADOR, "criar_task")
    assert pode_fazer(Papel.MEDICO, "sugerir_terapia")
    assert not pode_fazer(Papel.VISITANTE, "criar_task")
    assert not pode_fazer("desconhecido", "conversar")
