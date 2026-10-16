# Libero

> Porque ninguém deveria se perder. Nem quem cuida.

---

## O Problema

Em 2024, um senhor de 62 anos com Alzheimer levou a garrafa de café e saiu para trabalhar. Como fazia há 40 anos. Ele andou. Se machucou. Caiu. Vinte e nove dias depois, a família encontrou o corpo no mato.

O filho tinha saído por 20 minutos. Duas quadras.

**Isso não é um caso isolado.**

- **55 milhões** de pessoas vivem com demência no mundo. Serão **152 milhões** em 2050.
- **60%** vão perambular em algum momento.
- **50%** dos que perambulam se machucam. **10%** morrem.
- **66%** dos cuidadores têm sintomas de depressão.
- **40%** dos cuidadores morrem antes do paciente.

**Ninguém cuida de quem cuida.**

---

## A Solução

**Libero** é um protótipo de sistema de cuidado 24 horas para idosos com Alzheimer ou demência que vivem em casa.

Ele usa **câmera e áudio contínuos** para perceber quedas, tentativas de saída, confusão e crises — e **propõe** ações: conversar, acalmar, orientar ou sugerir ajuda externa.

Cada resposta é baseada em **Terapia de Validação** e **Reminiscência**: nunca corrige a realidade do idoso, sempre acolhe a emoção por trás dela.

A família recebe **notificações em tempo real** (via WebSocket) e **histórias gravadas automaticamente**.

**É um protótipo.** A validação clínica e a certificação são roadmap.

---

## O Que Está Implementado

### Funcionalidades Reais

| Feature | Status | Como testar |
| :--- | :--- | :--- |
| Áudio contínuo com transcrição | Real | `python edge/capture/listener.py` |
| Transcrição via Groq Whisper | Real | Falar no microfone |
| LLM (Groq / AWS Bedrock) | Real | `python cloud/agents/companion.py` |
| Voz via AWS Polly | Real | `python edge/output/speaker.py` |
| Detecção multimodal de queda (áudio + visão) | Real | `python cloud/agents/safety.py` |
| Detecção de negação ("não estou sentindo dor") | Real | `pytest tests/unit/test_adversarial.py` |
| Decisão em 4 níveis | Real | `python edge/decision/levels.py` |
| Câmera MJPEG ao vivo no dashboard | Real | `http://localhost:8081/stream` |
| Chat em tempo real com bolhas | Real | Dashboard → Conversas |
| Notificação em tempo real (WebSocket + overlay) | Real | `curl -X POST .../teste/emergencia` |
| Autenticação com 3 roles (família, médico, admin) | Real | `ana@libero.com` / `libero123` |
| 13 ferramentas MCP (Streamable HTTP) | Real | `GET /mcp/tools` |
| 102 testes automatizados | Real | `pytest tests/ -v` |

### Funcionalidades de Protótipo (com limitações)

| Feature | Limitação |
| :--- | :--- |
| Chamada a SAMU/polícia | **Não executa.** Apenas registra como `proposta_nao_executada`. Execução real é roadmap. |
| Notificação por SNS | Só funciona se `SNS_TOPIC_ARN` estiver configurado. Sem ele, modo simulado. |
| Persistência em DynamoDB | Código existe, mas o protótipo usa JSON local. DynamoDB é roadmap. |
| Bedrock (Claude) | Requer credenciais AWS configuradas. Fallback offline funciona sem AWS. |
| Groq Whisper | Requer `GROQ_API_KEY`. Fallback para Whisper local é limitado. |

### O Que É Roadmap

- Integração com **Bee** (wearable físico)
- **Voice fingerprint** (distinguir idoso, cuidador, visitante)
- **Rede neural terapêutica própria** (fine-tuning clínico)
- **Certificação LGPD/HIPAA** (o protótipo atual **não é** compliant)
- **Integração com planos de saúde**
- **Multi-casa** (um cuidador monitora múltiplos idosos)
- **Deploy em produção** (AWS Lambda, CDK, TLS terminado em proxy)
- **Integração com YouTube, Netflix, Spotify**
- **Geração de apresentações de memórias**
- **Validação clínica com terapeutas**

---

## Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                       LIBERO                                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ÁUDIO (contínuo)         CÂMERA (contínuo)                  │
│  edge/main.py             edge/main.py                       │
│  └─ Groq Whisper          └─ OpenCV / MediaPipe              │
│      │                       │                               │
│      └───────────┬───────────┘                               │
│                  ▼                                            │
│  ┌──────────────────────────────────────┐                   │
│  │       CÉREBRO (Cloud)                 │                   │
│  │  cloud/agents/orchestrator.py         │                   │
│  │  ├─ companion (validação)             │                   │
│  │  ├─ safety (queda, fuga, grito)       │                   │
│  │  ├─ memory (reminiscência)            │                   │
│  │  ├─ care (remédios, água)             │                   │
│  │  ├─ family (notificação)              │                   │
│  │  ├─ health (correlação)               │                   │
│  │  └─ governance (auditoria)            │                   │
│  └──────────────────┬───────────────────┘                   │
│                     │                                        │
│      ┌──────────────┼──────────────┐                        │
│      ▼              ▼              ▼                        │
│  ┌────────┐    ┌────────┐    ┌────────┐                    │
│  │ MCP    │    │WebSocket│   │Polly   │                    │
│  │Server  │    │(real-time)│  │(voz)   │                    │
│  └────────┘    └────────┘    └────────┘                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Componentes Principais

| Camada | Arquivo | Função |
| :--- | :--- | :--- |
| **Edge** | `edge/main.py` | Orquestra áudio, câmera, voz |
| **Listener** | `edge/capture/listener.py` | Áudio contínuo com VAD + Groq Whisper |
| **Câmera** | `edge/capture/stream.py` | OpenCV + detecção de queda |
| **Câmera HTTP** | `edge/camera_server.py` | Serve MJPEG em :8081 |
| **Voz** | `edge/output/speaker.py` | AWS Polly / espeak |
| **Decisão** | `edge/decision/levels.py` | 4 níveis com detecção de negação |
| **Orquestrador** | `cloud/agents/orchestrator.py` | Coordena 8 agentes |
| **Segurança** | `cloud/agents/safety.py` | Queda, fuga, grito |
| **Companhia** | `cloud/agents/companion.py` | Terapia de validação |
| **Memória** | `cloud/agents/memory.py` | Grava histórias |
| **Saúde** | `cloud/agents/health.py` | Correlaciona sintomas |
| **Governança** | `cloud/agents/governance.py` | Auditoria + viés |
| **MCP Server** | `cloud/mcp_server/server.py` | 13 ferramentas HTTP |
| **Dashboard** | `interface/web/libero.js` | Frontend HTML/CSS/JS puro |

---

## Requisitos

- **Python 3.11+** (testado em 3.11 e 3.14)
- **Linux, macOS ou Windows**
- **Microfone** (obrigatório)
- **Câmera** (opcional, mas recomendada)
- **Conta Groq** (free tier suficiente)
- **Conta AWS** (opcional, para Bedrock + Polly)

---

## Instalação

```bash
# 1. Clonar
git clone https://github.com/nataliaexe/Libero.git
cd Libero

# 2. Virtualenv
python3 -m venv venv
source venv/bin/activate  # Linux/macOS

# 3. Dependências Python
pip install -r requirements.txt

# 4. Dependências de sistema (Linux)
sudo apt install -y ffmpeg portaudio19-dev espeak-ng v4l-utils
```

### Configurar `.env`

```bash
cp .env.example .env
nano .env
```

**Mínimo** (modo development):
```bash
LIBERO_ENV=development
GROQ_API_KEY=gsk_sua_chave_aqui
GROQ_LLM_MODEL=openai/gpt-oss-120b
AWS_REGION=us-east-2
```

**Completo** (com AWS):
```bash
LIBERO_ENV=development
GROQ_API_KEY=gsk_...
GROQ_LLM_MODEL=openai/gpt-oss-120b
AWS_REGION=us-east-2
BEDROCK_MODEL_ID=arn:aws:bedrock:us-east-2:...:inference-profile/us.anthropic.claude-haiku-4-5-20251001-v1:0
POLLY_VOICE=Camila
```

---

## Como Rodar

### 3 Terminais

**Terminal 1 — MCP Server**:
```bash
cd ~/libero
source venv/bin/activate
python cloud/mcp_server/server.py
```

**Terminal 2 — Edge (áudio + câmera + voz)**:
```bash
cd ~/libero
source venv/bin/activate
LIBERO_CAMERA_CONSENT=true python edge/main.py
```

**Terminal 3 — Dashboard**:
```bash
cd ~/libero
source venv/bin/activate
python -m http.server 3000 --directory interface/web
```

### Acessar

- **Dashboard**: http://localhost:3000/dashboard.html
- **Câmera (edge)**: http://localhost:8081/stream
- **MCP API**: http://localhost:8080/mcp/tools

### Contas de Teste (modo development)

| Email | Senha | Role |
| :--- | :--- | :--- |
| ana@libero.com | libero123 | família |
| medico@libero.com | medico123 | médico |
| admin@libero.com | admin123 | admin |

**Importante**: estas contas **só existem em modo development**. Em produção (`LIBERO_ENV=production`), o servidor exige `LIBERO_USERS_JSON` com senhas fortes.

---

## Testes

```bash
pytest tests/ -v
```

**102 testes passando**, cobrindo:

- Detecção multimodal de queda
- Detecção de negação ("não estou sentindo dor" ≠ emergência)
- Intenção ≠ comportamento (fuga)
- Escalonamento proporcional (SAMU só com confiança ≥ 0.9)
- Correlação de sintomas (infecção urinária)
- Auditoria e detecção de viés
- 13 ferramentas MCP
- Autenticação e isolamento entre idosos
- WebSocket com escopo por idoso
- Câmera com fallback e placeholder
- Merge de blocos de voz
- Listener com filtros anti-falso-positivo

---

## Segurança e Privacidade — O Que É Real

### O Que Está Implementado

| Aspecto | Status |
| :--- | :--- |
| Senhas com scrypt | Real |
| Sessões em cookie HttpOnly + Secure | Real |
| Rate limit de login | Real |
| CORS restrito em produção | Real |
| Isolamento por idoso (authz) | Real |
| Ticket one-time para câmera | Real |
| Logs sem conteúdo sensível | Real |
| Ações externas marcadas como `proposta_nao_executada` | Real |

### O Que NÃO Está Implementado

| Aspecto | Status |
| :--- | :--- |
| Criptografia end-to-end | Roadmap |
| Certificação LGPD | Roadmap |
| Certificação HIPAA | Roadmap |
| Criptografia em repouso (dados locais) | Roadmap |
| Auditoria persistente (não em memória) | Roadmap |
| Rotação de chaves | Roadmap |

**Nota**: este projeto **não é** um sistema de emergência médica certificado. É um **protótipo de pesquisa** que visa conformidade futura.

---

## Limitações Conhecidas

### Do Protótipo Atual

- **Detecção de emergência é heurística**. Os thresholds são calibrados manualmente. Não há validação clínica.
- **Chamadas a SAMU/polícia não são executadas**. Apenas registradas.
- **Persistência em memória ou JSON local**. Multi-instância não é suportado.
- **Câmera requer consentimento explícito** (`LIBERO_CAMERA_CONSENT=true`).
- **Câmera e edge não podem rodar em processos distintos** no mesmo `/dev/videoN`.
- **Microfone** depende do ambiente (ruído, latência do PipeWire no Linux).
- **Groq Whisper** tem latência (~1-2s). Não é transcrição local.
- **Bedrock** requer credenciais AWS. Sem elas, fallback offline é usado.

### Do Escopo

- **Não substitui médico**. É apoio domiciliar.
- **Não substitui cuidador humano**. É complemento.
- **Não é dispositivo médico**. Não há validação pela ANVISA.

---

## Documentação Adicional

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — Arquitetura detalhada
- [`docs/GOVERNANCE.md`](docs/GOVERNANCE.md) — Governança e auditoria
- [`docs/PRIVACY.md`](docs/PRIVACY.md) — Privacidade e dados
- [`docs/FRICTION_LOG.md`](docs/FRICTION_LOG.md) — Registro de problemas e soluções
- [`docs/SECURITY_DEPLOYMENT.md`](docs/SECURITY_DEPLOYMENT.md) — Configuração para produção

---

## Roadmap Técnico

### Curto Prazo (1-3 meses)

- CI/CD (GitHub Actions) com pytest + lint
- Adapter pattern para persistência (JSON em dev, DynamoDB em prod)
- Logging estruturado (substituir prints)
- Validação de env vars com Pydantic BaseSettings
- ThreadPoolExecutor no edge (limitar concorrência)
- Secrets Manager para credenciais em produção

### Médio Prazo (3-12 meses)

- Integração com Bee (wearable físico)
- Voice fingerprint
- Rede neural terapêutica própria (fine-tuning clínico)
- Certificação LGPD/HIPAA
- Estudos clínicos com universidades

### Longo Prazo (1-2 anos)

- Deploy em produção (AWS Lambda, CDK)
- Integração com planos de saúde
- Multi-casa
- Plataforma para desenvolvedores (SDK)

---

## Autoria

**Natália Borges Vargas**
Projeto submetido ao **Build, Ship, Shape: Amazon Developer Hackathon**.

---

## Licença

MIT. Veja [LICENSE](LICENSE).

---

## Frase Final

> *"O Libero não impede a doença. Ele impede que a doença vença."*

**LIBERO**
*Porque ninguém deveria se perder. Nem quem cuida.*
