# Libero ML — Roadmap

Este diretório contém o **roadmap** para a evolução do Libero de regras + LLM para uma rede neural terapêutica própria.

## Estado atual (v1.0)

- **Regras de decisão** (`edge/decision/levels.py`) — determinístico, auditável
- **LLM (Claude via Bedrock)** — geração de respostas terapêuticas
- **Base de conhecimento** (`cloud/knowledge/`) — terapia de validação, reminiscência, musicoterapia

## Roadmap

### v1.1 — Fine-tuning leve (3-6 meses)

- Coletar dataset de conversas terapêuticas anonimizadas
- Fine-tune do Claude via Bedrock Custom Models
- Avaliação clínica com terapeutas

### v1.2 — RAG terapêutico (6-12 meses)

- Banco vetorial de técnicas terapêuticas (validação, reminiscência, CBT)
- Recuperação contextual em tempo real
- Avaliação de eficácia

### v2.0 — Rede neural própria (1-2 anos)

- Transformer pequeno (~1B params) treinado em:
  - Conversas terapêuticas (com consentimento)
  - Literatura clínica sobre demência
  - Protocolos de crise
- Inferência local no dispositivo (edge)
- Avaliação clínica randomizada

## Por que não agora

Uma rede neural própria exige:
1. Dataset clínico (não temos)
2. Validação clínica (não temos)
3. Tempo de treino (semanas)
4. GPU (caro)

O **LLM + regras** entrega **80% do valor** com **5% do esforço**. A rede neural é a evolução, não o ponto de partida.

## Ética

Qualquer modelo treinado precisa:
- Consentimento explícito dos dados
- Validação por terapeutas
- Auditoria de viés
- Explicabilidade das decisões

**Não vamos treinar nada sem isso.**
