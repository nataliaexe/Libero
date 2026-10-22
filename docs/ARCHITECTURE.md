# Libero architecture

Libero is a research prototype for home-care support. It has a local edge process, an HTTP API/MCP endpoint, and a browser dashboard. It is not a validated medical device or a guaranteed 24-hour monitoring service.

## Implemented flow

1. **Edge capture:** `edge/main.py` starts a microphone listener. Camera capture starts only when `LIBERO_CAMERA_CONSENT=true` is set before launch. The edge serves its local status and MJPEG stream on port 8081.
2. **Speech processing:** Voice activity and energy heuristics gate transcription. Groq Whisper is used when configured; local Whisper is the fallback when installed. A transcribed phrase is sent to the orchestrator.
3. **Orchestration:** `cloud/agents/orchestrator.py` applies heuristic safety rules, conversation responses, and memory detection. Responses may use Groq, Bedrock, or a limited offline fallback.
4. **MCP and API:** `cloud/mcp_server/server.py` exposes the JSON-RPC MCP endpoint at `/mcp` using Streamable HTTP JSON responses. The browser conversation uses `initialize`, `notifications/initialized`, `tools/list`, and `tools/call` against this endpoint. The server does not open SSE streams; GET `/mcp` returns `405 Method Not Allowed`.
5. **Family dashboard:** The web UI shows locally stored conversations, memories, tasks, and alerts. Its environment page reads sensor state from the edge process rather than assuming the API process shares in-memory listener state.

## Storage and optional integrations

- Chat and care tasks are stored in local JSON files in the user's data directory.
- Bedrock and Polly calls require AWS credentials and configuration. Bedrock use is optional and must be active to claim it in a demo.
- SNS, DynamoDB, Timestream, S3, multi-home operation, and production deployment are not part of the default local flow. Existing infrastructure code is not evidence of a deployed integration.
- The Fire TV folder contains an experimental interface, not a submission-ready application verified on Fire OS or Vega OS.

## Limits

- Fall and sound-event detection are experimental heuristics, not calibrated clinical probabilities.
- A camera frame or connected edge process does not establish round-the-clock availability.
- The prototype does not contact emergency services.
- The edge process reports its current sensor state and stores detected events locally. Automatic delivery of edge detections to the dashboard WebSocket or remote family notifications is not implemented; the visible WebSocket overlay is triggered by a demo endpoint.
- The edge stream is intended for a local demo. Production use requires a reviewed transport, TLS, authorization, and privacy design.
