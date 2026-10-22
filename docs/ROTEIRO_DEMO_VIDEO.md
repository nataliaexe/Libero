# Libero — roteiro do vídeo demo

**Duração-alvo:** 1:40–1:50. **Idioma falado:** inglês. O vídeo deve ficar abaixo de três minutos.

## Preparação

- Abra o dashboard já autenticado, com dados fictícios. Não mostre senha, cookie, token, perfil real ou dados de saúde de uma pessoa real.
- Inicie a API, o processo edge e o servidor web. `scripts/run-all.sh` sobe os três serviços quando `tmux` e o virtualenv estão instalados.
- Use a conversa digitada da interface. Ela chama o MCP Streamable HTTP real; não apresente o ensaio como captura de voz ao vivo.
- Envie “I need to go home.” Confirme que aparece uma resposta e o selo `MCP 2025-11-25 · iniciar_conversa completed`.
- Envie “When I was young, I danced with my husband at the club.” Confirme que a memória aparece na tela Memories. O registro é local no protótipo.
- O selo do modelo mostra o provedor real. Se aparecer `local fallback`, mantenha essa indicação. Só reivindique Bedrock se aparecer `Amazon Bedrock`.
- Não mostre a câmera; ela é opcional e depende de consentimento e de um dispositivo estável.

## Roteiro em inglês

| Tempo | Imagem e ação | Narração / fala |
|---|---|---|
| 0:00–0:10 | Comece no dashboard e aproxime a tela da conversa recente. | “When someone living with dementia says, ‘I need to go home,’ a reminder alone cannot address the feeling behind those words.” |
| 0:10–0:22 | Abra Conversations. Digite `I need to go home.` e envie. | “Libero connects a supportive conversation to a record the family can review.” |
| 0:22–0:45 | Mostre a resposta real, o provedor real e o selo MCP atualizado. Segure a tela alguns segundos para leitura. | “This is a simulated Alexa+ experience using Libero’s MCP server. The app negotiates protocol 2025-11-25, discovers its tools, and completes the `iniciar_conversa` call. The provider label tells you how this response was produced.” |
| 0:45–1:02 | Na mesma conversa, envie `When I was young, I danced with my husband at the club.` Mostre que Libero responde. | “A conversation can also preserve a personal story, so the family has more context than a task reminder.” |
| 1:02–1:20 | Abra Memories e mostre a história salva; depois volte ao histórico da conversa. | “Libero saves this story in the local prototype and makes it available to review. Recent conversation and saved memories can inform a later reply.” |
| 1:20–1:42 | Termine no dashboard com o nome Libero e a atividade registrada. | “Libero is an early care-support prototype. It does not contact emergency services, verify medication, or replace a caregiver. Next, we want to pilot the conversation and memory flow with care partners and validate the alert pathways.” |

## Plano de contingência

- Se a resposta do modelo demorar, use uma gravação curta de uma execução real feita com a mesma versão. Não substitua a resposta por um mock.
- Se a memória não aparecer, não improvise: confirme a frase de teste e grave novamente após verificar a tela Memories.
- Se o edge indicar microfone indisponível, mantenha a demo digitada. Não chame o texto de transcrição ao vivo.
- Se o selo mostrar `local fallback`, não alegue que Groq ou Bedrock gerou aquela resposta.
- Corte a montagem de Memories antes de acelerar a fala. Preserve o fluxo MCP e a explicação transparente do protótipo.

## Checklist final de submissão

- Vídeo público, narrado em inglês e com menos de 3 minutos.
- Repositório GitHub acessível aos juízes, com código-fonte, assets, instruções e licença; o evento aceita repositório público open source ou privado compartilhado com os revisores.
- Feedback escrito para cada API/SDK/ferramenta usada: propósito, o que funcionou, fricções, onboarding e se usaria novamente.
- Descrever claramente o que mudou durante o hackathon, já que Libero começou antes do evento.
- Só marcar mini desafio AWS Builder se a execução demonstrada realmente usar um serviço AWS documentado, como Bedrock.

Veja também o [pitch do Libero](PITCH_LIBERO.md) e os [requisitos oficiais](https://amazonappdev2026.devpost.com/).
