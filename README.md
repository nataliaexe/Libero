# Libero

> Porque ninguém deveria se perder. Nem quem cuida.

---

## O Problema

Em 2024, um senhor com Alzheimer pegou a garrafa de café e saiu para trabalhar. Como fazia há 40 anos. Ele andou. Se machucou. Caiu. Morreu sozinho no mato. A família passou 30 dias procurando.

O cuidador tinha saído por 10 minutos.

**Isso não é um caso isolado.**

- **55 milhões** de pessoas vivem com demência no mundo. Serão **152 milhões** em 2050.
- **60%** vão vagar em algum momento.
- **50%** dos que vagam se machucam. **10%** morrem.
- **66%** dos cuidadores têm sintomas de depressão.
- **40%** dos cuidadores morrem antes do paciente.

**Ninguém cuida de quem cuida.**

---

## A Solução

**Libero é um protótipo de pesquisa e desenvolvimento** para explorar assistência por voz, percepção local e ferramentas de apoio a cuidadores.

O repositório contém módulos de captura, heurísticas de segurança, uma API, armazenamento local e telas web. Os caminhos ainda não formam um serviço autônomo validado. Em particular, os escores não são probabilidades calibradas e as ações de emergência retornadas pelo detector são propostas: esse fluxo não chama o SAMU, não dispara SNS e não abre a câmera automaticamente.

As respostas conversacionais são orientadas por princípios de validação e reminiscência, mas não há avaliação clínica que garanta esse comportamento em todas as respostas do modelo.

---

## Como Funciona

```
┌─────────────────────────────────────────────────────────────┐
│                       LIBERO                                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  🎤 ÁUDIO                📷 CÂMERA                          │
│  (quando configurado)    (captura local/endpoint manual)     │
│      │                       │                               │
│      └───────────┬───────────┘                               │
│                  ▼                                            │
│  ┌──────────────────────────────────────┐                   │
│  │       CÉREBRO (Edge + Cloud)          │                   │
│  │                                        │                   │
│  │  • Transcrição (Groq Whisper)         │                   │
│  │  • Decisão contextual (4 níveis)      │                   │
│  │  • 8 agentes especializados           │                   │
│  │  • 3 camadas de conhecimento clínico  │                   │
│  └──────────────────┬───────────────────┘                   │
│                     │                                        │
│      ┌──────────────┼──────────────┐                        │
│      ▼              ▼              ▼                        │
│  ┌────────┐    ┌────────┐    ┌────────┐                    │
│  │COMPANHIA│   │SEGURANÇA│   │ FAMÍLIA│                    │
│  │ conversa│   │ detecta │   │notifica│                    │
│  └────────┘    └────────┘    └────────┘                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Os 4 Níveis de Intervenção

| Nível | Quando | O Que Faz |
| :--- | :--- | :--- |
| **0 - Observação** | Nenhum sinal reconhecido | O classificador não encontrou um padrão configurado; isso não comprova que esteja tudo bem. |
| **1 - Conversa** | Entrada textual para conversa | O orquestrador prepara uma resposta. |
| **2 - Intervenção** | Sinal heurístico acima do limiar | Gera uma resposta e pode listar ações propostas; não as executa. |
| **3 - Emergência** | Queda ou texto sinalizado | Gera uma resposta e propostas de ação; nenhum serviço de emergência é chamado por esse fluxo. |

### Os 8 Agentes

| Agente | Função |
| :--- | :--- |
| **Companhia** | Prepara respostas de conversa; sem garantia de segurança clínica |
| **Segurança** | Aplica heurísticas a sinais recebidos; não confirma eventos clínicos |
| **Memória** | Módulo para histórias e reminiscências; integração ainda parcial |
| **Cuidado** | Módulo de lembretes; não há agendador/entrega automática |
| **Família** | Tem integração explícita opcional com SNS; não faz parte do fluxo automático de emergência |
| **Saúde** | Módulo experimental; não substitui avaliação clínica |
| **Governança** | Regras e registros de auditoria; não certifica compliance |
| **Orquestrador** | Coordena partes do fluxo, sem executar ações externas de segurança |

---

## Stack Técnica

### Estado verificado no repositório

| Camada | Tecnologia | Status |
| :--- | :--- | :--- |
| **Transcrição** | Groq Whisper e fallback local | Implementação presente; depende de dispositivo, credenciais e serviço disponíveis |
| **LLM e TTS** | Groq, Bedrock e Polly | Integrações presentes; este teste não comprova disponibilidade externa |
| **Câmera** | OpenCV e MediaPipe/OpenCV | Captura depende do hardware; heurísticas não foram validadas em ambiente real |
| **Segurança** | Regras textuais e sinais de áudio/visão | Testes sintéticos; escores não calibrados e captura edge sem fusão temporal robusta |
| **API e autorização** | FastAPI, sessões e papéis | Testes unitários e smoke ASGI; sessões e limites ficam em memória |
| **Histórico e tasks** | Arquivos JSON locais | Não usam as tabelas DynamoDB declaradas no CDK |
| **Notificações** | Cliente SNS opcional | Envio só ocorre pela ferramenta explícita; `sent` significa aceite do SNS, não entrega ao cuidador |
| **Ações de segurança** | Plano retornado pelo detector | Não chama emergência, não inicia a câmera nem notifica a família automaticamente |
| **Interface web** | HTML/CSS/JavaScript | Telas de protótipo; Rede e Perfil são locais, e as ações do perfil do idoso são simuladas |
| **Testes** | `pytest tests/` | Cobrem regras e integrações simuladas; não validam dispositivos, serviços externos ou eficácia clínica |

### O Que É Roadmap

| Feature | Status |
| :--- | :--- |
| Integração com Bee (wearable físico) | Roadmap |
| Integração com YouTube, Netflix, Spotify | Roadmap |
| Integração com WhatsApp, Email | Roadmap |
| Persistência remota de memórias, rotina e conversas | Roadmap |
| Alarmes e entrega de tarefas | Roadmap |
| Convites e roteamento de alertas para a rede de cuidado | Roadmap |
| Geração de apresentações de memórias | Roadmap |
| Rede neural terapêutica própria | Roadmap 1-2 anos |
| Fine-tuning clínico do LLM | Roadmap 3-6 meses |
| LGPD/GDPR/HIPAA compliance certificado | Roadmap |

---

## Privacidade e Ética

O repositório contém controles de acesso e opções locais, mas ainda não demonstra garantias de privacidade ou segurança ponta a ponta.

| Camada | O Que Faz |
| :--- | :--- |
| **Captura** | O listener pode capturar continuamente; a câmera edge e a câmera da API são fluxos separados. |
| **Processamento** | O áudio pode ser enviado ao provedor de transcrição configurado. Não há garantia de que só metadados saiam do dispositivo. |
| **Armazenamento** | Histórico e tarefas usam arquivos JSON locais; retenção e criptografia em repouso não são garantidas pelo aplicativo. |
| **Acesso** | Há autenticação por sessão e papéis; sessões e limites são mantidos em memória. |
| **Transparência** | A interface ainda não oferece uma visão confiável do estado de todos os sensores. |

**Não há fluxo automático de envio de vídeo para emergência neste protótipo.** Isso não equivale a uma garantia geral de privacidade do dispositivo ou da rede.

### Sobre a câmera

- **Detector edge**: OpenCV e, quando disponível, MediaPipe processam no dispositivo.
- **Transmissão**: o endpoint de câmera pode servir um stream autenticado; confirme a configuração de rede antes de expor.
- **Retenção**: o aplicativo não implementa retenção de vídeo por sete dias.
- **Transparência**: o indicador de estado de câmera depende do fluxo usado e não cobre todos os dispositivos.
- O detector edge e a câmera exposta pela API são instâncias separadas; a interface não confirma o estado do detector edge.

---

## Como Rodar

### Requisitos

- Python 3.11+
- Linux, macOS ou Windows
- Microfone e câmera (ou apenas um dos dois)
- (Opcional) Conta AWS para Bedrock + Polly
- (Opcional) Conta Groq para Whisper + Llama

### Instalação

```bash
# 1. Clonar
git clone https://github.com/nataliaexe/Libero.git
cd Libero

# 2. Virtualenv
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# ou: venv\Scripts\activate  # Windows

# 3. Dependências
pip install -r requirements.txt

# 4. Configurar variáveis
cp .env.example .env
nano .env
```

### Configurar `.env`

```bash
# Groq (transcrição + LLM)
GROQ_API_KEY=sua_chave_aqui
GROQ_LLM_MODEL=openai/gpt-oss-120b

# AWS (Bedrock + Polly)
AWS_REGION=us-east-2
BEDROCK_MODEL_ID=arn:aws:bedrock:us-east-2:...:inference-profile/us.anthropic.claude-haiku-4-5-20251001-v1:0
POLLY_VOICE=Camila

# MCP
MCP_PORT=8080
MCP_HOST=127.0.0.1

# Ambiente local de demonstração. Para exposição pública, consulte docs/SECURITY_DEPLOYMENT.md.
LIBERO_ENV=development
```

### Rodar

```bash
# Terminal 1: MCP Server
python cloud/mcp_server/server.py

# Terminal 2: Dashboard
python -m http.server 3000 --directory interface/web

# Terminal 3: Libero (áudio + câmera + voz)
python edge/main.py
```

### Acessar

- **Dashboard**: http://localhost:3000/dashboard.html
- **Câmera**: http://localhost:3000/camera.html
- **MCP API**: http://localhost:8080/mcp/tools

### Contas de Teste (somente desenvolvimento local)

| Email | Senha | Role |
| :--- | :--- | :--- |
| ana@libero.com | libero123 | família |
| medico@libero.com | medico123 | médico |
| admin@libero.com | admin123 | admin |

Não use essas contas em um servidor acessível pela rede.

---

## Testes

Antes de tornar a API acessível pela rede, siga o guia de [exposição segura](docs/SECURITY_DEPLOYMENT.md). O modo padrão é produção e exige credenciais explícitas; contas demonstrativas só funcionam com `LIBERO_ENV=development` em loopback.

```bash
# Todos os testes
pytest tests/ -v

# Só unitários
pytest tests/unit/ -v

# Só integração
pytest tests/integration/ -v
```

Os testes automatizados cobrem regras e integrações simuladas. O número atual deve ser obtido executando `pytest tests/ -v`; esses testes não provam eficácia clínica nem operação com hardware ou serviços externos.

- Regras heurísticas para texto e combinação de sinais informados por chamada; os escores não são calibrados.
- Testes de autorização, ferramentas e módulos com dependências simuladas.
- O fluxo de segurança não chama o SAMU nem executa notificações externas.

---

## Estrutura do Projeto

```
libero/
├── edge/                          # Processamento local
│   ├── capture/                   # Áudio, câmera, VAD, listener
│   ├── processing/                # Transcrição, features
│   ├── output/                    # Voz (TTS)
│   ├── decision/                  # Níveis de intervenção
│   └── main.py                    # Sistema completo
├── cloud/                         # Processamento em nuvem
│   ├── agents/                    # 8 agentes
│   ├── knowledge/                 # Estágios, terapias, crises
│   ├── mcp_server/                # MCP + câmera + auth + WebSocket
│   ├── data/                      # DynamoDB, Timestream
│   ├── notification/              # SNS
│   └── ml/                        # Roadmap ML
├── interface/                     # Interfaces
│   ├── web/                       # Dashboard + câmera
│   ├── firetv/                    # Fire TV App
│   └── mobile/                    # Mobile App
├── infra/                         # Infraestrutura
│   └── cdk/                       # AWS CDK (5 stacks)
├── tests/                         # Testes
├── docs/                          # Documentação
├── scripts/                       # Automação
└── 3d/                            # Modelos 3D
```

---

## O Que Torna o Libero Diferente

### 1. Princípios de validação como orientação

Os prompts e módulos tentam seguir princípios de **Terapia de Validação (Naomi Feil)** e **Reminiscência**. Isso não garante que toda saída do modelo siga esses princípios.

Exemplos de resposta pretendida:
- "Você trabalhou por muitos anos. Me conta sobre isso."
- "Sua mãe deve ter sido incrível. Como ela era?"
- "Me fala da sua casa. Como ela é?"

### 2. Heurísticas de segurança em evolução

Queda não deve ser inferida por um som isolado. Há uma função que combina sinais de áudio e visão recebidos, mas a captura edge ainda não os sincroniza em uma janela temporal robusta. Os escores são regras heurísticas e não têm calibração clínica. Nenhuma chamada ao SAMU é feita automaticamente.

### 3. Escalonamento Proporcional

O detector considera sinais de intenção verbal e de comportamento observado separadamente. A política ainda é heurística e não tem validação clínica; ações externas retornadas são propostas e não são executadas por esse fluxo.

### 4. Notificação Honesta

A maioria dos sistemas diz "notificado" mesmo quando falha.

O módulo de notificação distingue alguns estados de processamento. `sent` indica aceite do SNS, não confirmação de entrega ao cuidador; o fluxo automático de emergência ainda não aciona esse módulo.

### 5. Governança Integrada

Auditoria de todas as decisões. Detecção de viés. Explicabilidade. Compliance como **framework**, não slogan.

---

## Visão de Longo Prazo

O Libero não é um projeto de hackathon. É um **produto em construção**.

**Próximos passos**:

1. **Bee (wearable)**: captura de áudio contínua, sem depender de microfone ambiente.
2. **Multi-casa**: um cuidador monitora múltiplos idosos.
3. **Rede neural terapêutica**: modelo próprio treinado em conversas clínicas.
4. **Integração com planos de saúde**: preventivo, não reativo.
5. **Pesquisa clínica**: medir impacto real em cuidadores e pacientes.

**Modelo de negócio**:

| Plano | Preço | Público |
| :--- | :--- | :--- |
| Família | R$ 299/mês | 1 idoso, dashboard, memórias |
| Casa de Repouso | R$ 500/leito/mês | Múltiplos idosos, painel |
| Plano de Saúde | R$ 100/vida/mês | Prevenção, ROI 40x |

---

## Licença

MIT. Veja [LICENSE](LICENSE).

---

## Autor

**Natália Borges Vargas**  
Projeto submetido ao **Build, Ship, Shape: Amazon Developer Hackathon**.

---

## Reconhecimentos

- **Bee** (wearable AI)
- **Alexa+** (MCP Server)
- **AWS Bedrock** (Claude Haiku 4.5)
- **AWS Polly** (voz neural)
- **Groq** (Whisper + Llama)
- **Naomi Feil** (Terapia de Validação)
- **Dr. Oliver Sacks** (inspiração sobre memória e identidade)

---

> *"A IA não vai enlouquecer. Ela vai se manter sã. Ela vai aliviar."*
