# Privacidade no protótipo Libero

Esta página descreve o estado do código atual. O Libero é um protótipo de pesquisa; não tem certificação LGPD, HIPAA ou ANVISA e não deve ser usado como serviço de emergência.

## Implementado no protótipo

- A câmera edge só é iniciada quando `LIBERO_CAMERA_CONSENT=true` está configurado antes de iniciar o processo.
- A tela de ambiente consulta o status reportado pelo edge. Abrir ou ocultar o stream só controla a visualização no navegador; para parar a captura física, é necessário parar o processo edge.
- O listener processa sinais de áudio e transcreve fala por Groq quando configurado ou por Whisper local quando disponível. O áudio bruto é escrito temporariamente para transcrição; o código remove o arquivo temporário após a tentativa de transcrever.
- O dashboard grava mensagens, memórias e tarefas em arquivos JSON locais no diretório de dados do usuário. A autenticação aplica papéis e isolamento por idoso nas rotas protegidas.
- O stream do edge é local por padrão e sua configuração de origem usa uma lista explícita para o dashboard.

## Não implementado / roadmap

- Criptografia ponta a ponta ou criptografia em repouso dos arquivos JSON.
- Expiração automática de mensagens, áudio, imagens ou eventos.
- Garantia de que nenhum áudio/imagem seja enviado a terceiros: transcrição remota depende do provedor configurado.
- Consentimento granular por tipo de dado ou por participante, controles de retenção pelo dashboard e botão físico de mute.
- Borramento de terceiros, detecção de nudez ou zonas de exclusão de câmera.
- Auditoria persistente e imutável, rotação de chaves e certificações de conformidade.

## Orientação para demos

Use dados fictícios. Informe quando microfone, câmera ou provedor remoto estiver ativo. Não mostre ambientes íntimos nem pessoas que não consentiram. Não descreva o sistema como vigilância contínua validada, dispositivo médico ou substituto de cuidado humano.
