# Libero - Friction Log

Registro de problemas encontrados durante o desenvolvimento.

## Formato

- **Tarefa**: O que eu tentei fazer
- **Passos**: O que eu fiz
- **Esperado**: O que eu esperava
- **Real**: O que aconteceu
- **Severidade**: baixa / média / alta
- **Workaround**: Como resolvi
- **Sugestão**: O que poderia melhorar

---

## 2026-10-06 - Bedrock sem credenciais

- **Tarefa**: Testar o agente de companhia
- **Passos**: `python cloud/agents/companion.py`
- **Esperado**: Resposta gerada pelo Claude
- **Real**: Erro "Unable to locate credentials"
- **Severidade**: baixa
- **Workaround**: Fallback offline implementado
- **Sugestão**: Documentar como configurar credenciais AWS no README

---

## 2026-10-06 - Timestream sem credenciais

- **Tarefa**: Registrar métricas de saúde
- **Passos**: `python cloud/agents/health.py`
- **Esperado**: Métrica salva no Timestream
- **Real**: Erro "Unable to locate credentials"
- **Severidade**: baixa
- **Workaround**: Fallback local
- **Sugestão**: Adicionar DynamoDB Local no docker-compose

---

## 2026-10-06 - Detecção de emergência imprecisa

- **Tarefa**: Testar "Socorro, caí!"
- **Passos**: `python cloud/agents/orchestrator.py`
- **Esperado**: Nível 3 com chamar_emergencia
- **Real**: Nível 3 sem chamar_emergencia
- **Severidade**: alta
- **Workaround**: Adicionado tipo "emergencia_texto" no safety.agir
- **Sugestão**: Documentar os tipos de evento esperados

---

## 2026-10-06 - utcnow() deprecated

- **Tarefa**: Rodar orquestrador no Python 3.14
- **Passos**: `python cloud/agents/orchestrator.py`
- **Esperado**: Sem warnings
- **Real**: DeprecationWarning sobre utcnow()
- **Severidade**: baixa
- **Workaround**: Substituído por datetime.now(timezone.utc)
- **Sugestão**: Nenhuma

---

## 2026-10-06 - Memória não detectava histórias curtas

- **Tarefa**: Testar "Meu pai me ensinou a trabalhar"
- **Passos**: `python cloud/agents/memory.py`
- **Esperado**: História detectada
- **Real**: Não detectada
- **Severidade**: média
- **Workaround**: Aumentado peso dos marcadores e reduzido threshold
- **Sugestão**: Documentar os marcadores de história
