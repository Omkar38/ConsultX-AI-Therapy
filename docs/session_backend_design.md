# ConsultX Session Tracking & Backend Design

## Overview
The ConsultX backend exposes the core services required to capture AI–user conversations, monitor ongoing risk levels, and generate end-of-session summaries. This module is responsible for:
- Maintaining authenticated sessions and a rolling conversation buffer.
- Persisting all exchanges and risk metrics for auditability.
- Performing lightweight sentiment and risk analysis per message.
- Aggregating trends to surface caution, high-risk, or crisis states.
- Producing structured session summaries that downstream components (UI, RAG guardrails, escalation flows) can consume.

The initial scope intentionally focuses on session tracking and safety telemetry; chatbot orchestration, authentication, and retrieval guardrails will integrate with these services later.

## Functional Requirements
- Create and manage conversation sessions for authenticated users.
- Append user or assistant messages, tagging each with sentiment, detected risk tier, and extracted crisis keywords.
- Maintain a rolling buffer of the most recent N turns for fast context retrieval.
- Surface current session state (status, latest risk tier, trend notes).
- Generate an end-of-session summary with per-tier message counts, top sentiments, flagged phrases, suggested resources, and escalation notes.
- Persist all state in durable storage (SQLite) with transactional integrity.
- Expose REST endpoints so the web front-end and AI middleware can drive the workflow.

## Non-Functional Requirements
- Local-first development using the Python standard library only (no external installs).
- Storage back-end must be lightweight, embeddable, and support concurrent read access.
- Clear separation between analysis, persistence, and transport layers for future replacement or scaling.
- Deterministic risk scoring built from lexicon-based heuristics, ready to be swapped for ML classifiers once available.
- Endpoints optionally protected by API-key authentication for rapid environment hardening.

## High-Level Architecture
```
┌────────────────┐     ┌────────────────┐     ┌─────────────────────┐
│ REST Controller │───▶│ Session Service │───▶│ Persistence (SQLite) │
└────────────────┘     ├────────────────┤     └─────────────────────┘
         ▲             │  Risk Engine   │
         │             │  Buffer Cache  │
         │             └────────────────┘
         │
         ▼
 ┌────────────────┐
 │ Front-end / AI │
 └────────────────┘
```

- **REST Controller (`backend/api.py`)**: Minimal HTTP handler that translates JSON requests into service calls, enforces API-key authentication, and serialises responses.
- **Session Service (`backend/session_tracking.py`)**: Core orchestration layer coordinating storage, rolling buffers, and the analysis module.
- **Risk Engine (`backend/analysis.py`)**: Provides sentiment and risk scoring using lexicon heuristics and keyword detection.
- **Persistence (`backend/storage.py`)**: SQLite-backed repository implementing CRUD for sessions, messages, metrics, and buffer snapshots.
- **Shared Models (`backend/models.py`)**: Dataclasses and enums describing session entities and API payloads.

## Data Model
### Sessions (`sessions` table)
- `id` (TEXT, primary key, UUIDv4)
- `user_id` (TEXT)
- `status` (TEXT, enum: `active`, `ended`)
- `created_at` / `updated_at` (TEXT, ISO-8601 UTC)
- `active_risk_tier` (TEXT, enum: `ok`, `caution`, `high`, `crisis`)
- `metadata` (TEXT, JSON blob for locale, channel, device)

### Messages (`messages` table)
- `id` (INTEGER primary key AUTOINCREMENT)
- `session_id` (TEXT, FK)
- `sender` (TEXT, enum: `user`, `assistant`, `system`)
- `content` (TEXT)
- `sentiment_score` (REAL, range -1.0…1.0)
- `risk_tier` (TEXT)
- `risk_score` (REAL 0…1)
- `flagged_keywords` (TEXT, JSON array)
- `created_at` (TEXT)

### Session Metrics (`session_metrics` table)
- `session_id` (TEXT, FK, unique)
- `message_count` (INTEGER)
- `user_turns` / `assistant_turns` (INTEGER)
- `avg_sentiment` (REAL)
- `max_risk_tier` (TEXT)
- `trend_notes` (TEXT)
- `suggested_resources` (TEXT, JSON array)

### Rolling Buffer (`buffers` table)
- `session_id` (TEXT, FK, unique)
- `serialized_buffer` (TEXT, JSON array of last N messages)

## Rolling Buffer Strategy
- Buffer capacity defaults to 10 exchanges (20 messages).
- The buffer mirrors the latest messages with content, sender, risk tier, and timestamp.
- The service updates the buffer after each message insert, ensuring low-latency retrieval for prompt construction or UI display.

## Risk & Sentiment Heuristics
- **Sentiment**: Simple lexicon-based scoring using curated positive and negative word banks and negation handling. Scores map to `positive`, `neutral`, `negative` bands.
- **Risk Tier**:
  - `crisis`: self-harm verbs + intent phrases (e.g., “kill myself”, “suicide”).
  - `high`: explicit plans, severe self-hate, or repeated crisis keywords within rolling window.
  - `caution`: concerning affect (e.g., “numb”, “worthless”) or rapid negative sentiment drift.
  - `ok`: baseline safe content.
- **Trend Detection**: Rolling average sentiment and last-5 risk tiers to add notes such as “deteriorating mood” or “recovering”.
- **Resource Suggestions**: Keyword-to-resource mapping (e.g., crisis hotline, mindfulness exercise). Stored with suggestions to feed summary and UI.

## Authentication
- API keys can be supplied via `CONSULTX_API_KEYS` (comma-separated) or `CONSULTX_API_KEYS_FILE` (one key per line).
- When configured, requests must provide either `Authorization: Bearer <key>` or `X-API-Key: <key>`.
- Unauthorized requests receive a 401 and `WWW-Authenticate` header, enabling clients to respond appropriately.

## Risk Adapters & External Providers
- The `RiskClassifier` maintains a register of adapters (callables returning `RiskAssessment`).
- Adapters can augment heuristics by contributing flagged phrases, raising tiers, or appending notes.
- `SessionTracker.register_risk_adapter` exposes the registration hook, so downstream code can plug in hosted classifiers, rule engines, or human-in-the-loop review workflows without modifying core logic.
- Adapter failures are captured and surfaced as diagnostic notes to avoid silent degradations.

## API Surface (Initial)
| Method | Path | Description |
| ------ | ---- | ----------- |
| `POST` | `/sessions` | Create a session for a user. |
| `GET`  | `/sessions` | List sessions (filters by status/user optional). |
| `GET`  | `/sessions/{id}` | Retrieve session metadata and current buffer. |
| `POST` | `/sessions/{id}/messages` | Append a message; returns updated risk tier and buffer snapshot. |
| `POST` | `/sessions/{id}/end` | Mark session complete and trigger summary generation. |
| `GET`  | `/sessions/{id}/summary` | Retrieve generated summary. |

All endpoints accept/return JSON. Error responses include an `error` string and optional `details`.

## Session Summary Structure
```json  
{
  "session_id": "uuid",
  "user_id": "user-123",
  "duration_seconds": 1260,
  "message_count": 28,
  "sentiment": {
    "average": -0.32,
    "trend": "declining",
    "bands": {"positive": 3, "neutral": 8, "negative": 17}
  },
  "risk": {
    "highest_tier": "high",
    "tier_counts": {"ok": 12, "caution": 10, "high": 6, "crisis": 0},
    "flagged_keywords": ["hopeless", "sleep forever"]
  },
  "suggested_resources": [
    {"type": "hotline", "label": "988 Suicide & Crisis Lifeline", "link": "tel:988"},
    {"type": "grounding", "label": "5-4-3-2-1 grounding exercise"}
  ],
  "notes": [
    "Multiple consecutive negative turns detected.",
    "Escalation recommended if crisis terms reappear."
  ]
}
```

## Error Handling
- Invalid JSON or missing fields → HTTP 400 with descriptive message.
- Unknown session → HTTP 404.
- Attempts to add messages to an ended session → HTTP 409.
- Internal exceptions translated to HTTP 500 with correlation ID (logged server-side).

## Logging & Observability
- Structured log entries per request (method, path, status code, latency).
- Risk escalations are logged at WARNING with session id and detected keywords.
- Session summaries stored in database and returned on demand for analytics.

## Extensibility Notes
- Storage layer can be swapped for PostgreSQL by replacing the repository implementation.
- Risk engine exposes a clean interface so that future ML models or external APIs can replace lexicon logic.
- Additional authentication strategies (OAuth, JWT) can layer over the existing controller by extending the `APIKeyAuthenticator`.
- Rolling buffer capacity adjustable via environment variable (`CONSULTX_BUFFER_SIZE`).
- API server intentionally framework-free, but the service orchestrator is independent, enabling migration to FastAPI/Express later without data rewrites.
