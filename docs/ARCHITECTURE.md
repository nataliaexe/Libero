# Libero - Arquitetura

## Visão Geral

O Libero é um sistema de cuidado para idosos com Alzheimer ou demência.
Ele percebe quando o idoso está confuso, agitado ou tentando sair sozinho,
e age: conversa, acalma, orienta, avisa a família.

## Camadas

### 1. Edge (Dispositivo)

- **Captura de áudio**: VAD, buffer circular
- **Captura de movimento**: Frame differencing
- **Detecção de queda**: Pose estimation (MediaPipe)
- **Processamento local**: Whisper tiny, extração de features
- **Decisão local**: Níveis 0-3

### 2. Cloud (AWS)

- **MCP Server**: Expõe ferramentas para Alexa+
- **Agentes**:
  - Companhia (terapia de validação)
  - Segurança (queda, fuga, agitação)
  - Memória (histórias, reminiscência)
  - Cuidado (remédios, água, comida)
  - Família (notificações, relatórios)
  - Saúde (detecção precoce)
  - Governança (auditoria, viés, compliance)
- **Dados**: DynamoDB, Timestream, S3
- **Notificação**: SNS, SES, Connect

### 3. Conhecimento

- **Estágios**: Braak, Reisberg, CDR, GDS
- **Terapias**: Validação, reminiscência, musicoterapia, etc.
- **Crises**: Sundowning, agitação, alucinação, fuga, queda

### 4. Interface

- **Fire TV**: Interface do idoso
- **Mobile**: Interface do cuidador
- **Web**: Dashboard da família

## Fluxo de Dados

Idoso → Edge → Cloud → Agentes → Ação → Idoso
↓
Família

## Níveis de Intervenção

| Nível | Quando | O Que Faz |
| :--- | :--- | :--- |
| 0 | Tudo normal | Observa |
| 1 | Oportunidade | Conversa |
| 2 | Confusão, agitação | Intervém |
| 3 | Queda, fuga | Emergência |
