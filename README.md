# ConsultX — Retrieval-Augmented Guardrails for Safer AI Therapy

ConsultX prevents over-affirmation and unsafe responses by grounding the LLM in vetted CBT/MI content (RAG) and enforcing post-generation safety checks. No fine-tuning required — everything runs through prompts, retrieval, and guardrails.

---

## 1. Overview

This branch contains the **full ConsultX stack**:

- A **Python backend** for:
  - Conversation **session tracking** (with rolling buffers).
  - **Risk scoring** across tiers: `ok`, `caution`, `high`, `crisis`.
  - **End-of-session summaries** for analysis & research.
  - An optional **therapy RAG pipeline** (Gemini + curated CBT/MI snippets + guardrails).

- A **React + TypeScript + Vite frontend** for:
  - Chat-style UI on top of the backend API.
  - Live view of messages, risk tiers, and session context.

This repo is meant to be **research-friendly**: easy to run locally, inspect, and extend for analysis & safety experiments.

---

## 2. Key Features

- 🧠 **MI + CBT-style responses**: Prompting and retrieval are tuned toward psycho-educational, non-diagnostic, MI/CBT-flavored guidance.
- 🛟 **Guardrail-first design**:
  - Pre-message safety checks and risk tiers.
  - Retrieval from vetted resources only.
  - Post-generation filters to catch over-affirmation, unsafe suggestions, and policy violations.
- 📊 **Session tracking & summaries**:
  - Rolling buffer of recent turns.
  - Per-session risk metrics & sentiment trends.
  - Structured JSON summary ready for downstream analysis.
- 🧩 **Modular core**:
  - `backend/core/*` isolates RAG, LLM calls, guardrails, and risk types.
  - `backend/session_tracking.py` handles session lifecycle & metrics.
  - Easy to swap in different LLMs or retrieval backends.
- 🌐 **Simple HTTP API**:
  - Built on the Python standard library.
  - Stateless endpoints plus SQLite persistence layer.
- 💻 **Modern frontend**:
  - React + TypeScript + Vite dev server.
  - Ready to wire to any backend endpoint.

---

## 3. Architecture at a Glance

High-level pipeline for a **therapy turn**:

```text
User message
   │
   ▼
[Step 1] Safety Gate (risk + policy check)
   - Keyword-based risk detection (ok / caution / high / crisis)
   - Lightweight sentiment & intent heuristics
   │
   ▼
[Step 2] Curated Knowledge Retrieval
   - Retrieve CBT/MI snippets from vetted psycho-educational sources
   - Top-k context chunks for this turn
   │
   ▼
[Step 3] Contextual Response Generation
   - LLM (e.g., Gemini) + MI/CBT prompt template
   - Uses retrieved context + risk tier rules
   │
   ▼
[Step 4] Guardrail Enforcement Layer
   - Post-generation filters for unsafe / over-affirmative patterns
   - Crisis escalation messaging, disclaimers, and safe deflections
   │
   ▼
Persisted in SQLite + exposed to the frontend for analysis & UX

The session tracker runs alongside this pipeline, storing:
  - All messages + timestamps.
  - Risk scores and tier transitions.
  - Final session summary with trends & resource hints.

```

---

## 4. Project Structure

```text
TheConsultX/
├── backend/
│   ├── __init__.py
│   ├── analysis.py            # Sentiment + risk heuristics & resource mapping
│   ├── api.py                 # HTTP server exposing REST endpoints
│   ├── models.py              # Dataclasses, enums, and shared types
│   ├── session_tracking.py    # Session lifecycle + metrics + summaries
│   ├── storage.py             # SQLite repository for sessions/messages/metrics
│   ├── core_adapter.py        # Thin wrapper: session tracker → RAG/guardrails core
│   └── core/                  # RAG + LLM + guardrails pipeline
│       ├── orchestrator.py    # Orchestrates retrieval → LLM → guardrails
│       ├── retrieval.py       # Vector store + embeddings + top-k snippet lookup
│       ├── prompt.py          # MI/CBT system & turn templates
│       ├── guardrails.py      # Post-gen filters, safety rules, escalation logic
│       ├── risk_types.py      # Canonical risk tiers and helper types
│       ├── llm_gateway.py     # Wrapper over Gemini / LLM API(s)
│       ├── memory.py          # Long-lived memory abstraction (per user/episode)
│       ├── session_store.py   # Persistent store for core pipeline state
│       ├── schemas.py         # Pydantic-style schemas for RAG/therapy turn payloads
│       └── ingest_build_examples.py
│                              # Scripts to ingest CBT/MI resources into a vector store
│
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── eslint.config.js
│   ├── prettier.config.js
│   └── src/
│       ├── main.tsx           # React entrypoint
│       ├── App.tsx            # Top-level app shell
│       ├── components/        # Chat UI, risk badges, layout components, etc.
│       └── ...
│
├── docs/
│   └── session_backend_design.md   # Detailed design doc for session tracking backend
│
├── consultx.db                # SQLite database (created/used by backend)
├── responses.json             # Example RAG / guardrail responses for reference
└── README.md                  # You are here
```
---
## 5. Backend — Running the Session Tracker & RAG Core

### 5.1. Prerequisites

- **Python 3.11+**

- For the **basic session tracker (no RAG/LLM)**, the backend uses only:
  - Python standard library
  - SQLite

- The **RAG/LLM pipeline** (`backend/core/*`) additionally requires:
  - Gemini client
  - LangChain / transformers
  - Vector store implementation
  - Sentence embeddings
  - Any other libraries imported at the top of those files

---

### 5.2. Quickstart (Session Tracker Only)

From the repo root, run:

```bash
python -m backend.api
```
By default, the API listens on:
```text
http://127.0.0.1:8000
```
---
### 5.3. Configuration (Environment Variables)

#### Core backend

- **`CONSULTX_DB_PATH`**  
  Path to SQLite DB file.  
  _Default_: `consultx.db` in the repo root.

- **`CONSULTX_BUFFER_SIZE`**  
  Rolling buffer size per session.  
  _Default_: `20` messages.

- **`CONSULTX_API_KEYS`**  
  Comma-separated list of API keys.  
  If set, every request must authenticate with one of these keys.

- **`CONSULTX_API_KEYS_FILE`**  
  Optional file path; one API key per line.  
  Merged with `CONSULTX_API_KEYS`.

---

#### RAG / LLM pipeline (optional)

- **`CONSULTX_ENABLE_RAG`** (`0` / `1`)  
  When `1`, `POST /sessions/{id}/messages` can invoke the RAG pipeline via flags.

- **`CONSULTX_RAG_AUTOREPLY`** (`0` / `1`)  
  When `1`, the generated assistant reply is auto-appended to the session.

- **`GOOGLE_API_KEY`**  
  API key for the Gemini model (used in `backend/core/llm_gateway.py`).

- **`CONSULTX_RAG_MODEL`**  
  Model name to use in the LLM gateway.  
  _Default_: `gemini-2.0-flash`.

- **`CONSULTX_RAG_K`**  
  Top-`k` retrieved context chunks per turn.  
  _Default_: `2`.

- **`CONSULTX_RAG_COUNTRY`**  
  Country / region code used for region-aware disclaimers/resources.  
  _Default_: `US`.

- **`CONSULTX_RAG_GUARDRAILS`** (`0` / `1`)  
  Toggle the post-generation guardrail enforcement layer.

---

If the RAG stack fails (missing libraries, no vector store, etc.), the backend returns a graceful error note in the `rag` block **without breaking the session tracker**.

---
## 6. Frontend — React + Vite App

From the repo root:

```bash
cd frontend

# Install dependencies
npm install

# Run dev server (default Vite port: 3000)
npm run dev
```

You should see something like:

```text
VITE vX.X.X  ready in XXXX ms
  ➜  Local:   http://localhost:3000/
```

Configure the frontend to point at your backend API (`http://127.0.0.1:8000` by default).  
Once wired, you can:

- Start a new session from the UI.
- Send user messages.
- View assistant responses, risk tiers, and summaries.


---
## 7. REST API Summary

All endpoints are served from backend/api.py.

| Method | Path                      | Description                                                             |
| ------ | ------------------------- | ----------------------------------------------------------------------- |
| POST   | `/sessions`               | Create a new session. Body: `{"user_id": "...", "metadata": {...}}`.    |
| GET    | `/sessions`               | List sessions (optional filters: `user_id`, `status`).                  |
| GET    | `/sessions/{id}`          | Get metadata, latest buffer snapshot, and cached metrics for a session. |
| POST   | `/sessions/{id}/messages` | Append a message to a session. Supports optional RAG flags.             |
| POST   | `/sessions/{id}/end`      | Mark session as ended and compute/store final summary.                  |
| GET    | `/sessions/{id}/summary`  | Retrieve or recompute the session summary JSON.                         |

---
## 7.1. Message Payload (with Optional RAG)

Basic message:

```json
{
  "sender": "user",
  "content": "I feel exhausted and unmotivated lately."
}
```
Advanced, invoking RAG:
```json
{
  "sender": "user",
  "content": "I feel exhausted and unmotivated lately.",
  "use_rag": true,
  "auto_reply": true
}
```

Response includes:

assistant_message (if RAG produced a reply and auto_reply was set).
rag block with:
Retrieved snippets.
Raw LLM output.
Guardrail decisions/notes.
Updated risk metrics and buffer snapshot for the session.


---
## 7.2. Sample Workflow (Curl)
```bash
# 1. Create a session
curl -X POST http://127.0.0.1:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"user_id": "demo-user"}'

# 2. Append a user message
curl -X POST http://127.0.0.1:8000/sessions/{session_id}/messages \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "user",
    "content": "I feel hopeless and tired.",
    "use_rag": true,
    "auto_reply": true
  }'

# 3. End the session and fetch summary
curl -X POST http://127.0.0.1:8000/sessions/{session_id}/end

curl http://127.0.0.1:8000/sessions/{session_id}/summary
```

---
## 8. Extensibility

A few ways to extend ConsultX for analysis & research:

- 🔍 **Custom risk models**  
  Plug your own classifier (transformer, API, etc.) into the risk pipeline and map outputs into the `ok` / `caution` / `high` / `crisis` tiers.

- 📚 **New knowledge bases**  
  Use `backend/core/ingest_build_examples.py` as a starting point to ingest different CBT/MI resources, psycho-educational guides, or synthetic examples.

- 🤖 **Swap LLMs**  
  Implement another client in `backend/core/llm_gateway.py` (e.g., OpenAI, local models) and keep the same orchestrator interface.

- 🌎 **Locale-specific resources**  
  Extend risk → resource mapping (e.g., hotlines, support services) by country or region.

- 🧪 **A/B experimentation**  
  Run experiments comparing:
  - Plain LLM vs RAG vs RAG + Guardrails  
  - Different prompt styles or retrieval strategies  
  - Different risk-escalation policies

---
## 9. Safety & Disclaimer

ConsultX is a research and prototyping tool, not a clinical product.

- It does **not** provide medical advice.  
- It is **not** a replacement for professional mental health care.

Any deployment in real-world settings must include:

- Human oversight  
- Clinically validated risk escalation procedures  
- Proper legal, ethical, and privacy review  

---
## 10. License / Attribution

This project is open source under the MIT License.

If you use ConsultX in research, demos, or reports, please credit:

> ConsultX — Retrieval-Augmented Guardrails for Safer AI Therapy (AMS 691.01 Group 4: Omkar Lashkare, Jiyang Wu, Yemoe Aung, Zikai Cheng, and Sarah Aguiar, 2025)

See the `LICENSE` file for full details.



