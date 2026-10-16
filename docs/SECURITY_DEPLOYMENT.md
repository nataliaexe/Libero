# Exposição segura do Libero

O servidor inicia em modo de produção por padrão e falha fechado se faltar configuração de autenticação ou a origem permitida do dashboard. Não publique o Uvicorn diretamente na internet. Termine TLS em um proxy reverso e encaminhe apenas tráfego HTTPS para o serviço.

## Configuração de produção

Guarde estas variáveis em um gerenciador de segredos do ambiente de execução. Não as coloque no Git, no HTML ou em logs.

```bash
LIBERO_ENV=production
MCP_HOST=127.0.0.1
MCP_PORT=8080
LIBERO_ALLOWED_ORIGINS=https://libero.example.com
LIBERO_USERS_JSON='[
  {"email":"cuidador@example.com","senha":"<senha-aleatoria-com-14-ou-mais-caracteres>","nome":"Cuidador","role":"familia","idoso_id":"dona-maria"},
  {"email":"admin@example.com","senha":"<outra-senha-aleatoria-com-14-ou-mais-caracteres>","nome":"Admin","role":"admin","idoso_id":"*"}
]'
```

`LIBERO_USERS_JSON` precisa conter ao menos uma conta admin. Os papéis aceitos são `familia`, `medico` e `admin`. Cada conta não admin deve estar vinculada a um único `idoso_id`. As senhas são derivadas com scrypt durante a inicialização; o servidor não grava as senhas em arquivos.

Não configure `LIBERO_TOKEN` ou `LIBERO_ADMIN_TOKEN` em produção. Esses tokens estáticos existem somente para compatibilidade com ferramentas locais e, se forem configurados, precisam ter pelo menos 32 caracteres aleatórios. Para usuários do dashboard, use login e sessões com cookie `HttpOnly`, `Secure` e `SameSite=Strict`.

Sirva o dashboard e a API na mesma origem HTTPS. O cookie de sessão é intencionalmente restrito a esse modelo. Se a instalação usar origens distintas, configure um proxy para unificá-las antes de alterar a política de cookies/CORS.

## Rede e operação

- Permita tráfego público somente na porta HTTPS do proxy. Mantenha a porta `8080` acessível apenas pelo proxy e serviços locais.
- Configure o proxy para validar e encaminhar corretamente o endereço do cliente; não confie em `X-Forwarded-For` recebido diretamente da internet.
- Mantenha o Uvicorn em um único processo enquanto sessões, rate limits, tickets de câmera e conexões WebSocket forem armazenados em memória. Reiniciar o serviço invalida as sessões e tickets.
- Configure o proxy como único caminho de entrada, com TLS, limites de requisição e logs sem cookies nem tickets. O limite de tentativas de login é em memória e pressupõe que o endereço do cliente encaminhado pelo proxy seja confiável.
- Restrinja as credenciais AWS e Groq aos serviços e recursos necessários. Não use credenciais pessoais ou de administrador da conta.
- O vídeo e o áudio envolvem dados altamente sensíveis. Defina consentimento, retenção, acesso de operadores, resposta a incidentes e monitoramento antes de usar com pessoas reais.
- O modo `development` inclui contas e tokens demonstrativos conhecidos. Use-o apenas em loopback e nunca para uma instância exposta.

## Desenvolvimento local

Defina `LIBERO_ENV=development` no `.env` local. Nesse modo, o dashboard pode rodar em `localhost:3000`, e a API em `localhost:8080`. As credenciais demonstrativas são apenas para desenvolvimento e não são aceitas no modo de produção.
