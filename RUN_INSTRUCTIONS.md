# Como Rodar o Projeto Libero

Este projeto precisa de 2-3 terminais para funcionar completamente.

## Terminal 1: Backend MCP Server

```bash
cd ~/libero
source venv/bin/activate
pkill -f "cloud/mcp_server/server.py"
sleep 1
python cloud/mcp_server/server.py
```

**O que faz:** Servidor de API que gerencia autenticação, chat, tarefas, dispositivos e WebSocket.
**Porta:** 8080
**URL:** http://127.0.0.1:8080

---

## Terminal 2: Frontend React

```bash
cd ~/libero/frontend
npm install  # (apenas na primeira vez)
npm run dev
```

**O que faz:** Interface React com avatar, chat, emparelhamento de dispositivos.
**Porta:** 3000
**URL:** http://localhost:3000/react-app.html

**Nota:** Este comando:
1. Compila o avatar 3D
2. Compila o app React
3. Inicia servidor HTTP estático

---

## Terminal 3 (Opcional): Edge Service

```bash
cd ~/libero
source venv/bin/activate
pkill -f "edge/main.py"
sleep 1
python edge/main.py
```

**O que faz:** Captura de áudio e câmera em tempo real (microfone, detecção de quedas, movimentos).
**Porta:** 8081
**URL:** http://127.0.0.1:8081

**Nota:** Necessário apenas se quiser usar captura de áudio/câmera.

---

## Acessando a Aplicação

### Nova Interface React (Recomendada)
- URL: http://localhost:3000/react-app.html
- Features:
  - Avatar 3D animado
  - Chat com polling a cada 5 segundos
  - Modo TV (avatar em tela cheia)
  - Emparelhamento de dispositivos (TV, tablets)
  - Login com autenticação

### Interface Legada (Ainda disponível)
- URL: http://localhost:3000/dashboard.html
- Features:
  - Dashboard antigo
  - WebSocket (agora corrigido)
  - Páginas: alertas, chat, memórias, ambiente, tarefas

---

## Login Padrão (Development)

Email: `admin@libero.dev`
Senha: `admin123`

Ou use a variável de ambiente `LIBERO_TOKEN` para bypass de desenvolvimento.

---

## Troubleshooting

### WebSocket 403 Error
**Corrigido:** Em modo development, o WebSocket aceita conexões SEM autenticação para facilitar debug. Não requer token.

### Avatar não aparece
1. Verifique se o arquivo `woman.glb` existe em `frontend/public/`
2. Verifique se foi copiado para `interface/web/assets/libero-avatar/`
3. Execute `npm run build:avatar` novamente

### Erro de import no React
1. Execute `npm install` no diretório `frontend/`
2. Verifique se `node_modules` existe

### Porta já em uso
```bash
# Para matar processo na porta 8080
lsof -ti:8080 | xargs kill -9

# Para matar processo na porta 3000
lsof -ti:3000 | xargs kill -9
```

---

## Estrutura de Arquivos Modificados

### Backend
- `cloud/mcp_server/server.py` - Adicionados endpoints de dispositivos, corrigido WebSocket
- `cloud/mcp_server/auth.py` - Adicionada função `extrair_token_websocket()`

### Frontend
- `frontend/src/components/ModoTV.jsx` - Modo TV com emparelhamento
- `frontend/src/components/DevicePairing.jsx` - Modal de pareamento de dispositivos
- `frontend/src/components/Chat.jsx` - Chat com polling (já existia, verificado)
- `frontend/src/components/LiberoAvatar.jsx` - Caminho do avatar corrigido
- `frontend/src/styles.css` - Estilos para TV, pareamento, chat
- `frontend/vite.app.config.js` - Config de build para app React
- `frontend/package.json` - Scripts atualizados
- `interface/web/react-app.html` - HTML para app React

---

## Funcionalidades Implementadas

✅ WebSocket autenticação corrigida
✅ Avatar 3D configurado e acessível
✅ Modo TV (avatar em tela cheia sem bloquear funcionalidades)
✅ Emparelhamento de dispositivos (TV, tablets)
✅ Chat com polling a cada 5 segundos
✅ Envio de mensagens com onSubmit
✅ Sincronização de estado do avatar
