# ConsultX Session Tracking Backend

This repository delivers the first milestone for ConsultX: a self-contained backend that tracks conversation sessions, evaluates risk, and prepares end-of-session summaries in line with the project proposal.

## Features
- REST API built with the Python standard library (no external installs required).
- Session lifecycle management with rolling buffer snapshots.
- Lexicon-driven sentiment and risk classification (tiers: `ok`, `caution`, `high`, `crisis`).
- SQLite persistence for sessions, messages, metrics, and buffers.
- Automatic summary generation with sentiment trends, tier counts, and resource suggestions.
- Optional RAG therapy pipeline (Gemini + retrieval + guardrails) wired via `backend/core_adapter.py`, enabled with environment flags.
- Optional API-key authentication on every endpoint.
- Adapter-friendly risk engine so external classifiers can augment heuristic scoring.
- Unit tests covering core workflows.

## Project Layout
```
backend/
  analysis.py          # Sentiment + risk heuristics
  api.py               # HTTP server exposing REST endpoints
  models.py            # Dataclasses and enums
  session_tracking.py  # Orchestration service
  storage.py           # SQLite repository
docs/
  session_backend_design.md
tests/
  test_session_tracking.py
ConsultX - Group 4 Proposal.pdf
README.md
```

## Getting Started
1. Ensure Python 3.11+ is available.
2. (Optional) Set environment overrides:
   - `CONSULTX_DB_PATH`: SQLite file path (defaults to `consultx.db`).
   - `CONSULTX_BUFFER_SIZE`: Rolling buffer size (defaults to `20` messages).
   - `CONSULTX_API_KEYS`: Comma-separated API keys required for every request.
   - `CONSULTX_API_KEYS_FILE`: File containing one API key per line (merged with inline keys).
3. Launch the server:
   ```bash
   python -m backend.api
   ```
   The server listens on `http://127.0.0.1:8000`.

### RAG Integration (optional)
- Set `CONSULTX_ENABLE_RAG=1` to route user messages through the RAG pipeline (`backend/core_adapter.py` and `backend/core/*`).  
- Set `CONSULTX_RAG_AUTOREPLY=1` if you want the generated assistant reply auto-appended to the session.  
- Required runtime inputs: `GOOGLE_API_KEY` plus the vector store built for retrieval (see `backend/core/retrieval.py` defaults).  
- Optional knobs: `CONSULTX_RAG_MODEL` (default `gemini-2.0-flash`), `CONSULTX_RAG_K` (default `2`), `CONSULTX_RAG_COUNTRY` (default `US`), `CONSULTX_RAG_GUARDRAILS` (`1`/`0`).  
- If dependencies (Gemini client, langchain/transformers, or the vector DB) are missing, the call is skipped and an error note is returned in the `rag` block without breaking the session tracker.

### Authentication
If either `CONSULTX_API_KEYS` or `CONSULTX_API_KEYS_FILE` is supplied, the API enforces authentication. Clients must send one of:
- `Authorization: Bearer <api-key>`
- `X-API-Key: <api-key>`

Requests without a valid key receive `401 Unauthorized`.

## REST API
| Method | Path | Description |
| ------ | ---- | ----------- |
| `POST` | `/sessions` | Create a session. Body: `{"user_id": "...", "metadata": {...}}`. |
| `GET`  | `/sessions` | List sessions. Query params: `user_id`, `status`. |
| `GET`  | `/sessions/{id}` | Fetch metadata, latest buffer snapshot, and cached metrics. |
| `POST` | `/sessions/{id}/messages` | Append a message (`sender`: `user`/`assistant`/`system`, `content`). Optional flags: `use_rag` (bool) to invoke the RAG pipeline, `auto_reply` (bool) to auto-append the generated assistant turn when RAG is used. Responses include an optional `assistant_message` and `rag` block when present. |
| `POST` | `/sessions/{id}/end` | Mark session as ended and generate final summary. |
| `GET`  | `/sessions/{id}/summary` | Retrieve (or recompute) the session summary. |

Responses are JSON with ISO8601 timestamps. Errors follow `{"error": "...", "status": <code>}`.

### Sample Workflow
```bash
# Create a session
curl -X POST http://127.0.0.1:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"user_id": "demo-user"}'

# Append a user message
curl -X POST http://127.0.0.1:8000/sessions/{session_id}/messages \
  -H "Content-Type: application/json" \
  -d '{"sender": "user", "content": "I feel hopeless and tired."}'

# End the session and fetch summary
curl -X POST http://127.0.0.1:8000/sessions/{session_id}/end
```

## Testing
Run the unit test suite:
```bash
python -m unittest discover -s tests
```

## Extensibility
- Register advanced risk detectors at runtime: `tracker.register_risk_adapter(callable)` where the callable returns a `RiskAssessment`. Adapters can escalate tiers, contribute notes, and flag custom keywords.
- Expand the resource catalog by updating `backend/analysis.py` to map new keywords to referrals or exercises.

## Next Steps
1. **Identity Provider Integration**: Swap API-key auth for OAuth/JWT backed by the real user directory.
2. **Advanced Risk Models**: Plug clinical risk classifiers (e.g., hosted transformers) into the adapter pipeline.
3. **Locale-Aware Resources**: Expand referrals with multi-region contact data and dynamic selection.
4. **Frontend Integration**: Wire the web UI to consume buffer snapshots and summaries in real time.
5. **Telemetry & Logging**: Export structured logs to monitoring/alerting pipelines for operational visibility.
