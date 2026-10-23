# Libero

> Porque ninguém deveria se perder. Nem quem cuida.

Libero is a research prototype for home-care support focused on context, memory, and early safety awareness for people living with dementia and the caregivers around them.

This repository combines a local edge layer, conversational assistants, MCP-based tool orchestration, and a web dashboard used to simulate a real care-support workflow in a home environment. The goal is to explore how technology can preserve human context, reduce cognitive load, and help families respond more thoughtfully without replacing human care.

## What Libero is

Libero is not a clinical device and not a monitored emergency system. It is a prototype built to explore a practical question:

How can AI and home-care tools support both the person living with dementia and the person caring for them?

The current implementation demonstrates:

- conversational support via a web interface and MCP tool flow
- memory capture for meaningful personal stories
- local and experimental safety analysis
- caregiver-facing dashboards and context review

## What Libero is not

Libero does not currently provide:

- certified medical monitoring
- automatic emergency dispatch
- guaranteed 24/7 detection
- clinical validation or compliance certification

The project is designed as a research prototype and a human-centered design exploration.

---

## The problem

When somebody living with dementia says, "I need to go home," a reminder alone cannot address the feeling behind the sentence. Families may lose context, routines can become disorienting, and the risk of wandering or confusion can rise quickly.

At the same time, caregivers are often managing the emotional load of care while trying to maintain their own lives and responsibilities.

**Libero explores how technical support can reduce this pressure without replacing presence, trust, or judgment.**

---

## Short pitch

When someone living with dementia says, "I need to go home," a reminder cannot address the feeling behind that moment. Libero connects a supportive response to the context of the person and the family around them, helping preserve meaningful memories while surfacing situations that may deserve attention.

It is a research prototype for home-care support built to explore how AI can reduce caregiver burden, support safer routines, and keep human context close when memory fades.

Because no one should get lost. Not even the caregiver.

---

## Demonstration and status

The project already demonstrates a functioning local demo stack with:

- a dashboard web app
- an MCP-connected conversation flow
- memory capture and review
- edge status checks for microphone and camera assumptions
- experimental safety-event logic designed for research use

For production-grade deployment, the next steps are network hardening, consent workflows, security review, better persistence, and clinical/UX validation.

---

## How to run the demo

### Prerequisites

- Python 3.11+
- Node.js 18+
- Microphone (required) and camera (optional, consent-based)
- Groq API key (free tier works)
- AWS account (optional, for Bedrock + Polly)

### 1. Backend (MCP Server)

```bash
cd ~/libero
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add GROQ_API_KEY
python cloud/mcp_server/server.py
```

### 2. Edge (audio + camera)

```bash
cd ~/libero
source venv/bin/activate
LIBERO_CAMERA_CONSENT=true python edge/main.py
```

### 3. Frontend (React + Vite)

```bash
cd ~/libero/interface
npm install
npm run dev
```

Open `http://localhost:3000` and log in with:

- **Email**: `ana@libero.com`
- **Password**: `libero123`

### 4. Trigger a test emergency (optional)

```bash
curl -X POST http://localhost:8080/teste/emergencia \
  -H "Content-Type: application/json" \
  -d '{"idoso_id":"dona-maria","evento":"queda","local":"quarto"}'
```

---

## Tech stack

| Layer | Technology |
| :--- | :--- |
| **Edge** | Python, OpenCV, Groq Whisper |
| **Cloud** | FastAPI, AWS Bedrock (Claude), AWS Polly |
| **MCP Server** | Streamable HTTP (spec 2025-11-25) |
| **Frontend** | React, Vite, Framer Motion, @google/model-viewer |
| **Auth** | Cookie HttpOnly, 3 roles (family, doctor, admin) |
| **Tests** | Pytest (106 tests) |

---

## Documentation

- [docs/PITCH_LIBERO.md](docs/PITCH_LIBERO.md) — pitch material and positioning
- [docs/ROTEIRO_DEMO_VIDEO.md](docs/ROTEIRO_DEMO_VIDEO.md) — demo script and checklist
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — architecture overview
- [docs/GOVERNANCE.md](docs/GOVERNANCE.md) — safety and governance notes
- [docs/PRIVACY.md](docs/PRIVACY.md) — privacy and deployment considerations

---

## License

MIT. See [LICENSE](LICENSE).

Build by Natalia.exe
