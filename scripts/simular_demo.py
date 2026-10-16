"""
Libero - Simulação de Demo
Simula eventos para testar o sistema sem depender de microfone.
Use para testar antes de gravar o vídeo.
"""

import sys
import time
import requests
from datetime import datetime

API = "http://localhost:8080"
TOKEN_ADMIN = "libero-admin-token"
IDOSO = "dona-maria"

# Cores para o terminal
class C:
    OK = '\033[92m'
    WARN = '\033[93m'
    FAIL = '\033[91m'
    INFO = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'


def log(msg, tipo="info"):
    cor = {
        "info": C.INFO,
        "ok": C.OK,
        "warn": C.WARN,
        "fail": C.FAIL,
    }.get(tipo, "")
    print(f"{cor}{msg}{C.END}")


def enviar_mensagem(texto, espera=2):
    """Simula o idoso falando. Envia para o chat."""
    log(f"\n{'='*60}", "info")
    log(f"[IDOSO] {texto}", "warn")
    
    try:
        r = requests.post(
            f"{API}/chat/{IDOSO}/mensagem",
            json={"texto": texto},
            headers={"X-Libero-Token": TOKEN_ADMIN},
            timeout=30
        )
        
        if r.ok:
            resposta = r.json().get("resposta", "")
            log(f"[LIBERO] {resposta}", "ok")
            return resposta
        else:
            log(f"[ERRO] {r.status_code}: {r.text[:200]}", "fail")
            return None
    except Exception as e:
        log(f"[ERRO] {e}", "fail")
        return None
    
    time.sleep(espera)


def simular_emergencia(texto="Socorro, caí!"):
    """Simula emergência."""
    log(f"\n{'='*60}", "info")
    log(f"[EMERGÊNCIA] {texto}", "fail")
    
    try:
        r = requests.post(
            f"{API}/mcp/tools/verificar_seguranca",
            json={
                "idoso_id": IDOSO,
                "texto": texto,
                "features_audio": {"energia_max": 0.8, "duracao": 1},
                "features_visao": {"angulo_corpo": 80, "velocidade_queda": 0.8},
                "movimento": True
            },
            headers={"X-Libero-Token": TOKEN_ADMIN},
            timeout=30
        )
        
        if r.ok:
            resultado = r.json().get("result", {})
            nivel = resultado.get("nivel", "?")
            acoes = [a["tipo"] for a in resultado.get("acoes", [])]
            log(f"[NÍVEL] {nivel}", "fail")
            log(f"[AÇÕES] {acoes}", "warn")
            return resultado
        else:
            log(f"[ERRO] {r.status_code}: {r.text[:200]}", "fail")
            return None
    except Exception as e:
        log(f"[ERRO] {e}", "fail")
        return None


def simular_camera_movimento():
    """Simula evento de câmera."""
    log(f"\n{'='*60}", "info")
    log(f"[CÂMERA] Movimento detectado", "warn")
    
    try:
        r = requests.post(
            f"{API}/mcp/tools/verificar_seguranca",
            json={
                "idoso_id": IDOSO,
                "texto": "",
                "features_visao": {"angulo_corpo": 10, "velocidade_queda": 0},
                "movimento": True
            },
            headers={"X-Libero-Token": TOKEN_ADMIN},
            timeout=30
        )
        
        if r.ok:
            resultado = r.json().get("result", {})
            log(f"[RESULTADO] {resultado.get('nivel', 0)}", "ok")
            return resultado
    except Exception as e:
        log(f"[ERRO] {e}", "fail")


def verificar_sistema():
    """Verifica se o sistema está respondendo."""
    log("\n[VERIFICAÇÃO] Sistema está no ar?", "info")
    
    try:
        r = requests.get(f"{API}/health", timeout=5)
        if r.ok:
            dados = r.json()
            log(f"  ✓ Servidor OK ({dados.get('ferramentas', 0)} ferramentas)", "ok")
            return True
    except Exception as e:
        log(f"  ✗ Servidor offline: {e}", "fail")
        log("  → Rode: python cloud/mcp_server/server.py", "warn")
        return False


def main():
    log(f"\n{'#'*60}", "info")
    log(f"# LIBERO - SIMULAÇÃO DE DEMO", "info")
    log(f"# Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", "info")
    log(f"{'#'*60}", "info")
    
    if not verificar_sistema():
        return
    
    # ============================================================
    # CENÁRIO 1: Conversa normal
    # ============================================================
    log(f"\n\n{'='*60}", "info")
    log("CENÁRIO 1: Conversa normal", "info")
    log(f"{'='*60}", "info")
    
    enviar_mensagem("Oi, tudo bem?")
    time.sleep(2)
    enviar_mensagem("Bom dia")
    time.sleep(2)
    
    # ============================================================
    # CENÁRIO 2: Confusão (validação)
    # ============================================================
    log(f"\n\n{'='*60}", "info")
    log("CENÁRIO 2: Confusão (terapia de validação)", "info")
    log(f"{'='*60}", "info")
    
    enviar_mensagem("Preciso ir para casa")
    time.sleep(2)
    enviar_mensagem("Cadê minha mãe?")
    time.sleep(2)
    enviar_mensagem("Preciso ir trabalhar")
    time.sleep(2)
    
    # ============================================================
    # CENÁRIO 3: Memória (reminiscência)
    # ============================================================
    log(f"\n\n{'='*60}", "info")
    log("CENÁRIO 3: Memória (reminiscência)", "info")
    log(f"{'='*60}", "info")
    
    enviar_mensagem("Quando eu era jovem, eu dançava com meu marido no clube")
    time.sleep(2)
    enviar_mensagem("Meu pai me ensinou a trabalhar")
    time.sleep(2)
    
    # ============================================================
    # CENÁRIO 4: Cuidado
    # ============================================================
    log(f"\n\n{'='*60}", "info")
    log("CENÁRIO 4: Cuidado", "info")
    log(f"{'='*60}", "info")
    
    enviar_mensagem("Estou com sede")
    time.sleep(2)
    enviar_mensagem("Estou triste")
    time.sleep(2)
    
    # ============================================================
    # CENÁRIO 5: Emergência
    # ============================================================
    log(f"\n\n{'='*60}", "info")
    log("CENÁRIO 5: Emergência (queda)", "info")
    log(f"{'='*60}", "info")
    
    simular_emergencia("Socorro, caí!")
    time.sleep(3)
    
    # ============================================================
    # CENÁRIO 6: Câmera
    # ============================================================
    log(f"\n\n{'='*60}", "info")
    log("CENÁRIO 6: Câmera (movimento)", "info")
    log(f"{'='*60}", "info")
    
    simular_camera_movimento()
    time.sleep(2)
    
    # ============================================================
    # RESUMO
    # ============================================================
    log(f"\n\n{'#'*60}", "ok")
    log("# SIMULAÇÃO COMPLETA", "ok")
    log(f"# Verifique o dashboard para ver os resultados", "ok")
    log(f"{'#'*60}", "ok")
    log(f"\nPróximos passos:", "info")
    log(f"  1. Abra o dashboard: http://localhost:3000", "info")
    log(f"  2. Vá em Conversas → veja o histórico", "info")
    log(f"  3. Vá em Memórias → veja as histórias", "info")
    log(f"  4. Vá em Alertas → veja as emergências", "info")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\n\n[Simulação interrompida]", "warn")
    except Exception as e:
        log(f"\n\n[Erro fatal] {e}", "fail")
