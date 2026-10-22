"""
Libero - Controle de Áudio
Permite ligar/desligar o listener remotamente.
"""

import threading

# Estado global do listener (injetado pelo main.py)
_listener = None
_lock = threading.Lock()


def registrar_listener(listener):
    """Registra o listener para controle remoto."""
    global _listener
    with _lock:
        _listener = listener


def get_listener():
    """Retorna o listener atual."""
    with _lock:
        return _listener


def is_rodando():
    """Verifica se o listener está rodando."""
    l = get_listener()
    return l is not None and l.rodando


def iniciar():
    """Inicia o listener."""
    l = get_listener()
    if l and not l.rodando:
        l.iniciar()
        return True
    return False


def parar():
    """Para o listener."""
    l = get_listener()
    if l and l.rodando:
        l.parar()
        return True
    return False


def status():
    """Retorna status do listener."""
    l = get_listener()
    if not l:
        return {"registrado": False, "rodando": False}
    
    return {
        "registrado": True,
        "rodando": l.rodando,
        "frases_processadas": l.frases_processadas,
        "ultima_frase": l.ultima_frase,
        "nivel_atual": l.nivel_atual,
        "threshold": l.threshold,
        "metodo": l.metodo_transcricao if hasattr(l, 'metodo_transcricao') else 'desconhecido',
        "estado_microfone": getattr(l, "estado_microfone", "desconhecido"),
        "ultimo_erro": getattr(l, "ultimo_erro_transcricao", None),
    }
