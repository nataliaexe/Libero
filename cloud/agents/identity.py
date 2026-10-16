"""
Libero - Agente de Identidade
Distingue idoso, cuidador e visitante.
"""

from enum import Enum


class Papel(Enum):
    IDOSO = "idoso"           # Pode conversar, não cria tasks
    CUIDADOR = "cuidador"     # Pode criar tasks, ver tudo
    MEDICO = "medico"         # Só vê saúde
    VISITANTE = "visitante"   # Só conversa


# Ações permitidas por papel
ACOES_PERMITIDAS = {
    Papel.IDOSO: [
        "conversar", "pedir_musica", "pedir_agua", "pedir_ajuda"
    ],
    Papel.CUIDADOR: [
        "conversar", "criar_task", "editar_task", "remover_task",
        "ver_camera", "ver_historico", "configurar", "notificar_familia"
    ],
    Papel.MEDICO: [
        "ver_saude", "ver_historico_clinico", "sugerir_terapia"
    ],
    Papel.VISITANTE: [
        "conversar"
    ]
}


def pode_fazer(papel, acao):
    """Verifica se um papel pode fazer uma ação."""
    return acao in ACOES_PERMITIDAS.get(papel, [])


def identificar_por_canal(canal):
    """Identifica o papel pelo canal de interação, sem biometria de voz."""
    if canal == "voz":
        return Papel.IDOSO
    if canal == "dashboard":
        return Papel.CUIDADOR
    return Papel.VISITANTE
