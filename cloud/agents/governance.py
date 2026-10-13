"""
Libero - Agente de Governança
Auditoria, detecção de viés, compliance, explicabilidade.
"""

import os
import json
import hashlib
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()


class Auditoria:
    """Registra e audita todas as decisões do Libero."""
    
    def __init__(self):
        self.log = []
    
    def registrar(self, agente, acao, contexto, resultado, razao=None):
        """
        Registra uma ação de um agente.
        
        Args:
            agente: nome do agente (companion, safety, etc.)
            acao: o que foi feito
            contexto: contexto da ação
            resultado: resultado da ação
            razao: por que foi feito
        """
        entrada = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agente": agente,
            "acao": acao,
            "contexto": contexto,
            "resultado": resultado,
            "razao": razao,
            "hash": self._hash(agente, acao, contexto)
        }
        
        self.log.append(entrada)
        return entrada
    
    def _hash(self, agente, acao, contexto):
        """Gera hash para verificação de integridade."""
        conteudo = f"{agente}:{acao}:{json.dumps(contexto, sort_keys=True)}"
        return hashlib.sha256(conteudo.encode()).hexdigest()[:16]
    
    def exportar(self, arquivo="auditoria.json"):
        """Exporta o log de auditoria."""
        with open(arquivo, "w") as f:
            json.dump(self.log, f, ensure_ascii=False, indent=2)
        return arquivo


class DetectorVies:
    """Detecta viés nas decisões do Libero."""
    
    def __init__(self):
        self.decisoes = []
    
    def registrar(self, decisao):
        self.decisoes.append(decisao)
    
    def detectar_vies(self):
        """Detecta padrões de viés."""
        vieses = []
        
        # Viés de gênero: trata diferente por gênero
        generos = [d.get("genero") for d in self.decisoes if d.get("genero")]
        if generos:
            fem = sum(1 for g in generos if g == "F")
            masc = sum(1 for g in generos if g == "M")
            if fem > 0 and masc > 0:
                razao = max(fem, masc) / min(fem, masc)
                if razao > 2:
                    vieses.append({
                        "tipo": "genero",
                        "descricao": f"Desbalanceamento: {fem}F / {masc}M",
                        "severidade": "media"
                    })
        
        # Viés de urgência: superestima emergência
        niveis = [d.get("nivel") for d in self.decisoes if d.get("nivel") is not None]
        if niveis:
            emergencias = sum(1 for n in niveis if n == 3)
            proporcao = emergencias / len(niveis)
            if proporcao > 0.3:
                vieses.append({
                    "tipo": "urgencia",
                    "descricao": f"{proporcao*100:.1f}% das decisões foram emergência",
                    "severidade": "alta"
                })
        
        return vieses


class Compliance:
    """Verifica compliance com LGPD, GDPR, HIPAA."""
    
    REGRAS = {
        "LGPD": [
            "consentimento_explicito",
            "finalidade_especifica",
            "minimizacao_dados",
            "transparencia",
            "seguranca",
            "direito_ao_esquecimento"
        ],
        "GDPR": [
            "consentimento_explicito",
            "direito_ao_esquecimento",
            "portabilidade_dados",
            "transparencia",
            "seguranca"
        ],
        "HIPAA": [
            "criptografia",
            "auditoria",
            "controle_acesso",
            "integridade",
            "disponibilidade"
        ]
    }
    
    def verificar(self, regra):
        """Verifica se uma regra está sendo cumprida."""
        return {
            "regra": regra,
            "status": "pendente",
            "implementado": False
        }
    
    def relatorio(self):
        """Gera relatório de compliance."""
        return {
            "LGPD": len(self.REGRAS["LGPD"]),
            "GDPR": len(self.REGRAS["GDPR"]),
            "HIPAA": len(self.REGRAS["HIPAA"]),
            "total": sum(len(r) for r in self.REGRAS.values())
        }


class Governanca:
    """Agente de Governança completo."""
    
    def __init__(self):
        self.auditoria = Auditoria()
        self.detector_vies = DetectorVies()
        self.compliance = Compliance()
    
    def auditar(self, agente, acao, contexto, resultado, razao=None):
        """Audita uma ação."""
        return self.auditoria.registrar(agente, acao, contexto, resultado, razao)
    
    def registrar_decisao(self, decisao):
        """Registra uma decisão para detecção de viés."""
        self.detector_vies.registrar(decisao)
    
    def verificar_vies(self):
        """Verifica viés nas decisões."""
        return self.detector_vies.detectar_vies()
    
    def verificar_compliance(self):
        """Verifica compliance."""
        return self.compliance.relatorio()
    
    def explicar(self, decisao_id):
        """Explica uma decisão."""
        for entrada in self.auditoria.log:
            if entrada.get("hash") == decisao_id:
                return {
                    "decisao": entrada,
                    "explicacao": f"O agente {entrada['agente']} executou {entrada['acao']} porque {entrada.get('razao', 'não especificado')}"
                }
        return None


if __name__ == "__main__":
    print("=== Teste do Agente de Governança ===\n")
    
    gov = Governanca()
    
    # Auditar ações
    gov.auditar("safety", "detectar_queda", {"idoso": "dona-maria"}, "nivel_3")
    gov.auditar("companion", "conversar", {"idoso": "dona-maria"}, "resposta_gerada")
    gov.auditar("memory", "gravar_historia", {"idoso": "dona-maria"}, "gravado")
    
    print(f"Auditorias: {len(gov.auditoria.log)}")
    
    # Registrar decisões
    gov.registrar_decisao({"genero": "F", "nivel": 2})
    gov.registrar_decisao({"genero": "F", "nivel": 3})
    gov.registrar_decisao({"genero": "M", "nivel": 2})
    
    print(f"Viés: {gov.verificar_vies()}")
    print(f"Compliance: {gov.verificar_compliance()}")
