# How to run the Libero Demo

This project is a **research prototype** for home-care support. It runs locally on Linux/macOS/Windows.

## Prerequisites
- Python 3.11+
- Node.js 18+
- (Optional) AWS credentials for Bedrock/Polly

## Step 1: Backend (MCP Server)
Open Terminal 1 and run:
```bash
cd ~/libero
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your GROQ_API_KEY
python cloud/mcp_server/server.py
```
The API will be available at `http://127.0.0.1:8080`.

## Step 2: Edge Device (Audio + Camera)
Open Terminal 2 and run:
```bash
cd ~/libero
source venv/bin/activate
LIBERO_CAMERA_CONSENT=true python edge/main.py
```
This starts the microphone listener and the camera stream at `http://127.0.0.1:8081/stream`.

## Step 3: React Frontend
Open Terminal 3 and run:
```bash
cd ~/libero/frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

## Step 4: Login
Use the development credentials:
- **Email**: `ana@libero.com`
- **Password**: `libero123`

## Step 5: Test the flow
1. Go to **Conversations** and type `I need to go home`.
2. Go to **Environment** and click **Open visualization** (requires Edge running).
3. Go to **Care Screen** to see the avatar.
4. Trigger an emergency overlay:
```bash
curl -X POST http://localhost:8080/teste/emergencia \
  -H "Content-Type: application/json" \
  -d '{"idoso_id":"dona-maria","evento":"queda","local":"quarto"}'
```

## Troubleshooting
- **Camera not opening**: Ensure no other app is using `/dev/video0`.
- **Microphone not working**: Ensure the Edge is running and the terminal is not muted.
- **Login fails**: Ensure the MCP Server (Terminal 1) is running.
