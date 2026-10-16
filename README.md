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

**Libero** é um sistema de cuidado 24 horas para idosos com Alzheimer ou demência que vivem em casa.

Ele usa **câmera e áudio contínuos** para perceber quedas, tentativas de saída, confusão e crises — e age na hora: **conversa, acalma, orienta ou chama ajuda**.

Cada resposta é baseada em **terapia de validação** e **reminiscência**: nunca corrige a realidade do idoso, sempre acolhe a emoção por trás dela.

A família recebe **notificações honestas** e **histórias gravadas automaticamente** — as memórias que o idoso conta viram legado, e o cuidador finalmente pode dormir.

**É a presença que nunca dorme, nunca se irrita e nunca enlouquece.**

---

## Como Funciona

```
┌─────────────────────────────────────────────────────────────┐
│                       LIBERO                                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  🎤 ÁUDIO                📷 CÂMERA                          │
│  (contínuo)              (contínuo)                          │
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
| **0 - Observação** | Tudo normal | Ouve, transcreve, arquiva. Não fala. |
| **1 - Conversa** | Oportunidade | Inicia conversa, valida, pergunta. |
| **2 - Intervenção** | Confusão, agitação | Acalma, orienta, notifica família. |
| **3 - Emergência** | Queda, fuga | Ativa câmera, notifica, chama SAMU. |

### Os 8 Agentes

| Agente | Função |
| :--- | :--- |
| **Companhia** | Conversa usando terapia de validação |
| **Segurança** | Detecta queda, fuga, agitação |
| **Memória** | Grava histórias e reminiscências |
| **Cuidado** | Lembra remédios, água, comida |
| **Família** | Notifica cuidadores com honestidade |
| **Saúde** | Correlaciona sintomas (ex: infecção urinária) |
| **Governança** | Audita decisões, detecta viés, compliance |
| **Orquestrador** | Coordena todos os agentes |

---

## Stack Técnica

### O Que Está Implementado

| Camada | Tecnologia | Status |
| :--- | :--- | :--- |
| **Transcrição** | Groq Whisper (large-v3-turbo) | ✅ Funcionando |
| **LLM** | Groq (Llama) + AWS Bedrock (Claude) | ✅ Funcionando |
| **Voz (TTS)** | AWS Polly (Camila, neural) | ✅ Funcionando |
| **Câmera** | OpenCV + MediaPipe | ✅ Funcionando |
| **Detecção de queda** | Pose estimation (multimodal) | ✅ Testado |
| **Decisão contextual** | Python (com detecção de negação) | ✅ Testado |
| **MCP Server** | FastAPI + Streamable HTTP | ✅ Funcionando |
| **Ferramentas MCP** | 13 tools para Alexa+ | ✅ Testado |
| **Autenticação** | 3 roles (família, médico, admin) | ✅ Testado |
| **WebSocket** | Multi-dispositivo em tempo real | ✅ Implementado |
| **Dashboard** | HTML/CSS/JS puro | ✅ Funcionando |
| **Testes** | 47 testes (unit + integration + adversarial) | ✅ Passando |

### O Que É Roadmap

| Feature | Status |
| :--- | :--- |
| Integração com Bee (wearable físico) | Roadmap |
| Integração com YouTube, Netflix, Spotify | Roadmap |
| Integração com WhatsApp, Email | Roadmap |
| Página de memórias (galeria) | Roadmap |
| Página de tasks/remédios com alarmes | Roadmap |
| Chat com histórico de conversas | Roadmap |
| Geração de apresentações de memórias | Roadmap |
| Rede neural terapêutica própria | Roadmap 1-2 anos |
| Fine-tuning clínico do LLM | Roadmap 3-6 meses |
| LGPD/GDPR/HIPAA compliance certificado | Roadmap |

---

## Privacidade e Ética

**Privacy by Design** não é slogan. É arquitetura.

| Camada | O Que Faz |
| :--- | :--- |
| **Captura** | VAD: só grava quando há voz. Câmera só em emergência. |
| **Processamento** | Local (edge). Metadados apenas para a nuvem. |
| **Armazenamento** | Criptografia end-to-end. Expiração automática. |
| **Acesso** | Autenticação forte. Log de tudo. Revogação. |
| **Transparência** | Dashboard mostra exatamente quando a câmera liga. |

**O vídeo nunca sai do dispositivo.** Exceto em emergência confirmada (confiança ≥ 0.9), criptografado.

### Sobre Câmera 24/7

- **Detecção local**: OpenCV + MediaPipe processam no dispositivo.
- **Nada é enviado à nuvem**: só metadados (tipo do evento, confiança, timestamp).
- **Vídeo bruto**: só em emergência, com consentimento, expira em 7 dias.
- **Transparência**: LED visível quando gravando (hardware, quando aplicável).

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

**47 testes passando**, incluindo:

- ✅ Detecção de queda multimodal
- ✅ Detecção de negação ("não estou sentindo dor" ≠ emergência)
- ✅ Intenção ≠ comportamento (fuga só com observação)
- ✅ Escalonamento proporcional (SAMU só com confiança ≥ 0.9)
- ✅ Correlação de sintomas (infecção urinária)
- ✅ Auditoria e detecção de viés
- ✅ 13 ferramentas MCP

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

### 1. Terapia de Validação como Fundamento

A maioria dos assistentes de IA para idosos **corrige a realidade**. Isso causa **crises, agressão e choro**.

O Libero é treinado em **Terapia de Validação (Naomi Feil)** e **Reminiscência**. Ele **nunca** diz:
- "Você não trabalha mais."
- "Sua mãe morreu."
- "Você está em casa."

Ele diz:
- "Você trabalhou por muitos anos. Me conta sobre isso."
- "Sua mãe deve ter sido incrível. Como ela era?"
- "Me fala da sua casa. Como ela é?"

### 2. Detecção Multimodal com Confiança Calibrada

Queda **não é** um som alto. Queda **é** áudio + visão + movimento, combinados.

O Libero só chama SAMU com **confiança ≥ 0.9**. Antes disso, ele **conversa** primeiro.

### 3. Escalonamento Proporcional

O Libero **nunca** chama a polícia por uma frase isolada. Ele **nunca** ativa câmera sem necessidade. Ele **nunca** notifica a família por ruído.

**Ele distingue**: intenção verbal ≠ comportamento observado.

### 4. Notificação Honesta

A maioria dos sistemas diz "notificado" mesmo quando falha.

O Libero usa **estados reais**: `queued`, `sent`, `delivered`, `failed`, `simulated`.

**A família sabe exatamente o que aconteceu.**

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
