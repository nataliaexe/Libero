# Libero

> Porque ninguém deveria se perder. Nem quem cuida.

## O Problema

60% das pessoas com demência vão vagar. 50% se machucam. 10% morrem.
66% dos cuidadores têm depressão. 40% morrem antes do paciente.

## A Solução

Libero é um sistema de cuidado para idosos com Alzheimer ou demência.
Ele percebe quando o idoso está confuso, agitado ou tentando sair sozinho.
E age: conversa, acalma, orienta, avisa a família.

## Como Funciona

1. **Captura**: áudio contínuo + sensores de movimento.
2. **Entende**: IA analisa voz, tom, contexto.
3. **Decide**: 4 níveis (observação, conversa, intervenção, emergência).
4. **Age**: voz, notificação, emergência.
5. **Aprende**: feedback loop contínuo.

## Stack

- **Edge**: Python, OpenCV, Whisper
- **Cloud**: AWS (Bedrock, AgentCore, Strands)
- **MCP**: Streamable HTTP (spec 2025-11-25+)
- **Interface**: Fire TV, React Native, React
- **Dados**: DynamoDB, Timestream, S3
- **Voz**: Whisper (entrada), Amazon Polly (saída)

## Governança

- Privacy by Design
- Criptografia end-to-end
- Expiração automática
- Auditoria completa
- Compliance (LGPD, GDPR, HIPAA)

## Licença

MIT
